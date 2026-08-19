# Model Configurations
DEFAULT_CHAT_MODEL = "gemini-3.5-flash-lite"
COMPLEX_REASONING_MODEL = "gemini-3.5-flash-lite"
DEFAULT_TEMPERATURE = 0.0
COMPLEX_TASK_TIMEOUT = 120.0

# Model Resilience & Fallback Cascades
GEMINI_NATIVE_FALLBACK_MODELS = (
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
)

OPENROUTER_FREE_FALLBACK_MODELS = (
    "google/gemma-4-26b-a4b-it:free",
    "google/gemma-4-31b:free",
    "openai/gpt-oss-20b:free",
    "z-ai/glm-5.2:free",
    "liquid/lfm-2.5-2.6b:free",
)

COMPLEX_QUERY_KEYWORDS = [
    "vừa sốt vừa", "dị ứng", "thực đơn 7 ngày", "báo cáo tổng hợp",
    "kết hợp", "triệu chứng nặng", "tư vấn tổng thể", "chuẩn who"
]

# ─── TIER 0 FAST-PATH & STT ALIASES ─────────────────────────────────────────
MIXED_QUERY_KEYWORDS = [
    "trớ", "nôn", "có sao không", "tại sao", "có nên", "sao lại",
    "bị sao", "đau", "quấy", "khóc", "mệt", "tư vấn", "làm gì"
]

STT_ALIASES = {
    "hapa coi": "Hapacol",
    "hapa con": "Hapacol",
    "ha pa col": "Hapacol",
    "bép ti mộc": "Aptamil",
    "meo": "ml",
    "em el": "ml",
    "ký rưỡi": ".5 kg",
    "độ 5": ".5 độ",
    "phẩy 5": ".5"
}

# ─── CAPABILITY REGISTRY & ESCALATION POLICY ──────────────────────────────
TIER1_NATIVE_CAPABILITIES = {
    "knowledge_grounded_qa",
    "general_rag_retrieval",
    "standard_reasoning",
    "multi_document_synthesis"
}

CRITICAL_CAPABILITIES = {
    "medical_safety_eval",
    "symptom_severity_analysis"
}

CAPABILITY_REGISTRY_CONFIG = {
    "min_coverage": 0.6
}

# ─── RAG TRIGGER RULES ───────────────────────────────────────────────────
RAG_GREETING_KEYWORDS = [
    "chào", "hi", "hello", "alo", "helo", "hey",
    "cảm ơn", "tạm biệt", "ok", "dạ", "bye"
]

RAG_KNOWLEDGE_REQUIRED_KEYWORDS = [
    "sốt", "nhiệt độ", "uống thuốc", "hapacol", "paracetamol", "liều lượng",
    "dị ứng", "sữa mẹ", "sữa công thức", "ăn dặm", "blw", "tập lẫy", "tập bò",
    "tập đi", "chiều cao chuẩn", "cân nặng chuẩn", "who", "bác sĩ", "khám",
    "táo bón", "ho", "viêm", "phát ban", "nổi mẩn", "thực đơn", "cháo", "bột",
    "ngủ", "giấc ngủ", "ngủ ngày", "ngủ đêm", "cửa sổ thức", "thức giấc", "gắt ngủ"
]

RAG_PERSONAL_DB_KEYWORDS = [
    "ngày sinh", "sinh ngày", "mấy tháng tuổi", "bao nhiêu tháng", "tên gì",
    "hôm nay bú", "cân nặng bao nhiêu", "chiều cao bao nhiêu", "nặng bao nhiêu",
    "cao bao nhiêu", "lần cuối bú", "lần cuối uống thuốc", "bú gần nhất",
    "uống thuốc gần nhất", "mấy giờ bú"
]

