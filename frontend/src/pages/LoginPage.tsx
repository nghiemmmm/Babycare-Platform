import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ApiClientError } from "../lib/authClient";
import AuthLayout from "../components/AuthLayout";
import { Eye, EyeOff } from "lucide-react";

const inputClass =
  "w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-all";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  // apiFetch() tự đăng xuất và điều hướng về đây ngay khi gặp 401 không làm mới token được -
  // đọc cờ khi trang này MOUNT (không phải module-scope, vì LoginPage mount lại mỗi lần
  // RequireAuth điều hướng tới đây) rồi xoá ngay để không hiện lại nếu quay lại /login sau đó
  // vì lý do khác (vd. bấm "Đăng xuất" thủ công).
  const [error, setError] = useState<string | null>(() => {
    if (sessionStorage.getItem("bc_session_expired") === "1") {
      sessionStorage.removeItem("bc_session_expired");
      return "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.";
    }
    return null;
  });
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Không thể đăng nhập, vui lòng thử lại.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Chào bạn quay lại" subtitle="Đăng nhập để tiếp tục theo dõi hồ sơ của bé.">
      {error && (
        <div className="mb-4 px-4 py-2.5 rounded-xl bg-red-50 border border-red-100 text-red-600 text-xs font-semibold">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <label htmlFor="email" className="text-xs font-bold text-slate-600">
            Email
          </label>
          <input
            id="email"
            type="email"
            className={inputClass}
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="vd. minhan2020@gmail.com"
          />
        </div>
        <div className="space-y-1.5">
          <label htmlFor="password" className="text-xs font-bold text-slate-600">
            Mật khẩu
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              className={`${inputClass} pr-10`}
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors p-1 cursor-pointer"
              tabIndex={-1}
              aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2.5 rounded-xl bg-primary text-white text-sm font-bold shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all disabled:opacity-60 cursor-pointer"
        >
          {submitting ? "Đang đăng nhập…" : "Đăng nhập"}
        </button>

        <div className="relative my-3 flex items-center justify-center">
          <div className="border-t border-slate-200 w-full"></div>
          <span className="bg-white px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider absolute">HOẶC</span>
        </div>

        <button
          type="button"
          disabled={submitting}
          onClick={async () => {
            setEmail("nghiem@babycare.com");
            setPassword("Nghiem1234");
            setError(null);
            setSubmitting(true);
            try {
              await login("nghiem@babycare.com", "Nghiem1234");
              navigate("/", { replace: true });
            } catch (err) {
              setError(err instanceof ApiClientError ? err.message : "Không thể đăng nhập tài khoản Demo.");
            } finally {
              setSubmitting(false);
            }
          }}
          className="w-full py-2.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-bold hover:bg-emerald-100 transition-all disabled:opacity-60 cursor-pointer flex items-center justify-center gap-2"
        >
          <span>🚀 Đăng nhập nhanh (Tài khoản Demo)</span>
        </button>
      </form>

      <div className="mt-4 text-center">
        <button
          onClick={() => navigate("/forgot-password")}
          className="text-xs font-semibold text-primary hover:underline cursor-pointer"
        >
          Quên mật khẩu?
        </button>
      </div>

      <div className="mt-3 text-center text-xs text-slate-500">
        Chưa có tài khoản?{" "}
        <button onClick={() => navigate("/register")} className="font-bold text-primary hover:underline cursor-pointer">
          Đăng ký ngay
        </button>
      </div>
    </AuthLayout>
  );
}
