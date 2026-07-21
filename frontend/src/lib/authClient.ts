// Auth client: lưu token, gọi API /auth/*, và bọc fetch() để tự đính kèm
// Authorization + tự làm mới token khi hết hạn (401) cho toàn bộ app.
//
// Dùng đường dẫn tương đối "/api/v1/..." giống các fetch() còn lại trong
// App.tsx - server.ts (Express) đã proxy "/api/v1/*" sang backend FastAPI,
// và tự chèn "Bearer mock-token" nếu request KHÔNG có Authorization. Khi
// người dùng đã đăng nhập thật, apiFetch() luôn gửi kèm id_token thật nên
// mock-token sẽ không còn được dùng tới.

export interface AuthTokenResponse {
  uid: string;
  email: string | null;
  id_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface UserProfile {
  email: string | null;
  name: string | null;
  role: string;
  active: boolean;
  first_login: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
  phone: string | null;
}

export interface UserMeResponse {
  uid: string;
  email: string | null;
  name: string | null;
  picture: string | null;
  profile: UserProfile | null;
}

export interface Message {
  message: string;
}

const STORAGE_KEYS = {
  idToken: "bc_id_token",
  refreshToken: "bc_refresh_token",
  uid: "bc_uid",
  email: "bc_email",
} as const;

export const AUTH_EXPIRED_EVENT = "bc:auth-expired";

export const authStorage = {
  get idToken(): string | null {
    return localStorage.getItem(STORAGE_KEYS.idToken);
  },
  get refreshToken(): string | null {
    return localStorage.getItem(STORAGE_KEYS.refreshToken);
  },
  get uid(): string | null {
    return localStorage.getItem(STORAGE_KEYS.uid);
  },
  get email(): string | null {
    return localStorage.getItem(STORAGE_KEYS.email);
  },
  save(tokens: AuthTokenResponse) {
    localStorage.setItem(STORAGE_KEYS.idToken, tokens.id_token);
    localStorage.setItem(STORAGE_KEYS.refreshToken, tokens.refresh_token);
    localStorage.setItem(STORAGE_KEYS.uid, tokens.uid);
  },
  saveEmail(email: string) {
    localStorage.setItem(STORAGE_KEYS.email, email);
  },
  clear() {
    localStorage.removeItem(STORAGE_KEYS.idToken);
    localStorage.removeItem(STORAGE_KEYS.refreshToken);
    localStorage.removeItem(STORAGE_KEYS.uid);
    localStorage.removeItem(STORAGE_KEYS.email);
  },
};

export class ApiClientError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function parseErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (body && typeof body.message === "string") return body.message;
    // Lỗi validate 422 của FastAPI/Pydantic không có field "message" mà trả về
    // {"detail": "..."} hoặc {"detail": [{"msg": "...", ...}, ...]} - nếu bỏ qua trường hợp
    // này, người dùng chỉ thấy "Yêu cầu thất bại (mã lỗi 422)" chung chung dù backend đã có
    // thông tin cụ thể hơn (vd. mật khẩu quá ngắn, email sai định dạng).
    if (body && typeof body.detail === "string") return body.detail;
    if (body && Array.isArray(body.detail) && body.detail.length > 0) {
      const messages = body.detail
        .map((item: { msg?: string }) => item?.msg)
        .filter((msg: unknown): msg is string => typeof msg === "string");
      if (messages.length > 0) return messages.join(" ");
    }
  } catch {
    // response không phải JSON - bỏ qua, dùng message mặc định bên dưới
  }
  return `Yêu cầu thất bại (mã lỗi ${response.status}).`;
}

let refreshPromise: Promise<boolean> | null = null;

async function refreshIdToken(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const refreshToken = authStorage.refreshToken;
    if (!refreshToken) return false;
    try {
      const response = await fetch("/api/v1/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!response.ok) return false;
      const tokens: AuthTokenResponse = await response.json();
      authStorage.save(tokens);
      return true;
    } catch {
      return false;
    }
  })();

  const result = await refreshPromise;
  refreshPromise = null;
  return result;
}

/**
 * Wrapper quanh fetch() gốc: tự đính kèm `Authorization: Bearer <id_token>`
 * nếu đã đăng nhập, tự thử làm mới token và gọi lại một lần khi gặp 401.
 * Cùng chữ ký với fetch() để thay thế trực tiếp mọi lệnh gọi hiện có trong App.tsx.
 */
export async function apiFetch(input: string, init: RequestInit = {}, _isRetry = false): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = authStorage.idToken;
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(input, { ...init, headers });

  if (response.status === 401 && token && !_isRetry) {
    const refreshed = await refreshIdToken();
    if (refreshed) {
      return apiFetch(input, init, true);
    }
    authStorage.clear();
    // RequireAuth điều hướng về /login ngay khi AUTH_EXPIRED_EVENT khiến isAuthenticated=false -
    // nhanh tới mức unmount cả cây component gọi apiFetch trước khi kịp hiện bất kỳ thông báo
    // lỗi nào tại chỗ. Lưu cờ để LoginPage tự đọc và giải thích lý do bị đăng xuất, thay vì
    // người dùng thấy "tự nhiên bị đá về trang đăng nhập" không rõ nguyên do.
    sessionStorage.setItem("bc_session_expired", "1");
    window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
  }

  return response;
}

function jsonBody(body: unknown): RequestInit {
  return { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

async function authRequest<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, init);
  if (!response.ok) {
    throw new ApiClientError(await parseErrorMessage(response), response.status);
  }
  return (await response.json()) as T;
}

export const authApi = {
  register: (email: string, password: string, name?: string) =>
    authRequest<AuthTokenResponse>("/auth/register", jsonBody({ email, password, name })),
  login: (email: string, password: string) =>
    authRequest<AuthTokenResponse>("/auth/login", jsonBody({ email, password })),
  me: () => apiFetch("/api/v1/auth/me").then(async (res) => {
    if (!res.ok) throw new ApiClientError(await parseErrorMessage(res), res.status);
    return (await res.json()) as UserMeResponse;
  }),
  forgotPassword: (email: string) => authRequest<Message>("/auth/forgot-password", jsonBody({ email })),
  verifyResetOtp: (email: string, otp: string) =>
    authRequest<Message>("/auth/verify-reset-otp", jsonBody({ email, otp })),
  resetPassword: (email: string, otp: string, newPassword: string) =>
    authRequest<Message>("/auth/reset-password", jsonBody({ email, otp, new_password: newPassword })),
};
