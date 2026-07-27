import { useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { authApi, ApiClientError } from "../lib/authClient";
import { OtpInput } from "../components/OtpInput";
import AuthLayout from "../components/AuthLayout";
import { Eye, EyeOff } from "lucide-react";

const RESEND_COOLDOWN_SECONDS = 60;

type Stage = "email" | "otp" | "password" | "done";

const inputClass =
  "w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-all";

const buttonClass =
  "w-full py-2.5 rounded-xl bg-primary text-white text-sm font-bold shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all disabled:opacity-60 cursor-pointer";

const STAGE_COPY: Record<Stage, { title: string; subtitle: string }> = {
  email: { title: "Quên mật khẩu", subtitle: "Nhập email đã đăng ký, chúng tôi sẽ gửi mã xác thực gồm 6 chữ số tới đó." },
  otp: { title: "Nhập mã xác thực", subtitle: "Mã gồm 6 chữ số vừa được gửi tới email của bạn. Mã có hiệu lực trong 10 phút." },
  password: { title: "Đặt mật khẩu mới", subtitle: "Mã xác thực hợp lệ. Nhập mật khẩu mới cho tài khoản của bạn." },
  done: { title: "Hoàn tất", subtitle: "Đặt lại mật khẩu thành công." },
};

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [stage, setStage] = useState<Stage>("email");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  const cooldownTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (cooldownTimer.current) clearInterval(cooldownTimer.current);
    };
  }, []);

  function startCooldown() {
    setCooldown(RESEND_COOLDOWN_SECONDS);
    if (cooldownTimer.current) clearInterval(cooldownTimer.current);
    cooldownTimer.current = setInterval(() => {
      setCooldown((s) => {
        if (s <= 1 && cooldownTimer.current) {
          clearInterval(cooldownTimer.current);
        }
        return s - 1;
      });
    }, 1000);
  }

  async function sendOtp() {
    setError(null);
    setSubmitting(true);
    try {
      await authApi.forgotPassword(email);
      setOtp("");
      setStage("otp");
      startCooldown();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Không thể gửi yêu cầu, vui lòng thử lại.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEmailSubmit(event: FormEvent) {
    event.preventDefault();
    await sendOtp();
  }

  async function handleResend() {
    if (cooldown > 0 || submitting) return;
    await sendOtp();
  }

  async function handleOtpSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (otp.length !== 6) {
      setError("Vui lòng nhập đủ 6 chữ số của mã xác thực.");
      return;
    }

    setSubmitting(true);
    try {
      await authApi.verifyResetOtp(email, otp);
      setStage("password");
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Không thể xác thực mã, vui lòng thử lại.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handlePasswordSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Mật khẩu xác nhận không khớp.");
      return;
    }

    setSubmitting(true);
    try {
      await authApi.resetPassword(email, otp, password);
      setStage("done");
    } catch (err) {
      // Nhiều khả năng nhất khiến bước cuối này thất bại là mã OTP đã hết hạn trong lúc
      // người dùng nhập mật khẩu mới (mã hợp lệ trong 10 phút, đã được xác thực đúng ở bước
      // trước). Quay lại bước nhập mã để họ có ngay lựa chọn "Gửi lại mã", thay vì kẹt ở màn
      // hình mật khẩu không có lối thoát nào khác ngoài rời khỏi luồng quên mật khẩu.
      setOtp("");
      setStage("otp");
      setError(err instanceof ApiClientError ? err.message : "Không thể đặt lại mật khẩu, vui lòng thử lại.");
    } finally {
      setSubmitting(false);
    }
  }

  const { title, subtitle } = STAGE_COPY[stage];

  return (
    <AuthLayout title={title} subtitle={subtitle}>
      {error && (
        <div className="mb-4 px-4 py-2.5 rounded-xl bg-red-50 border border-red-100 text-red-600 text-xs font-semibold">
          {error}
        </div>
      )}

      {stage === "email" && (
        <form onSubmit={handleEmailSubmit} className="space-y-4">
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
          <button type="submit" disabled={submitting} className={buttonClass}>
            {submitting ? "Đang gửi…" : "Gửi mã xác thực"}
          </button>
        </form>
      )}

      {stage === "otp" && (
        <form onSubmit={handleOtpSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-600">
              Mã xác thực gửi tới <span className="text-primary">{email}</span>
            </label>
            <OtpInput value={otp} onChange={setOtp} disabled={submitting} autoFocus />
          </div>

          <div className="flex items-center justify-between text-xs font-semibold">
            <button type="button" onClick={() => setStage("email")} className="text-slate-500 hover:text-primary cursor-pointer">
              Đổi email
            </button>
            <button
              type="button"
              onClick={handleResend}
              disabled={cooldown > 0 || submitting}
              className="text-primary hover:underline disabled:opacity-50 disabled:no-underline cursor-pointer"
            >
              {cooldown > 0 ? `Gửi lại mã (${cooldown}s)` : "Gửi lại mã"}
            </button>
          </div>

          <button type="submit" disabled={submitting || otp.length !== 6} className={buttonClass}>
            {submitting ? "Đang xác thực…" : "Xác thực mã"}
          </button>
        </form>
      )}

      {stage === "password" && (
        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="password" className="text-xs font-bold text-slate-600">
              Mật khẩu mới
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                className={`${inputClass} pr-10`}
                required
                minLength={6}
                autoComplete="new-password"
                autoFocus
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Tối thiểu 6 ký tự"
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
          <div className="space-y-1.5">
            <label htmlFor="confirm-password" className="text-xs font-bold text-slate-600">
              Xác nhận mật khẩu mới
            </label>
            <div className="relative">
              <input
                id="confirm-password"
                type={showConfirmPassword ? "text" : "password"}
                className={`${inputClass} pr-10`}
                required
                minLength={6}
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Nhập lại mật khẩu mới"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors p-1 cursor-pointer"
                tabIndex={-1}
                aria-label={showConfirmPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
              >
                {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
          <button type="submit" disabled={submitting} className={buttonClass}>
            {submitting ? "Đang lưu…" : "Đặt lại mật khẩu"}
          </button>
        </form>
      )}

      {stage === "done" && (
        <div className="space-y-4">
          <p className="text-sm text-slate-600">Bạn có thể đăng nhập với mật khẩu mới ngay bây giờ.</p>
          <button onClick={() => navigate("/login", { replace: true })} className={buttonClass}>
            Về trang đăng nhập
          </button>
        </div>
      )}

      {stage !== "done" && (
        <div className="mt-4 text-center text-xs text-slate-500">
          Nhớ ra mật khẩu rồi?{" "}
          <button onClick={() => navigate("/login")} className="font-bold text-primary hover:underline cursor-pointer">
            Quay lại đăng nhập
          </button>
        </div>
      )}
    </AuthLayout>
  );
}
