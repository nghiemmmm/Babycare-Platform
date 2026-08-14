import os
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from dotenv import load_dotenv


# ============================================================
# GEMINI API FREE-TIER / MODEL TESTER
# ============================================================
# Mục đích:
#   1. Kiểm tra API Key
#   2. Lấy danh sách model có generateContent
#   3. Gọi generateContent trực tiếp bằng REST API
#   4. Xác định model:
#        🟢 CALLABLE
#        🔴 QUOTA = 0
#        🟠 RATE LIMIT 429
#        ⚠️ 404
#        ⛔ AUTH / PERMISSION
#
# Không sử dụng LangChain.
# ============================================================


# ============================================================
# 🔑 API KEY
# ============================================================
# Điền API key trực tiếp ở đây.
#
# Ví dụ:
# MANUAL_GEMINI_API_KEY = "AQ.xxxxxxxxxxxxxxxxx"
#
# Hoặc để "" và đặt:
#
# GEMINI_API_KEY=...
#
# trong file .env
# ============================================================

MANUAL_GEMINI_API_KEY = ""


# ============================================================
# ⚙️ CONFIG
# ============================================================

# True  = test toàn bộ model có generateContent
# False = chỉ test PRIORITY_MODELS
TEST_ALL_MODELS = True

# Nếu TEST_ALL_MODELS = False
PRIORITY_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
]

REQUEST_TIMEOUT = 20

# Delay giữa các request.
# Để tránh tự gây 429 khi test quá nhanh.
DELAY_BETWEEN_REQUESTS = 1.0


# ============================================================
# LOAD .ENV
# ============================================================

load_dotenv(override=True)


# ============================================================
# UTILS
# ============================================================

def mask_key(key: str) -> str:
    """
    Che API key khi in ra terminal.
    """

    if not key:
        return "***"

    if len(key) <= 12:
        return "***"

    return f"{key[:8]}...{key[-4:]}"


def get_api_key() -> str:
    """
    Ưu tiên:
        1. MANUAL_GEMINI_API_KEY
        2. GEMINI_API_KEY trong .env
    """

    manual = MANUAL_GEMINI_API_KEY.strip()

    if manual and manual != "YOUR_GEMINI_API_KEY":
        return manual

    return os.getenv(
        "GEMINI_API_KEY",
        ""
    ).strip()


def print_separator(
    char="=",
    length=100
):
    print(char * length)


# ============================================================
# GENERIC HTTP JSON REQUEST
# ============================================================

def http_json(
    url: str,
    method: str = "GET",
    payload=None,
    timeout: int = REQUEST_TIMEOUT
):
    """
    HTTP request trả về:
        status
        json_data
        raw_error
    """

    headers = {
        "User-Agent":
            "BabyCare-AI-Gemini-Free-Tier-Tester/1.0",
        "Content-Type":
            "application/json",
    }

    data = None

    if payload is not None:
        data = json.dumps(
            payload
        ).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method=method,
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=timeout
        ) as response:

            body = response.read().decode(
                "utf-8"
            )

            if body:
                return (
                    response.status,
                    json.loads(body),
                    None
                )

            return (
                response.status,
                {},
                None
            )

    except urllib.error.HTTPError as e:

        try:

            body = e.read().decode(
                "utf-8"
            )

            parsed = (
                json.loads(body)
                if body
                else {}
            )

        except Exception:

            parsed = {}

        return (
            e.code,
            parsed,
            body if "body" in locals()
            else str(e)
        )

    except Exception as e:

        return (
            None,
            {},
            str(e)
        )


# ============================================================
# STEP 1
# FETCH MODEL CATALOG
# ============================================================

