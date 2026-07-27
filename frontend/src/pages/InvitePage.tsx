import { useEffect, useState, type ReactNode } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Heart, ShieldCheck, Eye, UserCog } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { apiFetch, parseErrorMessage } from "../lib/authClient";
import AuthLayout from "../components/AuthLayout";

interface InvitationPublicInfo {
  baby_name: string;
  baby_avatar_url: string | null;
  guardian_name: string;
  invited_email: string;
  role: "ADMIN" | "GUARDIAN" | "VIEWER";
  status: "pending" | "accepted" | "declined" | "expired";
}

const ROLE_LABELS: Record<InvitationPublicInfo["role"], { label: string; icon: ReactNode }> = {
  ADMIN: { label: "Đồng quản trị (Toàn quyền quản lý)", icon: <UserCog className="w-4 h-4" /> },
  GUARDIAN: { label: "Người chăm sóc (Được chỉnh sửa nhật ký)", icon: <ShieldCheck className="w-4 h-4" /> },
  VIEWER: { label: "Người xem (Chỉ xem dữ liệu)", icon: <Eye className="w-4 h-4" /> },
};

export default function InvitePage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { isAuthenticated, email } = useAuth();

  const [info, setInfo] = useState<InvitationPublicInfo | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const [actionState, setActionState] = useState<"idle" | "accepting" | "declining" | "accepted" | "declined">("idle");
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`/api/v1/guardians/invite/${token}`);
        if (!res.ok) throw new Error(await parseErrorMessage(res));
        const data: InvitationPublicInfo = await res.json();
        if (!cancelled) setInfo(data);
      } catch (err) {
        if (!cancelled) setLoadError(err instanceof Error ? err.message : "Không tải được lời mời.");
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function handleAccept() {
    if (!isAuthenticated) {
      const params = new URLSearchParams({
        redirect: `/invite/${token}`,
        email: info.invited_email,
      });
      navigate(`/login?${params.toString()}`);
      return;
    }
    setActionError(null);
    setActionState("accepting");
    try {
      const res = await apiFetch(`/api/v1/guardians/invite/${token}/accept`, { method: "POST" });
      if (!res.ok) throw new Error(await parseErrorMessage(res));
      setActionState("accepted");
      setTimeout(() => navigate("/", { replace: true }), 1500);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Chấp nhận lời mời thất bại, vui lòng thử lại.");
      setActionState("idle");
    }
  }

  async function handleDecline() {
    setActionError(null);
    setActionState("declining");
    try {
      const res = await fetch(`/api/v1/guardians/invite/${token}/decline`, { method: "POST" });
      if (!res.ok) throw new Error(await parseErrorMessage(res));
      setActionState("declined");
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Từ chối lời mời thất bại, vui lòng thử lại.");
      setActionState("idle");
    }
  }

  if (isLoading) {
    return (
      <AuthLayout title="Lời mời tham gia chăm sóc bé" subtitle="Đang tải thông tin lời mời...">
        <div className="text-sm text-slate-400 text-center py-6">Đang tải...</div>
      </AuthLayout>
    );
  }

  if (loadError || !info) {
    return (
      <AuthLayout title="Lời mời không hợp lệ" subtitle="Không thể tải thông tin lời mời này.">
        <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm font-semibold">
          {loadError || "Lời mời không tồn tại hoặc đã bị thu hồi."}
        </div>
      </AuthLayout>
    );
  }

  if (actionState === "accepted" || info.status === "accepted") {
    return (
      <AuthLayout title="Đã chấp nhận lời mời" subtitle={`Bạn đã chính thức tham gia chăm sóc ${info.baby_name}.`}>
        <div className="px-4 py-3 rounded-xl bg-emerald-50 border border-emerald-100 text-emerald-700 text-sm font-semibold">
          Đang chuyển tới trang hồ sơ của bé...
        </div>
      </AuthLayout>
    );
  }

  if (actionState === "declined" || info.status === "declined") {
    return (
      <AuthLayout title="Đã từ chối lời mời" subtitle="Cảm ơn bạn đã phản hồi.">
        <div className="px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-600 text-sm font-semibold">
          Bạn đã từ chối lời mời tham gia chăm sóc {info.baby_name}. Người đã mời bạn sẽ được thông báo.
        </div>
      </AuthLayout>
    );
  }

  if (info.status === "expired") {
    return (
      <AuthLayout title="Lời mời đã hết hạn" subtitle="Vui lòng liên hệ người đã mời bạn để gửi lại lời mời mới.">
        <div className="px-4 py-3 rounded-xl bg-amber-50 border border-amber-100 text-amber-700 text-sm font-semibold">
          Lời mời tham gia chăm sóc {info.baby_name} đã hết hạn.
        </div>
      </AuthLayout>
    );
  }

  const roleInfo = ROLE_LABELS[info.role];
  const emailMismatch = isAuthenticated && email && email.toLowerCase() !== info.invited_email.toLowerCase();

  return (
    <AuthLayout title="Lời mời tham gia chăm sóc bé" subtitle="Xem chi tiết và phản hồi lời mời bên dưới.">
      <div className="space-y-4">
        <div className="flex items-center gap-3 p-4 bg-primary/5 border border-primary/10 rounded-2xl">
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
            <Heart className="w-5 h-5 text-primary" />
          </div>
          <div>
            <p className="text-sm font-bold text-slate-800">{info.baby_name}</p>
            <p className="text-xs text-slate-500">Bạn được mời: <span className="font-semibold">{info.guardian_name}</span></p>
          </div>
        </div>

        <div className="flex items-center gap-2 px-4 py-3 bg-white border border-slate-200 rounded-2xl text-sm text-slate-700">
          {roleInfo.icon}
          <span className="font-semibold">{roleInfo.label}</span>
        </div>

        <p className="text-xs text-slate-500">
          Email được mời: <span className="font-semibold">{info.invited_email}</span>
        </p>

        {emailMismatch && (
          <div className="px-4 py-3 rounded-xl bg-amber-50 border border-amber-100 text-amber-700 text-xs font-semibold">
            Bạn đang đăng nhập bằng email khác ({email}). Vui lòng đăng nhập đúng tài khoản có email {info.invited_email} để chấp nhận lời mời.
          </div>
        )}

        {actionError && (
          <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-xs font-semibold">
            {actionError}
          </div>
        )}

        <div className="flex flex-col gap-2 pt-2">
          <button
            onClick={handleAccept}
            disabled={actionState === "accepting" || actionState === "declining" || Boolean(emailMismatch)}
            className="w-full py-2.5 rounded-xl bg-primary text-white text-sm font-bold shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all disabled:opacity-60 cursor-pointer"
          >
            {actionState === "accepting"
              ? "Đang xử lý..."
              : isAuthenticated
              ? "Chấp nhận lời mời"
              : "Đăng nhập / Đăng ký để chấp nhận"}
          </button>
          <button
            onClick={handleDecline}
            disabled={actionState === "accepting" || actionState === "declining"}
            className="w-full py-2.5 rounded-xl bg-white border border-slate-200 text-slate-600 text-sm font-bold hover:bg-slate-50 transition-all disabled:opacity-60 cursor-pointer"
          >
            {actionState === "declining" ? "Đang xử lý..." : "Từ chối"}
          </button>
        </div>
      </div>
    </AuthLayout>
  );
}