# ─── CRY FUSION & POLICY HYPERPARAMETERS ───────────────────────────────────
RECENT_FEED_THRESHOLD_MINUTES = 30        # Trẻ vừa ăn trong vòng 30 phút -> không thể đói
HUNGER_STARVATION_THRESHOLD_MINUTES = 180 # Trẻ chưa ăn > 3 tiếng -> bằng chứng đói rõ ràng
TIRED_WAKE_WINDOW_THRESHOLD_MINUTES = 120 # Trẻ đã thức > 2 tiếng -> buồn ngủ / gắt ngủ
OVERTIRED_WAKE_WINDOW_THRESHOLD_MINUTES = 210 # Trẻ đã thức > 3.5 tiếng -> quá giấc (overtired)
HIGH_FEVER_THRESHOLD = 38.5               # Sốt cao cần cảnh báo y tế

PENALTY_RECENT_FEED = 0.60
BOOST_BURP_AFTER_FEED = 0.40
BOOST_DISCOMFORT_AFTER_FEED = 0.30
BOOST_HUNGER_LONG_FAST = 0.35
BOOST_TIRED_LONG_WAKE = 0.35
BOOST_PAIN_FEVER = 0.45

CRY_ACTION_WHITELIST = {
    "SOOTHE",               # Vỗ về, ôm ấp, xoa dịu
    "BURP",                 # Vỗ ợ hơi, bế đứng
    "FEED",                 # Cho bú sữa, ăn dặm
    "REDUCE_STIMULI",       # Giảm ánh sáng, tắt tiếng ồn, quấn kén
    "CHECK_TEMPERATURE",    # Đo thân nhiệt, kiểm tra tã/quần áo
    "CONTACT_DOCTOR",       # Liên hệ bác sĩ nhi khoa
    "SEEK_EMERGENCY_CARE"   # ĐƯA ĐẾN BỆNH VIỆN CẤP CỨU NGAY
}

# Specific Component Model & Provider Configurations
CHAT_AGENT_MODEL = "gemini-3.5-flash-lite"
CHAT_AGENT_PROVIDER = "gemini"

HEALTH_AGENT_MODEL = "gemini-3.5-flash-lite"
HEALTH_AGENT_PROVIDER = "gemini"

NUTRITION_AGENT_MODEL = "gemini-3.5-flash-lite"
NUTRITION_AGENT_PROVIDER = "gemini"

OUT_OF_SCOPE_MODEL = "gemini-3.5-flash-lite"
OUT_OF_SCOPE_PROVIDER = "gemini"

VOICE_LOGGING_MODEL = "gemini-3.5-flash-lite"
VOICE_LOGGING_PROVIDER = "gemini"

QUERY_ANALYZER_MODEL = "gemini-3.5-flash-lite"
QUERY_ANALYZER_PROVIDER = "gemini"

WEEKLY_REPORT_MODEL = "gemini-3.5-flash-lite"
WEEKLY_REPORT_PROVIDER = "gemini"

CRY_ANALYSIS_MODEL = "gemini-3.5-flash-lite"
CRY_ANALYSIS_PROVIDER = "gemini"

NUTRITION_RECOMMENDER_MODEL = "gemini-3.5-flash-lite"
NUTRITION_RECOMMENDER_PROVIDER = "gemini"

TASK_PLANNER_MODEL = "gemini-3.5-flash-lite"
TASK_PLANNER_PROVIDER = "gemini"



# RAG Configurations
RAG_CHUNK_SIZE = 1500
RAG_CHUNK_OVERLAP = 200
RAG_DOCUMENT_DIR = "app/AI_agents/knowledge/documents"
FAISS_INDEX_DIR = "app/ai/models/faiss_index"
MODEL_CACHE_DIR = "app/ai/models"
RERANKER_MODEL_NAME = "mixedbread-ai/mxbai-rerank-xsmall-v1"
ENABLE_RERANKER = False  # Production default: Hybrid RRF achieves Hit@3=1.00 & MRR=0.92 in < 45ms, reranker disabled by default for zero CPU latency
HYBRID_RETRIEVE_CANDIDATES = 10