def fetch_all_models(
    api_key: str
):
    """
    Lấy tất cả model từ:

    GET
    https://generativelanguage.googleapis.com/v1beta/models

    Chỉ giữ model hỗ trợ:
        generateContent
    """

    models = []

    page_token = None

    while True:

        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models"
            f"?key={urllib.parse.quote(api_key)}"
        )

        if page_token:

            url += (
                "&pageToken="
                + urllib.parse.quote(
                    page_token
                )
            )

        status, data, raw = http_json(
            url
        )

        if status != 200:

            error_message = ""

            if isinstance(data, dict):

                error_message = (
                    data
                    .get("error", {})
                    .get(
                        "message",
                        ""
                    )
                )

            if not error_message:
                error_message = raw

            return (
                [],
                f"HTTP {status}: "
                f"{error_message}"
            )

        for model in data.get(
            "models",
            []
        ):

            methods = model.get(
                "supportedGenerationMethods",
                []
            )

            if (
                "generateContent"
                not in methods
            ):
                continue

            name = (
                model
                .get("name", "")
                .replace(
                    "models/",
                    ""
                )
            )

            if not name:
                continue

            models.append({

                "name": name,

                "display_name":
                    model.get(
                        "displayName",
                        name
                    ),

                "description":
                    model.get(
                        "description",
                        ""
                    ),

                "input_token_limit":
                    model.get(
                        "inputTokenLimit"
                    ),

                "output_token_limit":
                    model.get(
                        "outputTokenLimit"
                    ),

            })

        page_token = data.get(
            "nextPageToken"
        )

        if not page_token:
            break

    # Remove duplicate model names

    unique_models = {}

    for model in models:

        unique_models[
            model["name"]
        ] = model

    return (
        list(
            unique_models.values()
        ),
        None
    )


# ============================================================
# ERROR CLASSIFICATION
# ============================================================

def classify_error(
    status,
    data,
    raw
):
    """
    Phân loại response.
    """

    error = {}

    if isinstance(
        data,
        dict
    ):

        error = data.get(
            "error",
            {}
        )

    message = (
        error.get(
            "message",
            ""
        )
        if isinstance(
            error,
            dict
        )
        else ""
    )

    if not message:

        message = raw or ""

    message_lower = (
        str(message)
        .lower()
    )


    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    if status == 200:

        return (
            "CALLABLE",
            message
        )


    # --------------------------------------------------------
    # 404
    # --------------------------------------------------------

    if status == 404:

        if (
            "no longer available"
            in message_lower
        ):

            return (
                "404_NEW_USER",
                message
            )

        return (
            "404_NOT_FOUND",
            message
        )


    # --------------------------------------------------------
    # 429
    # --------------------------------------------------------

    if status == 429:

        if (
            "limit: 0"
            in message_lower
            or
            "limit:0"
            in message_lower
            or
            "quota"
            in message_lower
        ):

            return (
                "QUOTA_0",
                message
            )

        return (
            "429_RATE_LIMIT",
            message
        )


    # --------------------------------------------------------
    # 401 / 403
    # --------------------------------------------------------

    if status in (
        401,
        403
    ):

        return (
            "AUTH_OR_PERMISSION",
            message
        )


    # --------------------------------------------------------
    # 400
    # --------------------------------------------------------

    if status == 400:

        return (
            "BAD_REQUEST",
            message
        )


    # --------------------------------------------------------
    # NETWORK
    # --------------------------------------------------------

    if status is None:

        return (
            "NETWORK_ERROR",
            message
        )


    # --------------------------------------------------------
    # OTHER
    # --------------------------------------------------------

    return (
        f"HTTP_{status}",
        message
    )


# ============================================================
# STEP 2
# TEST GENERATE CONTENT
# ============================================================

def test_generate_content(
    api_key: str,
    model_name: str
):
    """
    Gọi trực tiếp:

    POST
    /v1beta/models/{model}:generateContent

    Không sử dụng LangChain.
    """

    encoded_model = urllib.parse.quote(
        model_name,
        safe=""
    )

    encoded_key = urllib.parse.quote(
        api_key
    )

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{encoded_model}"
        ":generateContent"
        f"?key={encoded_key}"
    )


    payload = {

        "contents": [

            {

                "role": "user",

                "parts": [

                    {
                        "text":
                            "Reply with exactly: OK"
                    }

                ],

            }

        ],

        "generationConfig": {

            "temperature": 0,

            "maxOutputTokens": 5,

        },

    }


    start_time = time.time()

    status, data, raw = http_json(

        url,

        method="POST",

        payload=payload,

    )

    duration_ms = int(
        (
            time.time()
            - start_time
        )
        * 1000
    )


    category, message = (
        classify_error(
            status,
            data,
            raw
        )
    )


    response_text = ""


    # --------------------------------------------------------
    # SUCCESS RESPONSE
    # --------------------------------------------------------

    if status == 200:

        try:

            response_text = (

                data
                ["candidates"]
                [0]
                ["content"]
                ["parts"]
                [0]
                ["text"]

            ).strip()

        except Exception:

            response_text = (
                "(200 OK nhưng "
                "không đọc được response)"
            )


    return {

        "model":
            model_name,

        "status":
            status,

        "category":
            category,

        "duration_ms":
            duration_ms,

        "message":
            message,

        "response":
            response_text,

    }


