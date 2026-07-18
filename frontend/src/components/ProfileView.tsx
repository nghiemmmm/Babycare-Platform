import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  UserPlus,
  Mail,
  Shield,
  Trash2,
  Camera,
  Check,
  RefreshCw,
  Heart,
  Calendar,
  Briefcase,
  AlertTriangle,
  Users,
  Clock,
  Plus,
  Edit3,
  CheckCircle,
  Eye,
  MessageSquare
} from "lucide-react";
import { BabyProfile, Gender, Guardian } from "../types";

interface ProfileViewProps {
  babies: BabyProfile[];
  guardians: Guardian[];
  onSelectBaby: (id: string) => void;
  onUpdateBaby: (baby: BabyProfile) => void;
  onAddBaby: (baby: Omit<BabyProfile, "id">) => void;
  onAddGuardian: (g: Omit<Guardian, "id">) => void;
  onDeleteGuardian: (id: string) => void;
}

export default function ProfileView({
  babies,
  guardians,
  onSelectBaby,
  onUpdateBaby,
  onAddBaby,
  onAddGuardian,
  onDeleteGuardian,
}: ProfileViewProps) {
  const activeBaby = babies.find((b) => b.isActive) || babies[0];

  // UI state toggles: viewing dashboard, editing existing, or creating new
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);

  // Form states for baby profile
  const [babyName, setBabyName] = useState(activeBaby.name);
  const [birthDate, setBirthDate] = useState(activeBaby.birthDate);
  const [gender, setGender] = useState<Gender>(activeBaby.gender);
  const [avatarUrl, setAvatarUrl] = useState(activeBaby.avatarUrl || "");

  // Invite Guardian form states
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [inviteRole, setInviteRole] = useState<"ADMIN" | "GUARDIAN" | "VIEWER">("GUARDIAN");
  const [showInviteSuccess, setShowInviteSuccess] = useState(false);

  // Sync input fields whenever activeBaby changes, but only if not currently creating
  React.useEffect(() => {
    if (!isCreating) {
      setBabyName(activeBaby.name);
      setBirthDate(activeBaby.birthDate);
      setGender(activeBaby.gender);
      setAvatarUrl(activeBaby.avatarUrl || "");
    }
  }, [activeBaby, isCreating]);

  const handleSaveBaby = (e: React.FormEvent) => {
    e.preventDefault();
    if (isCreating) {
      // Adding a brand new profile
      onAddBaby({
        name: babyName || "Newborn Baby",
        birthDate: birthDate || new Date().toISOString().split("T")[0],
        gender: gender,
        avatarUrl: avatarUrl || "/static/img/leo.png",
        isActive: true
      });
      setIsCreating(false);
      setIsEditing(false);
    } else {
      // Updating existing profile
      onUpdateBaby({
        ...activeBaby,
        name: babyName,
        birthDate,
        gender,
        avatarUrl
      });
      setIsEditing(false);
    }
  };

  const handleStartCreation = () => {
    // Open blank form inputs for new baby creation
    setBabyName("");
    setBirthDate(new Date().toISOString().split("T")[0]);
    setGender(Gender.Unknown);
    setAvatarUrl("");
    setIsCreating(true);
    setIsEditing(false);
  };

  const handleInviteGuardian = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail || !inviteName) return;

    onAddGuardian({
      name: inviteName,
      email: inviteEmail,
      role: inviteRole,
      status: "Invited"
    });

    setInviteEmail("");
    setInviteName("");
    setShowInviteModal(false);
    setShowInviteSuccess(true);
    setTimeout(() => setShowInviteSuccess(false), 3000);
  };

  // Helper: calculate age strings in months and days
  const calculateAgeDetails = (birthDateStr: string) => {
    const birth = new Date(birthDateStr);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - birth.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    const years = Math.floor(diffDays / 365);
    const remainingDays = diffDays % 365;
    const months = Math.floor(remainingDays / 30.4);
    const days = Math.floor(remainingDays % 30.4);

    if (years > 0) {
      return `${years} tuổi, ${months} tháng tuổi`;
    }
    return `${months} tháng, ${days} ngày tuổi`;
  };

  return (
    <div className="space-y-6" id="profile-view">
      
      {/* Horizontal Baby Profile Tabs */}
      <div className="flex flex-wrap items-center justify-between border-b border-white/20 pb-4">
        <div className="flex flex-wrap items-center gap-2">
          {babies.map((baby) => (
            <button
              key={baby.id}
              onClick={() => {
                onSelectBaby(baby.id);
                setIsEditing(false);
                setIsCreating(false);
              }}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                baby.isActive && !isCreating
                  ? "bg-primary text-white shadow-xs"
                  : "bg-white/60 text-slate-500 border border-white/20 hover:bg-white/80"
              }`}
            >
              {baby.name} {baby.isActive && !isCreating && "• Đang chọn"}
            </button>
          ))}
          
          <button
            onClick={handleStartCreation}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer ${
              isCreating
                ? "bg-primary text-white border-primary"
                : "border-dashed border-slate-300 text-slate-500 hover:text-slate-800"
            }`}
          >
            <UserPlus className="w-3.5 h-3.5" />
            Thêm bé mới
          </button>
        </div>

        {/* Global edit toggle button */}
        {!isCreating && (
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="inline-flex items-center gap-1.5 bg-white/60 hover:bg-white/80 border border-white/30 px-3.5 py-1.5 rounded-xl text-xs font-bold text-slate-600 transition-all cursor-pointer"
          >
            <Edit3 className="w-3.5 h-3.5 text-primary" />
            {isEditing ? "Xem Hồ sơ" : "Sửa thông tin"}
          </button>
        )}
      </div>

      <AnimatePresence mode="wait">
        
        {/* VIEW 1: Profile demographic dashboard mode */}
        {!isEditing && !isCreating ? (
          <motion.div
            key="dashboard-view"
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            className="grid grid-cols-1 lg:grid-cols-12 gap-8"
          >
            
            {/* Left side: Main Profile Panel & Activity Stream (Cột 7/12) */}
            <div className="lg:col-span-7 space-y-6">
              
              {/* Main Profile Panel */}
              <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-6">
                <div className="flex flex-col sm:flex-row items-center gap-6">
                  {/* Avatar circular frame with soft double border */}
                  <div className="w-24 h-24 rounded-full p-1 border-2 border-white/40 ring-4 ring-primary/10 overflow-hidden shrink-0">
                    <img
                      src={activeBaby.avatarUrl || "/static/img/leo.png"}
                      alt={activeBaby.name}
                      className="w-full h-full rounded-full object-cover"
                    />
                  </div>

                  <div className="text-center sm:text-left space-y-2">
                    <div>
                      <h2 className="text-primary font-bold text-2xl tracking-tight">{activeBaby.name}</h2>
                      <p className="text-xs font-bold text-slate-400 mt-0.5">
                        {calculateAgeDetails(activeBaby.birthDate)}
                      </p>
                    </div>

                    {/* Status badges */}
                    <div className="flex flex-wrap items-center justify-center sm:justify-start gap-1.5">
                      <span className="px-3 py-1 bg-sky-100 text-sky-700 rounded-full text-[10px] font-bold">
                        Nhóm máu A+
                      </span>
                      <span className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-[10px] font-bold">
                        Khỏe mạnh
                      </span>
                      <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-[10px] font-bold">
                        {activeBaby.gender === "Boy" ? "Bé trai" : activeBaby.gender === "Girl" ? "Bé gái" : "Chưa xác định"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Info details sub-grid */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white/40 border border-white/20 rounded-2xl p-4 flex items-center gap-3">
                    <div className="p-2.5 bg-sky-50 rounded-xl text-sky-500">
                      <Calendar className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Ngày sinh</span>
                      <span className="text-xs font-bold text-slate-700">{activeBaby.birthDate}</span>
                    </div>
                  </div>

                  <div className="bg-white/40 border border-white/20 rounded-2xl p-4 flex items-center gap-3">
                    <div className="p-2.5 bg-emerald-50 rounded-xl text-emerald-500">
                      <Briefcase className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Bác sĩ nhi khoa</span>
                      <span className="text-xs font-bold text-slate-700">Dr. Aris</span>
                    </div>
                  </div>
                </div>

                {/* Allergies and medical history block */}
                <div className="p-4 bg-red-50/50 border border-red-100 rounded-2xl space-y-2">
                  <span className="text-[10px] font-bold text-red-800 uppercase tracking-wider flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Dị ứng & Cảnh báo Y khoa
                  </span>
                  <div className="flex flex-wrap gap-2">
                    <span className="px-3 py-1 bg-red-100 border border-red-200 text-red-700 font-bold rounded-full text-[10px] cursor-default">
                      🥛 Nhạy cảm sữa bò
                    </span>
                    <span className="px-3 py-1 bg-orange-100 border border-orange-200 text-orange-700 font-bold rounded-full text-[10px] cursor-default">
                      🥜 Đề phòng Đậu phộng
                    </span>
                  </div>
                </div>
              </div>

              {/* Real-time Activity stream */}
              <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-white/20 pb-2">
                  <h3 className="text-primary font-bold text-sm tracking-tight flex items-center gap-1.5">
                    <Clock className="w-4.5 h-4.5 text-slate-400" />
                    Dòng hoạt động thời gian thực
                  </h3>
                  <a href="#activity-log" className="text-[10px] font-bold text-primary hover:underline">
                    Xem lịch sử
                  </a>
                </div>

                <div className="space-y-3">
                  {[
                    { user: "Mẹ Elena", action: "đã ghi nhận cữ sữa công thức 180ml", time: "5 phút trước", color: "bg-sky-50 text-sky-500" },
                    { user: "Bố David", action: "đã bắt đầu tính giờ ngủ", time: "20 phút trước", color: "bg-purple-50 text-purple-500" },
                    { user: "Bảo mẫu Maria", action: "đã ghi nhận giọt Vitamin D3", time: "1 giờ trước", color: "bg-emerald-50 text-emerald-500" }
                  ].map((act, idx) => (
                    <div key={idx} className="p-3 bg-white/40 border border-white/20 rounded-2xl flex items-center justify-between gap-3 text-xs">
                       <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${act.color}`}>
                          {act.user.charAt(0)}
                        </div>
                        <div>
                          <p className="font-semibold text-slate-700">
                            <span className="font-bold text-slate-800">{act.user}</span> {act.action}
                          </p>
                        </div>
                      </div>
                      <span className="text-[9px] font-bold text-slate-400">{act.time}</span>
                    </div>
                  ))}
                </div>
              </div>

            </div>

            {/* Right side: Caregivers family circle panel (Cột 5/12) */}
            <div className="lg:col-span-5 space-y-6">
              
              {/* Caregivers panel */}
              <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-white/20 pb-2">
                  <h3 className="text-primary font-bold text-sm tracking-tight flex items-center gap-1.5">
                    <Users className="w-4.5 h-4.5 text-primary" />
                    Vòng kết nối người chăm sóc
                  </h3>
                  <span className="px-2 py-0.5 bg-emerald-50 text-emerald-600 rounded-md text-[9px] font-bold animate-pulse">
                    Đang đồng bộ
                  </span>
                </div>

                {/* Caregivers list */}
                <div className="space-y-3">
                  {guardians.map((g) => (
                    <div
                      key={g.id}
                      className="p-3 bg-white/40 border border-white/20 rounded-2xl flex items-center justify-between gap-3 hover:bg-white/70 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="relative">
                          <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-xs font-bold text-slate-600">
                            {g.name.charAt(0)}
                          </div>
                          {g.status === "Synced" && (
                            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-500 rounded-full border border-white" />
                          )}
                        </div>
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs font-bold text-slate-700">{g.name}</span>
                            {g.role === "ADMIN" && (
                              <span className="px-1.5 py-0.2 bg-emerald-50 text-emerald-600 font-bold text-[8px] rounded uppercase">
                                Admin
                              </span>
                            )}
                          </div>
                          <p className="text-[10px] text-slate-400">{g.email}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-1.5">
                        {g.status !== "Synced" && (
                          <button className="text-[9px] font-bold text-primary hover:underline">
                            Gửi lại
                          </button>
                        )}
                        {g.role !== "ADMIN" && (
                          <button
                            onClick={() => onDeleteGuardian(g.id)}
                            className="p-1 text-slate-400 hover:text-rose-500 rounded-lg hover:bg-rose-50 cursor-pointer"
                            title="Xóa"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Invite Member outline button */}
                <button
                  onClick={() => setShowInviteModal(true)}
                  className="w-full inline-flex items-center justify-center gap-1.5 border border-dashed border-slate-300 hover:border-primary text-slate-500 hover:text-primary text-xs font-bold py-2.5 rounded-2xl transition-colors cursor-pointer"
                >
                  <Plus className="w-4 h-4" />
                  Mời thành viên gia đình
                </button>

                {/* Family status widget */}
                <div className="p-3.5 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border border-emerald-500/10 rounded-2xl flex items-center gap-3">
                  <Heart className="w-5 h-5 text-emerald-600 shrink-0 animate-pulse" />
                  <div>
                    <p className="text-xs font-bold text-emerald-800">Đã đồng bộ tất cả!</p>
                    <p className="text-[10px] text-emerald-600 font-semibold">
                      Vòng kết nối gia đình của bạn đang hoạt động đồng bộ tức thì.
                    </p>
                  </div>
                </div>
              </div>

            </div>

          </motion.div>
        ) : (
          
          // VIEW 2: Edit or Create Baby Profile view
          <motion.div
            key="edit-view"
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 max-w-2xl mx-auto space-y-6"
          >
            <h3 className="text-primary font-bold text-sm uppercase tracking-wide text-slate-500">
              {isCreating ? "Đăng ký hồ sơ em bé mới" : `Chỉnh sửa hồ sơ của ${activeBaby.name}`}
            </h3>

            <form onSubmit={handleSaveBaby} className="space-y-6 text-xs font-bold text-slate-600">
              
              {/* Photo Input link */}
              <div className="flex items-center gap-4">
                <div className="relative group cursor-pointer shrink-0">
                  <img
                    src={avatarUrl || "/static/img/leo.png"}
                    alt={babyName || "Preview"}
                    className="w-20 h-20 rounded-full object-cover border-2 border-white/40 shadow-sm"
                  />
                  <div className="absolute inset-0 bg-slate-900/30 rounded-full flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-all">
                    <Camera className="w-5 h-5" />
                  </div>
                </div>
                <div className="space-y-1.5 flex-1">
                  <h4 className="font-bold text-slate-700">Đường dẫn ảnh đại diện</h4>
                  <input
                    type="text"
                    value={avatarUrl}
                    onChange={(e) => setAvatarUrl(e.target.value)}
                    placeholder="Dán đường dẫn ảnh trực tiếp..."
                    className="w-full font-medium bg-slate-50 border border-slate-200 focus:border-primary/40 focus:outline-hidden rounded-xl px-3 py-2 text-slate-700"
                  />
                </div>
              </div>

              {/* Form Input fields */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block">Tên em bé</label>
                  <input
                    type="text"
                    required
                    value={babyName}
                    onChange={(e) => setBabyName(e.target.value)}
                    placeholder="Ví dụ: Liam James"
                    className="w-full bg-slate-50 border border-slate-200 focus:border-primary/40 focus:bg-white focus:outline-hidden rounded-xl px-3.5 py-2 text-sm text-slate-800 font-medium"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block">Ngày sinh</label>
                  <input
                    type="date"
                    required
                    value={birthDate}
                    onChange={(e) => setBirthDate(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 focus:border-primary/40 focus:bg-white focus:outline-hidden rounded-xl px-3.5 py-2 text-sm text-slate-800 font-medium"
                  />
                </div>
              </div>

              {/* Gender selector */}
              <div className="space-y-1.5">
                <label className="block">Giới tính</label>
                <div className="flex gap-2">
                  {[Gender.Boy, Gender.Girl, Gender.Unknown].map((g) => {
                    const genderLabels: Record<string, string> = {
                      [Gender.Boy]: "Bé trai",
                      [Gender.Girl]: "Bé gái",
                      [Gender.Unknown]: "Chưa rõ"
                    };
                    return (
                      <button
                        key={g}
                        type="button"
                        onClick={() => setGender(g)}
                        className={`px-4 py-2 rounded-xl border transition-all cursor-pointer ${
                          gender === g
                            ? "bg-primary text-white border-primary shadow-xs"
                            : "bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-600"
                        }`}
                      >
                        {genderLabels[g]}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="pt-4 border-t border-white/20 flex items-center justify-between">
                <button
                  type="submit"
                  className="bg-primary hover:bg-primary/95 text-white px-5 py-2.5 rounded-full font-bold transition-all shadow-md shadow-primary/20 cursor-pointer"
                >
                  {isCreating ? "Tạo Hồ sơ em bé" : "Lưu chi tiết hồ sơ"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsCreating(false);
                    setIsEditing(false);
                  }}
                  className="text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  Hủy
                </button>
              </div>

            </form>
          </motion.div>
        )}

      </AnimatePresence>

      {/* Invitation success toast notification */}
      <AnimatePresence>
        {showInviteSuccess && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-6 right-6 bg-emerald-600 text-white rounded-2xl px-4 py-3 shadow-lg flex items-center gap-2 z-50 text-xs font-bold"
          >
            <CheckCircle className="w-4 h-4" />
            Đã gửi lời mời thành công tới thành viên gia đình!
          </motion.div>
        )}
      </AnimatePresence>

      {/* Invite Caregiver Modal overlay */}
      <AnimatePresence>
        {showInviteModal && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-black text-slate-800">Mời người chăm sóc</h3>
                <button
                  onClick={() => setShowInviteModal(false)}
                  className="text-xs font-bold text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  Hủy
                </button>
              </div>

              <form onSubmit={handleInviteGuardian} className="space-y-4 text-xs font-bold text-slate-600">
                <div className="space-y-1">
                  <label className="block">Tên người chăm sóc</label>
                  <input
                    type="text"
                    required
                    value={inviteName}
                    onChange={(e) => setInviteName(e.target.value)}
                    placeholder="Ví dụ: Bà nội Martha, Bảo mẫu..."
                    className="w-full bg-slate-50 border border-slate-200 focus:border-primary/45 rounded-xl px-3 py-2 font-medium"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block">Địa chỉ Email</label>
                  <input
                    type="email"
                    required
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="guardian@family.com"
                    className="w-full bg-slate-50 border border-slate-200 focus:border-primary/45 rounded-xl px-3 py-2 font-medium"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block">Vai trò kết nối</label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as any)}
                    className="w-full bg-slate-50 border border-slate-200 focus:border-primary/45 rounded-xl px-3 py-2 font-medium"
                  >
                    <option value="GUARDIAN">Người chăm sóc (Được chỉnh sửa nhật ký)</option>
                    <option value="ADMIN">Đồng quản trị (Toàn quyền quản lý)</option>
                    <option value="VIEWER">Người xem (Chỉ xem dữ liệu)</option>
                  </select>
                </div>

                <button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-white py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer"
                >
                  Gửi lời mời
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
