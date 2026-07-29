import React, { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { FileDown, Plus, Clock, Apple, Droplet, X } from "lucide-react";
import { BabyProfile, FeedLog, IngredientLog } from "../types";

interface FeedingLogViewProps {
  activeBaby: BabyProfile;
  feeds: FeedLog[];
  ingredients: IngredientLog[];
  onAddFeed: (f: Omit<FeedLog, "id">) => void;
  onDeleteFeed: (id: string) => void;
  onAddIngredient: (ing: Omit<IngredientLog, "id">) => void;
  onDeleteIngredient: (id: string) => void;
}

export default function FeedingLogView({
  activeBaby,
  feeds,
  ingredients,
  onAddFeed,
  onDeleteFeed,
  onAddIngredient,
  onDeleteIngredient
}: FeedingLogViewProps) {
  // Modal visibility states
  const [showAddFeedModal, setShowAddFeedModal] = useState(false);
  const [showAddIngredientModal, setShowAddIngredientModal] = useState(false);

  // Form states for Feed
  const [feedType, setFeedType] = useState<"Formula" | "Breast" | "Solids">("Formula");
  const [feedAmount, setFeedAmount] = useState(180);
  const [feedDetails, setFeedDetails] = useState("Formula Milk");
  const [feedTime, setFeedTime] = useState("");

  // Form states for Ingredient
  const [ingName, setIngName] = useState("");
  const [ingReaction, setIngReaction] = useState<"Loved it" | "Spat out" | "Neutral" | "Allergic Reaction">("Loved it");

  const getCurrentTimeStr = () => {
    const now = new Date();
    return `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
  };

  // So khớp với "date" backend lưu (UTC, xem router.py add_nutrition_feed) - dùng cùng quy ước
  // UTC ở đây để tránh entry ghi lúc gần nửa đêm bị lệch ngày so với backend.
  const todayDateStr = new Date().toISOString().split("T")[0];

  React.useEffect(() => {
    setFeedTime(getCurrentTimeStr());
  }, []);

  // Tuổi bé (tháng) - dùng để quyết định có còn hiển thị chỉ số "Lượng sữa"/"Cữ bú tiếp theo"
  // hay không. Sau ~2 tuổi, trẻ không còn ăn/bú theo lịch sữa cố định nữa nên các chỉ số này
  // không còn ý nghĩa và bị ẩn đi thay vì hiện những con số cố định không liên quan tới bé.
  const getAgeInMonths = (birthDateStr: string): number => {
    const birth = new Date(birthDateStr);
    const now = new Date();
    return (now.getFullYear() - birth.getFullYear()) * 12 + (now.getMonth() - birth.getMonth());
  };

  const ageInMonths = getAgeInMonths(activeBaby.birthDate);
  const isInfant = ageInMonths < 24;

  // Parse "H:MM AM/PM" -> số phút kể từ 00:00, và chiều ngược lại - dùng để tính cữ bú tiếp theo
  // thật từ giờ cữ bú gần nhất, thay vì hiển thị "02:30 PM" cố định như trước.
  const parseTimeToMinutes = (timeStr: string): number | null => {
    const match = timeStr.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
    if (!match) return null;
    let hours = parseInt(match[1], 10) % 12;
    if (match[3].toUpperCase() === "PM") hours += 12;
    return hours * 60 + parseInt(match[2], 10);
  };

  const formatMinutesToTime = (totalMinutes: number): string => {
    const wrapped = ((totalMinutes % 1440) + 1440) % 1440;
    const hours24 = Math.floor(wrapped / 60);
    const mins = wrapped % 60;
    const ampm = hours24 >= 12 ? "PM" : "AM";
    const displayHrs = hours24 % 12 || 12;
    return `${String(displayHrs).padStart(2, "0")}:${String(mins).padStart(2, "0")} ${ampm}`;
  };

  const FEED_INTERVAL_MINUTES = 180; // ước tính 3 giờ/cữ - khoảng cách phổ biến cho trẻ bú sữa

  // Compute stats
  const totalMilk = feeds
    .filter((f) => f.babyId === activeBaby.id && f.type !== "Solids" && f.date === todayDateStr)
    .reduce((acc, f) => acc + f.amount, 0);

  const solidsCount = feeds.filter((f) => f.babyId === activeBaby.id && f.type === "Solids" && f.date === todayDateStr).length;

  const todaysMilkFeeds = feeds
    .filter((f) => f.babyId === activeBaby.id && f.type !== "Solids" && f.date === todayDateStr)
    .map((f) => ({ ...f, minutes: parseTimeToMinutes(f.time) }))
    .filter((f): f is typeof f & { minutes: number } => f.minutes !== null)
    .sort((a, b) => b.minutes - a.minutes);

  const lastMilkFeed = todaysMilkFeeds[0] || null;
  const nowMinutes = (() => {
    const now = new Date();
    return now.getHours() * 60 + now.getMinutes();
  })();

  let nextFeedLabel = "Chưa có dữ liệu";
  let nextFeedSubLabel = "Chưa ghi nhận cữ bú nào hôm nay";
  let nextFeedProgress = 0;

  if (lastMilkFeed) {
    const nextFeedMinutes = lastMilkFeed.minutes + FEED_INTERVAL_MINUTES;
    const diff = nextFeedMinutes - nowMinutes;
    nextFeedLabel = formatMinutesToTime(nextFeedMinutes);
    if (diff <= 0) {
      nextFeedSubLabel = "Đã đến giờ bú tiếp theo";
      nextFeedProgress = 100;
    } else if (diff < 60) {
      nextFeedSubLabel = `Trong khoảng ${diff} phút nữa`;
      nextFeedProgress = Math.min(((FEED_INTERVAL_MINUTES - diff) / FEED_INTERVAL_MINUTES) * 100, 100);
    } else {
      const h = Math.floor(diff / 60);
      const m = diff % 60;
      nextFeedSubLabel = `Trong khoảng ${h} giờ${m > 0 ? ` ${m} phút` : ""} nữa`;
      nextFeedProgress = Math.min(((FEED_INTERVAL_MINUTES - diff) / FEED_INTERVAL_MINUTES) * 100, 100);
    }
  }

  const handleFeedSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Chặn giờ tương lai - thuộc tính "max" trên input chỉ giới hạn UI picker, không chặn
    // được việc gõ tay trực tiếp trên một số trình duyệt, nên phải validate lại ở đây.
    if (feedTime && feedTime > getCurrentTimeStr()) {
      alert("Không thể chọn giờ trong tương lai. Vui lòng chọn giờ hiện tại hoặc trong quá khứ.");
      return;
    }

    let details = feedDetails;
    if (feedType === "Formula" && !details) details = "Formula Milk";
    if (feedType === "Breast" && !details) details = "Breast Milk";

    let finalTime = "12:00 PM";
    if (feedTime) {
      const [hrs, mins] = feedTime.split(":");
      const hours = parseInt(hrs);
      const ampm = hours >= 12 ? "PM" : "AM";
      const displayHrs = hours % 12 || 12;
      finalTime = `${displayHrs}:${mins} ${ampm}`;
    }

    onAddFeed({
      babyId: activeBaby.id,
      type: feedType,
      details,
      amount: feedType === "Solids" ? 1 : Number(feedAmount),
      time: finalTime,
      date: "Today"
    });

    setShowAddFeedModal(false);
    setFeedDetails("");
  };

  const handleIngredientSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ingName) return;

    onAddIngredient({
      babyId: activeBaby.id,
      name: ingName,
      reaction: ingReaction,
      date: new Date().toISOString().split("T")[0]
    });

    setShowAddIngredientModal(false);
    setIngName("");
  };

  return (
    <div className="space-y-6 relative min-h-screen pb-20" id="feeding-log-view">

      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <h1 className="text-primary font-bold text-2xl tracking-tight">Nhật ký Ăn uống</h1>
          <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-100 rounded-full text-[9px] font-bold">
            Đồng bộ Gia đình Hoạt động
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              const csvContent = "data:text/csv;charset=utf-8,"
                + "Time,Type,Details,Amount/Meals\n"
                + feeds.map(f => `${f.time},${f.type},${f.details},${f.amount}`).join("\n");
              const encodedUri = encodeURI(csvContent);
              const link = document.createElement("a");
              link.setAttribute("href", encodedUri);
              link.setAttribute("download", `${activeBaby.name}_nutrition_report.csv`);
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
            }}
            className="inline-flex items-center gap-1.5 bg-white/60 border border-white/30 text-slate-700 hover:bg-white/80 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer"
          >
            <FileDown className="w-3.5 h-3.5" />
            Xuất Nhật ký
          </button>

          <button
            onClick={() => setShowAddFeedModal(true)}
            className="inline-flex items-center gap-1.5 bg-primary hover:bg-primary/95 text-white px-3.5 py-2 rounded-xl text-xs font-bold transition-all shadow-md cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            Ghi chép mới
          </button>
        </div>
      </div>

      {/* Feeding Log Summary Cards & Progress Bars */}
      <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-6">
        <h3 className="text-primary font-bold text-xs uppercase tracking-wider text-slate-500">
          Tổng quan Dinh dưỡng Hàng ngày
        </h3>

        <div className={`grid grid-cols-1 gap-4 ${isInfant ? "md:grid-cols-3" : ""}`}>
          {/* Milk Intake Card - chỉ hiện với bé dưới 2 tuổi, bé lớn hơn không còn bú sữa theo cữ */}
          {isInfant && (
            <div className="bg-white/40 border border-white/20 rounded-2xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-slate-500 font-bold uppercase">Lượng sữa dùng</span>
                <Droplet className="w-4.5 h-4.5 text-sky-500" />
              </div>
              <div>
                <h4 className="text-xl font-bold text-primary">{totalMilk} / 800 ml</h4>
                <p className="text-[9px] text-slate-400 font-semibold mt-0.5">Mục tiêu: 800ml mỗi ngày</p>
              </div>
              {/* Progress bar */}
              <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-sky-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min((totalMilk / 800) * 100, 100)}%` }}
                />
              </div>
            </div>
          )}

          {/* Solids Card */}
          <div className="bg-white/40 border border-white/20 rounded-2xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-slate-500 font-bold uppercase">
                {isInfant ? "Cữ ăn dặm" : "Bữa ăn hôm nay"}
              </span>
              <Apple className="w-4.5 h-4.5 text-amber-500" />
            </div>
            <div>
              <h4 className="text-xl font-bold text-primary">{solidsCount} / 3 Bữa</h4>
              <p className="text-[9px] text-slate-400 font-semibold mt-0.5">
                {isInfant ? "Mục tiêu: 3 bữa nhẹ" : "Mục tiêu: 3 bữa chính"}
              </p>
            </div>
            {/* Progress bar */}
            <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-amber-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min((solidsCount / 3) * 100, 100)}%` }}
              />
            </div>
          </div>

          {/* Next Feed Card - chỉ hiện với bé dưới 2 tuổi, tính thật từ giờ cữ bú gần nhất hôm nay */}
          {isInfant && (
            <div className="bg-white/40 border border-white/20 rounded-2xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-slate-500 font-bold uppercase">Cữ bú tiếp theo</span>
                <Clock className="w-4.5 h-4.5 text-primary animate-pulse" />
              </div>
              <div>
                <h4 className="text-xl font-bold text-primary">{nextFeedLabel}</h4>
                <p className="text-[9px] text-slate-400 font-semibold mt-0.5">{nextFeedSubLabel}</p>
              </div>
              {/* Alert/Status Progress indicator bar */}
              <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-primary h-full rounded-full transition-all duration-500"
                  style={{ width: `${nextFeedProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Today's Feeding Timeline */}
      <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
        <h3 className="text-primary font-bold text-xs uppercase tracking-wider text-slate-500">
          Dòng thời gian Dinh dưỡng Hôm nay
        </h3>

        <div className="relative pl-6 border-l border-slate-100 space-y-5">
          {feeds
            .filter((f) => f.babyId === activeBaby.id && f.date === todayDateStr)
            .slice()
            .sort((a, b) => (parseTimeToMinutes(b.time) ?? 0) - (parseTimeToMinutes(a.time) ?? 0))
            .map((feed) => (
              <div key={feed.id} className="relative group flex items-start justify-between gap-4">
                <span className="absolute -left-[30.5px] top-1 w-2.5 h-2.5 rounded-full ring-4 bg-primary ring-primary/10" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-400 font-bold">{feed.time}</span>
                    <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded uppercase ${
                      feed.type === "Solids" ? "bg-amber-50 text-amber-600 border border-amber-100" : "bg-sky-50 text-sky-600 border border-sky-100"
                    }`}>
                      {feed.type === "Solids" ? "Ăn dặm" : feed.type === "Formula" ? "Sữa công thức" : "Sữa mẹ"}
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-slate-700 mt-1">
                    {feed.type === "Solids" ? feed.details : `${feed.amount}ml ${feed.type === "Formula" ? "Sữa công thức" : "Sữa mẹ"}`}
                  </h4>
                </div>

                <button
                  onClick={() => onDeleteFeed(feed.id)}
                  className="text-[10px] font-bold text-slate-400 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-all cursor-pointer"
                >
                  Xóa
                </button>
              </div>
            ))}

          {feeds.filter((f) => f.babyId === activeBaby.id && f.date === todayDateStr).length === 0 && (
            <div className="text-center py-6 text-slate-400 text-xs font-semibold">
              Không có nhật ký bú/ăn dặm nào hôm nay.
            </div>
          )}
        </div>
      </div>

      {/* New Ingredients Tracker */}
      <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-white/20 pb-2">
          <h3 className="text-primary font-bold text-xs uppercase tracking-wider text-slate-500">
            Nguyên liệu mới & Phản ứng của bé
          </h3>
          <button
            onClick={() => setShowAddIngredientModal(true)}
            className="text-[10px] font-bold text-primary hover:underline cursor-pointer"
          >
            + Theo dõi phản ứng mới
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {ingredients
            .filter((i) => i.babyId === activeBaby.id)
            .map((ing) => {
              let statusStyle = "bg-emerald-50 text-emerald-700 border-emerald-100";
              if (ing.reaction === "Spat out") statusStyle = "bg-orange-50 text-orange-700 border-orange-100";
              if (ing.reaction === "Allergic Reaction") statusStyle = "bg-rose-50 text-rose-700 border-rose-100 animate-pulse font-extrabold";

              const reactionLabels: Record<string, string> = {
                "Loved it": "Thích",
                "Neutral": "Bình thường",
                "Spat out": "Nhổ ra",
                "Allergic Reaction": "Dị ứng"
              };

              return (
                <div
                  key={ing.id}
                  className="p-3 bg-white/40 border border-white/20 rounded-2xl flex items-center justify-between gap-3 shadow-xs hover:bg-white/80 transition-all"
                >
                  <div>
                    <h4 className="text-xs font-bold text-slate-700">{ing.name}</h4>
                    <span className="text-[9px] text-slate-400 font-semibold">{ing.date}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className={`px-2 py-0.5 rounded-full border text-[9px] font-bold ${statusStyle}`}>
                      {reactionLabels[ing.reaction] || ing.reaction}
                    </span>
                    <button
                      onClick={() => onDeleteIngredient(ing.id)}
                      className="text-slate-300 hover:text-rose-500 transition-colors cursor-pointer"
                      title="Xóa bản ghi phản ứng"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}

          {ingredients.filter((i) => i.babyId === activeBaby.id).length === 0 && (
            <div className="col-span-2 text-center py-6 text-slate-400 text-xs">
              Chưa có báo cáo phản ứng dị ứng nào.
            </div>
          )}
        </div>
      </div>

      {/* Floating Action Button (FAB) at Bottom Right */}
      <button
        onClick={() => setShowAddFeedModal(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-primary hover:bg-primary/90 text-white rounded-full flex items-center justify-center shadow-lg shadow-primary/20 hover:scale-105 transition-all cursor-pointer z-40"
        title="Add feed entry"
      >
        <Plus className="w-6 h-6" />
      </button>

      {/* --- ADD FEED MODAL --- */}
      <AnimatePresence>
        {showAddFeedModal && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-black text-slate-800">Thêm cữ ăn mới</h3>
                <button
                  onClick={() => setShowAddFeedModal(false)}
                  className="text-xs font-bold text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  Hủy
                </button>
              </div>

              <form onSubmit={handleFeedSubmit} className="space-y-4 text-xs font-bold text-slate-600">
                <div className="space-y-1">
                  <label className="block">Loại thức ăn</label>
                  <div className="grid grid-cols-3 gap-2">
                    {["Formula", "Breast", "Solids"].map((type) => {
                      const labels: Record<string, string> = {
                        Formula: "Sữa CT",
                        Breast: "Sữa mẹ",
                        Solids: "Ăn dặm"
                      };
                      return (
                        <button
                          key={type}
                          type="button"
                          onClick={() => setFeedType(type as any)}
                          className={`py-2 rounded-xl border text-center transition-all cursor-pointer ${
                            feedType === type
                              ? "bg-primary border-primary text-white"
                              : "bg-slate-50 border-slate-200 hover:bg-slate-100"
                          }`}
                        >
                          {labels[type]}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {feedType !== "Solids" ? (
                    <div className="space-y-1">
                      <label className="block">Thể tích (ml)</label>
                      <input
                        type="number"
                        required
                        value={feedAmount}
                        onChange={(e) => setFeedAmount(Number(e.target.value))}
                        className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/45 focus:outline-hidden font-medium"
                      />
                    </div>
                  ) : (
                    <div className="space-y-1">
                      <label className="block">Thực đơn ăn dặm</label>
                      <input
                        type="text"
                        required
                        value={feedDetails}
                        onChange={(e) => setFeedDetails(e.target.value)}
                        placeholder="Ví dụ: Súp bơ nghiền"
                        className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/45 focus:outline-hidden font-medium"
                      />
                    </div>
                  )}

                  <div className="space-y-1">
                    <label className="block">Thời gian dùng</label>
                    <input
                      type="time"
                      required
                      value={feedTime}
                      max={getCurrentTimeStr()}
                      onChange={(e) => setFeedTime(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/45 focus:outline-hidden font-medium"
                    />
                    <p className="text-[10px] text-slate-400 font-semibold normal-case">
                      Chỉ chọn được giờ hiện tại hoặc trong quá khứ của hôm nay.
                    </p>
                  </div>
                </div>

                <button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-white py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer"
                >
                  Lưu Nhật ký cữ bú/ăn dặm
                </button>
              </form>
            </motion.div>
          </div>
        )}

        {/* --- ADD INGREDIENT MODAL --- */}
        {showAddIngredientModal && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-black text-slate-800">Thêm phản ứng ăn dặm</h3>
                <button
                  onClick={() => setShowAddIngredientModal(false)}
                  className="text-xs font-bold text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  Hủy
                </button>
              </div>

              <form onSubmit={handleIngredientSubmit} className="space-y-4 text-xs font-bold text-slate-600">
                <div className="space-y-1">
                  <label className="block">Tên nguyên liệu</label>
                  <input
                    type="text"
                    required
                    value={ingName}
                    onChange={(e) => setIngName(e.target.value)}
                    placeholder="Ví dụ: Bơ, Đậu phộng nghiền"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 focus:border-primary/45 focus:outline-hidden font-medium"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block">Trạng thái phản ứng</label>
                  <select
                    value={ingReaction}
                    onChange={(e) => setIngReaction(e.target.value as any)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/45 focus:outline-hidden font-medium"
                  >
                    <option value="Loved it">😋 Thích</option>
                    <option value="Neutral">😐 Bình thường</option>
                    <option value="Spat out">🤢 Nhổ ra</option>
                    <option value="Allergic Reaction">🚨 Phản ứng dị ứng (Phát ban/Nôn mửa)</option>
                  </select>
                </div>

                <button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-white py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer"
                >
                  Lưu Nhật ký phản ứng
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