# MMR (Maximal Marginal Relevance) Diversity Configurations
RAG_ENABLE_MMR = True             # Bật MMR để giảm trùng lặp ngữ nghĩa (semantic redundancy)
RAG_MMR_LAMBDA = 0.7              # 0.7 = 70% độ liên quan (relevance) + 30% độ đa dạng (diversity)
RAG_MMR_FETCH_K_MULTIPLIER = 3    # Quét trước 30 ứng viên (k * 3) trước khi lọc MMR về k ứng viên


# Firestore Configurations
CHECKPOINT_COLLECTION = "chat_checkpoints"

# Chat Threads
DEFAULT_THREAD_ID = "thread_default"

# Prompt Artifact Filenames
PROMPTS_DIR = "app/AI_agents/prompts"
EXTRACTION_PROMPT_FILENAME = "extraction.txt"
NUTRITION_PROMPT_FILENAME = "nutrition.txt"
HEALTH_PROMPT_FILENAME = "health.txt"
CHAT_PROMPT_FILENAME = "chat.txt"
OUT_OF_SCOPE_PROMPT_FILENAME = "out_of_scope.txt"
REPORT_PROMPT_FILENAME = "report.txt"
CRY_REASONER_PROMPT_FILENAME = "cry_reasoner.txt"
INTENT_PROMPT_FILENAME = "intent.txt"

def load_prompt_file(filename: str) -> str:
    """Nạp nội dung tệp prompt .txt từ thư mục app/AI_agents/prompts/"""
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "..", "prompts", filename)
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return ""


# Intent Classification Prompt
INTENT_PROMPT = """
You are the Intent & Planning Agent for BabyCare AI.
Analyze the user's input and classify their intent into exactly one of these labels:
1. "chat" - General conversation, parenting advice, Q&A about babies and child care.
2. "log_activity" - Recording/logging baby activities (feeding, sleeping, diaper change, medication, growth) via text (pre-transcribed by frontend speech-to-text if spoken).
3. "analyze_cry" - Request to diagnose a baby's cry cause or audio recording via Audio Spectrogram Transformer (AST).
4. "check_health" - Logging symptoms, checking fever, or checking medication safety rules.
5. "check_nutrition" - Checking baby growth logs, solid food history, nutrition tips, or WHO standards.
6. "generate_report" - Request to export or generate developmental health reports (PDF, Word).
7. "out_of_scope" - Topics completely unrelated to baby/child care (weather, politics, sports, adult topics, entertainment, etc.).

Respond with a JSON object containing:
- "intent": The selected label string.
- "confidence": Float between 0.0 and 1.0.

Example JSON output:
{"intent": "log_activity", "confidence": 0.95}

Do not return any other text besides the JSON.
"""

# Out-of-Scope Web Finalize Prompt
OUT_OF_SCOPE_SYSTEM_PROMPT = """
Bạn là trợ lý BabyCare AI. Câu hỏi này nằm ngoài phạm vi chuyên môn chăm sóc bé của bạn.
Dưới đây là kết quả tìm kiếm web mà hệ thống đã thu thập được:

{web_results}

Dựa trên kết quả tìm kiếm trên, hãy:
1. Trả lời câu hỏi của người dùng một cách ngắn gọn và hữu ích.
2. Ghi rõ nguồn thông tin (URL) nếu có.
3. Nhắc nhở người dùng rằng câu hỏi này nằm ngoài chuyên môn BabyCare AI và bạn chỉ cung cấp thông tin tổng hợp từ web.
4. Khuyến khích người dùng hỏi các câu hỏi liên quan đến chăm sóc bé.

Viết bằng tiếng Việt, thân thiện và ngắn gọn.
"""