# ============================================================
# PRINT CATALOG
# ============================================================

def print_model_catalog(
    models
):

    print_separator()

    print(
        f"{'STT':<5} | "
        f"{'MODEL':<48} | "
        f"DISPLAY NAME"
    )

    print_separator()

    for index, model in enumerate(
        models,
        1
    ):

        print(
            f"{index:<5} | "
            f"{model['name']:<48} | "
            f"{model['display_name']}"
        )

    print_separator()


# ============================================================
# PRINT RESULT
# ============================================================

def print_result(
    result
):

    model = result[
        "model"
    ]

    category = result[
        "category"
    ]

    duration = result[
        "duration_ms"
    ]

    response = result[
        "response"
    ]

    # --------------------------------------------------------
    # CALLABLE
    # --------------------------------------------------------

    if category == "CALLABLE":

        print(
            f"   🟢 CALLABLE / "
            f"CÓ THỂ GỌI "
            f"({duration} ms)"
        )

        print(
            f"      Response: "
            f"{response}"
        )


    # --------------------------------------------------------
    # QUOTA 0
    # --------------------------------------------------------

    elif category == "QUOTA_0":

        print(
            f"   🔴 QUOTA = 0 "
            f"({duration} ms)"
        )

        print(
            "      Model tồn tại "
            "nhưng quota hiện tại = 0."
        )


    # --------------------------------------------------------
    # RATE LIMIT
    # --------------------------------------------------------

    elif category == "429_RATE_LIMIT":

        print(
            f"   🟠 RATE LIMIT 429 "
            f"({duration} ms)"
        )

        print(
            "      Request bị giới hạn "
            "tốc độ/quota tạm thời."
        )


    # --------------------------------------------------------
    # 404 NEW USER
    # --------------------------------------------------------

    elif category == "404_NEW_USER":

        print(
            f"   ⚠️ 404 - "
            f"MODEL KHÔNG MỞ CHO NEW USERS "
            f"({duration} ms)"
        )


    # --------------------------------------------------------
    # 404
    # --------------------------------------------------------

    elif category == "404_NOT_FOUND":

        print(
            f"   ⚠️ 404 - "
            f"MODEL KHÔNG KHẢ DỤNG "
            f"({duration} ms)"
        )


    # --------------------------------------------------------
    # AUTH
    # --------------------------------------------------------

    elif category == "AUTH_OR_PERMISSION":

        print(
            f"   ⛔ AUTH / PERMISSION "
            f"({duration} ms)"
        )


    # --------------------------------------------------------
    # BAD REQUEST
    # --------------------------------------------------------

    elif category == "BAD_REQUEST":

        print(
            f"   ⚠️ BAD REQUEST "
            f"({duration} ms)"
        )


    # --------------------------------------------------------
    # OTHER
    # --------------------------------------------------------

    else:

        print(
            f"   ❌ {category} "
            f"({duration} ms)"
        )


    # --------------------------------------------------------
    # RAW ERROR
    # --------------------------------------------------------

    if category != "CALLABLE":

        message = str(
            result["message"]
        )

        message = (
            message
            .replace(
                "\n",
                " "
            )
        )

        if len(message) > 700:

            message = (
                message[:700]
                + "..."
            )

        print(
            f"      Raw: {message}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print_separator()

    print(
        "🤖 GEMINI API KEY / MODEL / "
        "FREE-TIER QUOTA TESTER"
    )

    print_separator()


    # ========================================================
    # API KEY
    # ========================================================

    api_key = get_api_key()


    if not api_key:

        print(
            "❌ KHÔNG TÌM THẤY API KEY!"
        )

        print()

        print(
            "Hãy sửa:"
        )

        print()

        print(
            'MANUAL_GEMINI_API_KEY = '
            '"AQ.xxxxxxxxxxxxx"'
        )

        print()

        print(
            "hoặc đặt GEMINI_API_KEY "
            "trong file .env"
        )

        return


    print(
        "📌 Nguồn API Key:"
    )

    if (
        MANUAL_GEMINI_API_KEY.strip()
        and
        MANUAL_GEMINI_API_KEY.strip()
        != "YOUR_GEMINI_API_KEY"
    ):

        print(
            "   [Nhập trực tiếp trong file]"
        )

    else:

        print(
            "   [Nạp từ file .env]"
        )


    print(
        f"🔑 API Key: "
        f"{mask_key(api_key)}"
    )


    # ========================================================
    # KEY FORMAT
    # ========================================================

    if api_key.startswith(
        "AQ."
    ):

        print(
            "ℹ️ API key dạng AQ.... "
            "được chấp nhận."
        )

        print(
            "ℹ️ Không dùng prefix AIzaSy "
            "để xác định key hợp lệ."
        )

    elif api_key.startswith(
        "AIzaSy"
    ):

        print(
            "ℹ️ API key có prefix "
            "AIzaSy."
        )

    else:

        print(
            "ℹ️ API key không có "
            "prefix AQ. hoặc AIzaSy."
        )

        print(
            "   Script vẫn tiếp tục test."
        )


    # ========================================================
    # STEP 1
    # ========================================================

    print()

    print(
        "🔍 [BƯỚC 1] "
        "ĐANG KIỂM TRA MODEL CATALOG..."
    )

    print()


    models, error = (
        fetch_all_models(
            api_key
        )
    )


    if error:

        print(
            "❌ KHÔNG THỂ LẤY MODEL CATALOG"
        )

        print(
            f"   {error}"
        )

        return


    print(
        f"✅ Tìm thấy "
        f"{len(models)} model "
        f"hỗ trợ generateContent."
    )


    if not models:

        print(
            "❌ Không có model "
            "generateContent."
        )

        return


    print()

    print_model_catalog(
        models
    )


    # ========================================================
    # SELECT MODELS
    # ========================================================

    available_names = {
        model["name"]
        for model in models
    }


    if TEST_ALL_MODELS:

        models_to_test = models

        print()

        print(
            "⚠️ TEST_ALL_MODELS = True"
        )

        print(
            f"   Sẽ test "
            f"{len(models_to_test)} model."
        )

        print(
            "   Có thể phát sinh 429 "
            "nếu request quá nhanh."
        )


    else:

        selected_names = [

            name

            for name in PRIORITY_MODELS

            if name in available_names

        ]


        models_to_test = [

            next(
                model
                for model in models
                if model["name"] == name
            )

            for name in selected_names

        ]


        print()

        print(
            "ℹ️ TEST_ALL_MODELS = False"
        )

        print(
            f"   Chỉ test "
            f"{len(models_to_test)} "
            "model ưu tiên."
        )


    # ========================================================
    # STEP 2
    # ========================================================

    print()

    print_separator()

    print(
        "🔍 [BƯỚC 2] "
        "LIVE GENERATION TEST"
    )

    print_separator()


    print(
        "⚠️ Đây mới là bước xác định "
        "quota inference thực tế."
    )

    print()

    print(
        "📌 Endpoint:"
    )

    print(
        "   Google Generative Language REST API"
    )

    print(
        "📌 Client:"
    )

    print(
        "   urllib.request"
    )

    print(
        "📌 LangChain:"
    )

    print(
        "   ❌ Không sử dụng"
    )


    results = []


    # ========================================================
    # TEST EACH MODEL
    # ========================================================

    for index, model in enumerate(
        models_to_test,
        1
    ):

        print()

        print(
            "─" * 100
        )

        print(
            f"📌 [{index}/"
            f"{len(models_to_test)}]"
            f" Testing Model: "
            f"[{model['name']}]"
        )

        print(
            f"   Display Name: "
            f"{model['display_name']}"
        )


        result = (
            test_generate_content(
                api_key,
                model["name"]
            )
        )


        results.append(
            result
        )


        print_result(
            result
        )


        # ----------------------------------------------------
        # DELAY
        # ----------------------------------------------------

        if (
            index
            <
            len(models_to_test)
        ):

            time.sleep(
                DELAY_BETWEEN_REQUESTS
            )


    # ========================================================
    # SUMMARY
    # ========================================================

    callable_models = [

        result

        for result in results

        if result[
            "category"
        ]
        ==
        "CALLABLE"

    ]


    quota_zero = [

        result

        for result in results

        if result[
            "category"
        ]
        ==
        "QUOTA_0"

    ]


    rate_limited = [

        result

        for result in results

        if result[
            "category"
        ]
        ==
        "429_RATE_LIMIT"

    ]


    models_404 = [

        result

        for result in results

        if result[
            "category"
        ]
        in (
            "404_NOT_FOUND",
            "404_NEW_USER",
        )

    ]


    auth_errors = [

        result

        for result in results

        if result[
            "category"
        ]
        ==
        "AUTH_OR_PERMISSION"

    ]


    # ========================================================
    # FINAL TABLE
    # ========================================================

    print()

    print_separator()

    print(
        "📊 KẾT QUẢ CUỐI CÙNG"
    )

    print_separator()


    print()

    print(
        f"🟢 CALLABLE       : "
        f"{len(callable_models)}"
    )

    print(
        f"🔴 QUOTA = 0      : "
        f"{len(quota_zero)}"
    )

    print(
        f"🟠 RATE LIMIT 429 : "
        f"{len(rate_limited)}"
    )

    print(
        f"⚠️ MODEL 404      : "
        f"{len(models_404)}"
    )

    print(
        f"⛔ AUTH/PERMISSION: "
        f"{len(auth_errors)}"
    )

    print(
        f"📊 TOTAL TESTED   : "
        f"{len(results)}"
    )


    # ========================================================
    # CALLABLE MODELS
    # ========================================================

    print()

    print_separator("-")

    print(
        "🟢🟢🟢 "
        "MODEL CÓ THỂ GỌI ĐƯỢC "
        "🟢🟢🟢"
    )

    print_separator("-")


    if callable_models:

        for result in callable_models:

            print(
                f"  ✅ "
                f"{result['model']:<50}"
                f" {result['duration_ms']} ms"
            )

    else:

        print(
            "  ❌ Không có model nào "
            "trả HTTP 200."
        )


    # ========================================================
    # QUOTA ZERO
    # ========================================================

    if quota_zero:

        print()

        print(
            "🔴 MODEL QUOTA = 0:"
        )

        for result in quota_zero:

            print(
                f"  • "
                f"{result['model']}"
            )


    # ========================================================
    # RATE LIMIT
    # ========================================================

    if rate_limited:

        print()

        print(
            "🟠 MODEL RATE LIMIT:"
        )

        for result in rate_limited:

            print(
                f"  • "
                f"{result['model']}"
            )


    # ========================================================
    # 404
    # ========================================================

    if models_404:

        print()

        print(
            "⚠️ MODEL 404:"
        )

        for result in models_404:

            print(
                f"  • "
                f"{result['model']}"
            )


    # ========================================================
    # ANALYSIS
    # ========================================================

    print()

    print_separator()

    print(
        "🧠 PHÂN TÍCH"
    )

    print_separator()


    print(
        """
1. LIST MODELS = API key truy cập được Model Catalog.

   Điều này KHÔNG có nghĩa tất cả model đều
   có quota inference.


2. HTTP 200 = generateContent thành công.

   Đây là kết quả quan trọng nhất để xác định
   model thực sự gọi được.


3. QUOTA = 0

   Model tồn tại nhưng project/account hiện tại
   không được cấp quota cho request đó.


4. 429 RATE LIMIT

   Request bị giới hạn tốc độ hoặc quota tạm thời.

   Không nên kết luận API key bị hỏng.


5. 404

   Model không khả dụng cho request hiện tại,
   hoặc model đã bị giới hạn/ngừng hỗ trợ.


6. AUTH / PERMISSION

   Kiểm tra API key hoặc quyền của project.


============================================================
KẾT LUẬN:
============================================================

Nếu xuất hiện:

    🟢 CALLABLE

thì model đó là model bạn có thể gọi
bằng API key hiện tại.

Nếu không có 🟢 CALLABLE:

    API key vẫn có thể hợp lệ,
    nhưng hiện tại không có model nào
    trả về generateContent thành công.
"""
    )


    print_separator()

    print(
        "🏁 TEST FINISHED"
    )

    print_separator()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()