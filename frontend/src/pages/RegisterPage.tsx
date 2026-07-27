import { useState, type FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ApiClientError } from "../lib/authClient";
import AuthLayout from "../components/AuthLayout";

const inputClass =
  "w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-all";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  // Cho phép quay lại đúng trang đã điều hướng tới đây (vd. /invite/:token khi người được mời
  // chưa có tài khoản) thay vì luôn đưa về "/" sau khi đăng ký thành công.
  const redirectTo = searchParams.get("redirect") || "/";
  const [name, setName] = useState("");
  const [email, setEmail] = useState(() => searchParams.get("email") || "");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Mật khẩu xác nhận không khớp.");
      return;
    }

    setSubmitting(true);
    try {
      await register(email, password, name || undefined);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Không thể đăng ký, vui lòng thử lại.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Tạo tài khoản mới" subtitle="Bắt đầu ghi lại hành trình lớn lên của bé.">
      {error && (
        <div className="mb-4 px-4 py-2.5 rounded-xl bg-red-50 border border-red-100 text-red-600 text-xs font-semibold">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <label htmlFor="name" className="text-xs font-bold text-slate-600">
            Tên của bạn
          </label>
          <input
            id="name"
            type="text"
            className={inputClass}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Tuỳ chọn"
          />
        </div>
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
          <input
            id="password"
            type="password"
            className={inputClass}
            required
            minLength={6}
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Tối thiểu 6 ký tự"
          />
        </div>
        <div className="space-y-1.5">
          <label htmlFor="confirm-password" className="text-xs font-bold text-slate-600">
            Xác nhận mật khẩu
          </label>
          <input
            id="confirm-password"
            type="password"
            className={inputClass}
            required
            minLength={6}
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Nhập lại mật khẩu"
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2.5 rounded-xl bg-primary text-white text-sm font-bold shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all disabled:opacity-60 cursor-pointer"
        >
          {submitting ? "Đang tạo tài khoản…" : "Đăng ký"}
        </button>
      </form>

      <div className="mt-4 text-center text-xs text-slate-500">
        Đã có tài khoản?{" "}
        <button
          onClick={() => navigate(`/login${redirectTo !== "/" ? `?redirect=${encodeURIComponent(redirectTo)}` : ""}`)}
          className="font-bold text-primary hover:underline cursor-pointer"
        >
          Đăng nhập
        </button>
      </div>
    </AuthLayout>
  );
}