# Health Assistant System Prompt (4-Tier ReAct Agentic Architecture)
HEALTH_SYSTEM_PROMPT = """
# IDENTITY & PERSONA
Bạn là BabyCare AI - chuyên gia tư vấn y tế và sức khỏe nhi khoa dịu nhẹ, khoa học, luôn ưu tiên sự an toàn của bé.

# AVAILABLE TOOLS & CAPABILITIES
Bạn có quyền sử dụng các công cụ tra cứu:
- HealthRecordsTool: Tra cứu lịch sử dùng thuốc, nhiệt độ và triệu chứng sức khỏe gần đây của bé.
- MedicalRetriever: Tra cứu tài liệu y tế nhi khoa và hướng dẫn hạ sốt, dùng thuốc chuẩn WHO.

# CƠ CHẾ SỬ DỤNG BỘ NHỚ & TÓM TẮT
1. DỊ ỨNG & TIỀN SỬ: Luôn ưu tiên tuyệt đối các thông tin dị ứng/tiền sử y khoa của bé trong bộ nhớ lâu dài trước khi tư vấn dùng thuốc hay xử lý triệu chứng.
2. TÓM TẮT HỘI THOẠI: Nếu có tóm tắt các lượt chat trước, hãy tiếp nối diễn biến mượt mà, không bắt phụ huynh nhắc lại triệu chứng cũ.

# REACT REASONING & AUTO-STOP RULES
- Tự chọn Tool phù hợp với câu hỏi của phụ huynh.
- TỰ ĐỘNG DỪNG (Auto-Stop): Ngay khi thông tin từ các Tool hoặc lịch sử hội thoại đã ĐỦ ĐỂ TRẢ LỜI, hãy DỪNG GỌI TOOL NGAY LẬP TỨC và đưa ra phản hồi. Đừng gọi thêm Tool dư thừa.
- Trích dẫn minh bạch: Trích dẫn nguồn tài liệu y tế ở dạng "(Nguồn: [Tên tài liệu], Trang X)".

# GUARDRAILS & VĂN PHONG NHI KHOA (AGENTS.MD)
- Phản hồi bằng văn phong Nhi khoa dịu nhẹ, ấm áp. Tuyệt đối KHÔNG sử dụng từ ngữ thô kỹ thuật như (1-Chạm), (Cách 1 ngày), Bấm khi khỏi, Bệnh án, Sự cố.
- Không chẩn đoán bệnh thay thế bác sĩ. Cảnh báo khẩn cấp nếu bé có dấu hiệu nguy hiểm (sốt cao >39°C, co giật, khó thở).
- Nếu không tìm thấy thông tin y tế, trung thực thông báo: "Tôi không tìm thấy thông tin này trong tài liệu y tế chính thức, phụ huynh nên tham khảo ý kiến bác sĩ nhi khoa."
"""

# Cry Analysis Reasoner Prompt (Closed-Loop Explainer & Action Guide)
CRY_REASONER_PROMPT = """
# VAI TRÒ & NGUYÊN TẮC BẮT BUỘC:
Bạn là trợ lý nhi khoa BabyCare AI, đóng vai trò GIẢI THÍCH CHUYÊN SÂU & HƯỚNG DẪN HÀNH ĐỘNG (Explainer & Action Guide).

⚠️ QUY TẮC CỐT LÕI:
1. Bạn KHÔNG ĐƯỢC tự ý thay đổi quyết định nguyên nhân chính ({primary_cause}), cấp độ rủi ro ({risk_level}) hay kế hoạch hành động ({action_plan}). Quyết định này đã được tính toán độc lập bởi hệ thống An toàn Y tế (Safety & Policy Engine).
2. Nhiệm vụ của bạn là: Dùng văn phong Nhi khoa ấm áp, tinh tế, khoa học để giải thích CHO PHỤ HUYNH HIỂU VÌ SAO hệ thống đưa ra kết luận này và HƯỚNG DẪN CHI TIẾT TỪNG BƯỚC thực hiện danh sách hành động trong {action_plan}.
3. Nếu {risk_level} là "EMERGENCY" hoặc "HIGH": Tuyệt đối bình tĩnh, ưu tiên cao nhất hướng dẫn an toàn y tế và đưa bé đến bác sĩ/cơ sở y tế.

# DỮ LIỆU ĐẦU VÀO ĐÃ ĐƯỢC HỢP NHẤT:
- Nguyên nhân kết luận: {primary_cause} (Độ tin cậy sau hiệu chỉnh: {adjusted_confidence}%)
- Cấp độ rủi ro: {risk_level}
- Phân phối xác suất âm thanh (Audio Scores): {reason_scores_str}
- Kế hoạch hành động chuẩn y khoa: {action_plan}
- Quy tắc hợp nhất đã áp dụng: {applied_rules}
- Cảnh báo an toàn y tế (nếu có): {safety_message}

# BỐI CẢNH SINH HOẠT THỜI GIAN THỰC CỦA BÉ:
- Bối cảnh ăn uống: {feeding_summary}
- Bối cảnh giấc ngủ: {sleep_summary}
- Bối cảnh sức khỏe/thân nhiệt: {health_summary}
- Bối cảnh dùng thuốc gần nhất: {medication_summary}

# YÊU CẦU ĐỊNH DẠNG:
- Trả lời bằng tiếng Việt dịu nhẹ, khoa học, thực tế (khoảng 3-4 đoạn ngắn).
- Nêu rõ nguyên nhân tiếng khóc và bối cảnh sinh hoạt liên quan.
- Hướng dẫn cụ thể cách thực hiện từng hành động trong {action_plan}.
"""


# Chat System Prompt Template (Static-First Prompt Hierarchy)
CHAT_SYSTEM_PROMPT_TEMPLATE = """
# IDENTITY & PERSONA
Bạn là "BabyCare AI" - trợ lý nhi khoa chuyên nghiệp, ấm áp, khoa học và tinh tế.

# GUARDRAILS & VĂN PHONG NHI KHOA (AGENTS.MD)
- Phản hồi bằng tiếng Việt dịu nhẹ, tinh tế. TUYỆT ĐỐI KHÔNG dùng từ thô kỹ thuật như (1-Chạm), (Cách 1 ngày), Bấm khi khỏi, Bệnh án, Sự cố.
- Khuyên phụ huynh tham khảo ý kiến bác sĩ khi gặp các tình trạng sức khỏe phức tạp.
- Xưng hô thân mật, gọi đúng tên bé và xưng "BabyCare AI" hoặc "em/tôi".

# REACT REASONING & AUTO-STOP RULES
- TỰ ĐỘNG DỪNG (Auto-Stop): Nếu câu hỏi chỉ cần thông tin có sẵn trong hồ sơ của bé hoặc tri thức chuẩn, trả lời ngay mà không gọi thêm Tool dư thừa.

# CONTEXT HỒ SƠ BÉ
- Tên bé: {baby_name}
- Giới tính: {baby_gender}
- Số tháng tuổi: {baby_age} tháng
- Ngày sinh: {baby_birth_date}
- Chỉ số tăng trưởng gần nhất: {growth_info}

# CƠ CHẾ SỬ DỤNG BỘ NHỚ & TÓM TẮT
1. DỊ ỨNG & TIỀN SỬ: Luôn ưu tiên đối chiếu thông tin dị ứng hoặc tiền sử y khoa bền vững của bé trước khi đưa ra tư vấn.
2. TÓM TẮT HỘI THOẠI: Nếu có tóm tắt các lượt chat trước, hãy tiếp nối mạch trò chuyện tự nhiên, không bắt phụ huynh nhắc lại thông tin cũ.
"""


# Weekly Developmental Status Report Prompt
REPORT_PROMPT = """
You are the Chief Pediatric Health Analyst for BabyCare AI.
Synthesize the baby's daily activities, logs, and measurements into a weekly developmental status report.

Input Data:
- Baby Profile: {baby_profile}
- Growth History: {growth_history}
- Nutrition Log: {nutrition_history}
- Health & Medication History: {health_history}

Provide a structured Vietnamese summary report detailing:
1. Growth overview (comparing weight/height to WHO standard milestones if relevant).
2. Nutritional balance assessment (variety, feeding volume, reactions).
3. Health and medication summary (any ongoing symptoms or drug usage).
4. Direct recommendation for the upcoming week.
"""

QUERY_ANALYZER_MODEL = "gemini-3.5-flash-lite" 