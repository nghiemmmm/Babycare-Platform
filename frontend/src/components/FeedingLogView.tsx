import React, { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  FileDown,
  Plus,
  Clock,
  Apple,
  Droplet,
  X,
  Search,
  Filter,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  PieChart as PieChartIcon
} from "lucide-react";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";
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

  // Date Filter state for Timeline & Stats: "today", "yesterday", "7days", "all"
  const [dateFilter, setDateFilter] = useState<"today" | "yesterday" | "7days" | "all">("today");

  // Ingredient Search & Reaction Filter states
  const [ingSearchQuery, setIngSearchQuery] = useState("");
  const [ingReactionFilter, setIngReactionFilter] = useState<"all" | "Loved it" | "Neutral" | "Spat out" | "Allergic Reaction">("all");

  const getCurrentTimeStr = () => {
    const now = new Date();
    return `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
  };

  const todayDateStr = new Date().toISOString().split("T")[0];

  React.useEffect(() => {
    setFeedTime(getCurrentTimeStr());
  }, []);

  const getAgeInMonths = (birthDateStr: string): number => {
    const birth = new Date(birthDateStr);
    const now = new Date();
    return (now.getFullYear() - birth.getFullYear()) * 12 + (now.getMonth() - birth.getMonth());
  };

  const ageInMonths = getAgeInMonths(activeBaby.birthDate);
  const isInfant = ageInMonths < 24;

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

  const FEED_INTERVAL_MINUTES = 180;

  // Filter feeds based on selected date filter
  const isMatchingDate = (fDate: string) => {
    if (dateFilter === "today") return fDate === todayDateStr || fDate === "Today";
    if (dateFilter === "yesterday") return fDate === "Yesterday";
    if (dateFilter === "7days") return fDate === todayDateStr || fDate === "Today" || fDate === "Yesterday" || fDate === "7 Days Ago";
    return true;
  };

  const filteredFeeds = feeds.filter((f) => f.babyId === activeBaby.id && isMatchingDate(f.date));

  // Compute stats
  const totalMilk = filteredFeeds
    .filter((f) => f.type !== "Solids")
    .reduce((acc, f) => acc + f.amount, 0);

  const solidsCount = filteredFeeds.filter((f) => f.type === "Solids").length;

  const breastMl = filteredFeeds.filter((f) => f.type === "Breast").reduce((acc, f) => acc + f.amount, 0);
  const formulaMl = filteredFeeds.filter((f) => f.type === "Formula").reduce((acc, f) => acc + f.amount, 0);

  // Nutritional Adequacy & Macronutrient Ratio Estimation (Chuẩn WHO/RDA)
  const hasFeeds = filteredFeeds.length > 0;
  const proteinPct = hasFeeds ? Math.min(100, Math.max(5, Math.round(((totalMilk * 0.015) + (solidsCount * 4)) / 18 * 100))) : 0;
  const fatPct = hasFeeds ? Math.min(100, Math.max(5, Math.round(((totalMilk * 0.035) + (solidsCount * 3)) / 25 * 100))) : 0;
  const carbsPct = hasFeeds ? Math.min(100, Math.max(5, Math.round(((totalMilk * 0.07) + (solidsCount * 15)) / 80 * 100))) : 0;
  const fiberPct = hasFeeds ? Math.min(100, Math.max(5, Math.round((solidsCount * 3.5) / 5 * 100))) : 0;

  const isNutritionalBalanced = hasFeeds && proteinPct >= 75 && fatPct >= 75 && carbsPct >= 75;

  // Pie chart dataset for ratio breakdown
  const pieData = [
    ...(breastMl > 0 ? [{ name: "Sữa mẹ", value: breastMl, color: "#38bdf8" }] : []),
    ...(formulaMl > 0 ? [{ name: "Sữa công thức", value: formulaMl, color: "#1c648e" }] : []),
    ...(solidsCount > 0 ? [{ name: "Ăn dặm (ml quy đổi)", value: solidsCount * 120, color: "#f59e0b" }] : [])
  ];

  const todaysMilkFeeds = filteredFeeds
    .filter((f) => f.type !== "Solids")
    .map((f) => ({ ...f, minutes: parseTimeToMinutes(f.time) }))
    .filter((f): f is typeof f & { minutes: number } => f.minutes !== null)
    .sort((a, b) => b.minutes - a.minutes);

  const lastMilkFeed = todaysMilkFeeds[0] || null;
  const nowMinutes = (() => {
    const now = new Date();
    return now.getHours() * 60 + now.getMinutes();
  })();

  let nextFeedLabel = "Chưa có dữ liệu";
  let nextFeedSubLabel = "Chưa ghi nhận cữ bú nào";
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

  // Filter ingredients
  const filteredIngredients = ingredients
    .filter((i) => i.babyId === activeBaby.id)
    .filter((i) => !ingSearchQuery.trim() || i.name.toLowerCase().includes(ingSearchQuery.toLowerCase()))
    .filter((i) => ingReactionFilter === "all" || i.reaction === ingReactionFilter);

  return (
    <div className="space-y-6 relative min-h-screen pb-20" id="feeding-log-view">

      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">Nhật ký ăn uống</h1>
          <span className="px-2.5 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-100 rounded-full text-xs font-bold">
            Đồng bộ gia đình
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Date Filter Buttons */}
          <div className="flex bg-white/60 backdrop-blur-md p-1 rounded-2xl border border-white/40 shadow-2xs">
            {[
              { id: "today", label: "Hôm nay" },
              { id: "yesterday", label: "Hôm qua" },
              { id: "7days", label: "7 ngày qua" },
              { id: "all", label: "Tất cả" }
            ].map((btn) => (
              <button
                key={btn.id}
                type="button"
                onClick={() => setDateFilter(btn.id as any)}
                className={`px-3 py-1 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  dateFilter === btn.id
                    ? "bg-[#1c648e] text-white shadow-2xs"
                    : "text-slate-500 hover:text-slate-800 hover:bg-white/50"
                }`}
              >
                {btn.label}
              </button>
            ))}
          </div>

          <button
            type="button"
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
            Xuất nhật ký
          </button>

          <button
            type="button"
            onClick={() => setShowAddFeedModal(true)}
            className="inline-flex items-center gap-1.5 bg-primary hover:bg-primary/95 text-white px-3.5 py-2 rounded-xl text-xs font-bold transition-all shadow-md cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            Ghi chép mới
          </button>
        </div>
      </div>

      {/* 🥣 AI WEANING TRANSITION EVALUATION BANNER */}
      {ageInMonths >= 5 && ageInMonths <= 12 && (
        <div className="bg-amber-50/90 border border-amber-200/80 p-4.5 rounded-3xl space-y-3 shadow-2xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="p-2 bg-amber-100 rounded-xl text-amber-800 text-xs font-bold">🥣 AI Y Khoa</span>
              <h4 className="text-xs font-black text-amber-950">AI đánh giá sẵn sàng chuyển sang ăn dặm</h4>
            </div>
            <span className="text-[10px] font-extrabold bg-amber-200/70 text-amber-900 px-2.5 py-0.5 rounded-full">
              Khuyến cáo Y tế WHO ({ageInMonths} Tháng)
            </span>
          </div>

          <p className="text-xs text-amber-900 font-medium leading-relaxed">
            Bé <span className="font-bold">{activeBaby.name}</span> đã <strong>{ageInMonths} tháng tuổi</strong>. 
            AI Đánh Giá Dinh Dưỡng: Bé đã <strong>đủ mốc sinh học sẵn sàng tập ăn dặm</strong> (Cổ vững, biết há miệng khi thấy thìa, phản xạ đẩy lưỡi giảm dần). Khuyên dùng bắt đầu với <em>Cháo rây 1:10</em> và <em>Củ quả nghiền dịu nhẹ</em>.
          </p>

          <div className="flex items-center gap-2.5 pt-1">
            <button
              type="button"
              onClick={() => {
                setFeedType("Solids");
                setFeedDetails("Cháo rây 1:10 & Bí đỏ nghiền");
                setShowAddFeedModal(true);
              }}
              className="bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold px-4 py-2 rounded-xl transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
            >
              ✨ AI gợi ý thực đơn & ghi nhận ăn dặm
            </button>
          </div>
        </div>
      )}

      {/* 🥩 NUTRITIONAL ADEQUACY & MACRONUTRIENT BALANCE CARD */}
      <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-500" />
              Đánh giá tỷ lệ chất dinh dưỡng (Chuẩn WHO/RDA)
            </h3>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              Mức độ đáp ứng nhu cầu năng lượng và vi chất cho bé {activeBaby.name} ({ageInMonths} tháng tuổi)
            </p>
          </div>

          <div className="self-start sm:self-auto">
            {!hasFeeds ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 border border-slate-200 text-slate-600 rounded-full text-xs font-bold">
                🌱 Chưa có nhật ký dinh dưỡng
              </span>
            ) : isNutritionalBalanced ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-full text-xs font-bold">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                🟢 Đạt Cân Bằng Dinh Dưỡng Chuẩn WHO
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-50 border border-amber-200 text-amber-800 rounded-full text-xs font-bold">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                💡 Gợi ý bổ sung thêm Chất Xơ / Rau củ
              </span>
            )}
          </div>
        </div>

        {/* 4 Macronutrients Adequacy Progress Bars Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-1">
          {/* 1. Protein */}
          <div className="p-3.5 bg-rose-50/50 border border-rose-100/80 rounded-2xl space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-rose-950">
              <span className="flex items-center gap-1.5">🥩 Chất Đạm (Protein)</span>
              <span className="text-rose-700 font-black">{proteinPct}%</span>
            </div>
            <div className="w-full bg-rose-100/60 h-2 rounded-full overflow-hidden">
              <div className="bg-rose-500 h-full rounded-full transition-all duration-500" style={{ width: `${proteinPct}%` }} />
            </div>
            <p className="text-[11px] text-rose-800/80 font-medium">Từ sữa, thịt/cá nghiền & lòng đỏ trứng</p>
          </div>

          {/* 2. Healthy Fats */}
          <div className="p-3.5 bg-amber-50/50 border border-amber-100/80 rounded-2xl space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-amber-950">
              <span className="flex items-center gap-1.5">🥑 Chất Béo (Fat/Lipid)</span>
              <span className="text-amber-700 font-black">{fatPct}%</span>
            </div>
            <div className="w-full bg-amber-100/60 h-2 rounded-full overflow-hidden">
              <div className="bg-amber-500 h-full rounded-full transition-all duration-500" style={{ width: `${fatPct}%` }} />
            </div>
            <p className="text-[11px] text-amber-800/80 font-medium">Từ sữa mẹ, sữa CT & dầu bơ dầm</p>
          </div>

          {/* 3. Carbohydrates */}
          <div className="p-3.5 bg-sky-50/50 border border-sky-100/80 rounded-2xl space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-sky-950">
              <span className="flex items-center gap-1.5">🌾 Tinh Bột (Carbs)</span>
              <span className="text-sky-700 font-black">{carbsPct}%</span>
            </div>
            <div className="w-full bg-sky-100/60 h-2 rounded-full overflow-hidden">
              <div className="bg-sky-500 h-full rounded-full transition-all duration-500" style={{ width: `${carbsPct}%` }} />
            </div>
            <p className="text-[11px] text-sky-800/80 font-medium">Từ cháo rây 1:10, yến mạch & khoai lang</p>
          </div>

          {/* 4. Fiber & Micronutrients */}
          <div className="p-3.5 bg-emerald-50/50 border border-emerald-100/80 rounded-2xl space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-emerald-950">
              <span className="flex items-center gap-1.5">🥦 Chất Xơ & Vitamin</span>
              <span className="text-emerald-700 font-black">{fiberPct}%</span>
            </div>
            <div className="w-full bg-emerald-100/60 h-2 rounded-full overflow-hidden">
              <div className="bg-emerald-500 h-full rounded-full transition-all duration-500" style={{ width: `${fiberPct}%` }} />
            </div>
            <p className="text-[11px] text-emerald-800/80 font-medium">Từ bí đỏ, súp lơ & trái cây dầm</p>
          </div>
        </div>
      </div>

      {/* Feeding Log Summary Cards & Recharts Pie Chart Grid */}
      <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-6">
        <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
          Tổng quan Dinh dưỡng ({dateFilter === "today" ? "Hôm nay" : dateFilter === "yesterday" ? "Hôm qua" : dateFilter === "7days" ? "7 ngày qua" : "Tất cả"})
        </h3>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left 2 Cols: Stat Cards */}
          <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Milk Intake Card */}
            {isInfant && (
              <div className="bg-white/40 border border-white/20 rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-bold">Lượng sữa dùng</span>
                  <Droplet className="w-4.5 h-4.5 text-sky-500" />
                </div>
                <div>
                  <h4 className="text-xl sm:text-2xl font-black text-slate-900">{totalMilk} / 800 ml</h4>
                  <p className="text-[11px] text-slate-500 font-medium mt-0.5">Mục tiêu: 800ml mỗi ngày</p>
                </div>
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
                <span className="text-xs text-slate-500 font-bold">
                  {isInfant ? "Cữ ăn dặm" : "Bữa ăn hôm nay"}
                </span>
                <Apple className="w-4.5 h-4.5 text-amber-500" />
              </div>
              <div>
                <h4 className="text-xl sm:text-2xl font-black text-slate-900">{solidsCount} / 3 Bữa</h4>
                <p className="text-[11px] text-slate-500 font-medium mt-0.5">
                  {isInfant ? "Mục tiêu: 3 bữa nhẹ" : "Mục tiêu: 3 bữa chính"}
                </p>
              </div>
              <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-amber-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min((solidsCount / 3) * 100, 100)}%` }}
                />
              </div>
            </div>

            {/* Next Feed Card */}
            {isInfant && (
              <div className="bg-white/40 border border-white/20 rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-bold">Cữ bú tiếp theo</span>
                  <Clock className="w-4.5 h-4.5 text-primary animate-pulse" />
                </div>
                <div>
                  <h4 className="text-xl sm:text-2xl font-black text-slate-900">{nextFeedLabel}</h4>
                  <p className="text-[11px] text-slate-500 font-medium mt-0.5">{nextFeedSubLabel}</p>
                </div>
                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-primary h-full rounded-full transition-all duration-500"
                    style={{ width: `${nextFeedProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Right Col: Recharts Pie Chart Ratio */}
          <div className="bg-white/40 border border-white/20 rounded-2xl p-4 flex flex-col items-center justify-center space-y-2">
            <div className="flex items-center gap-1.5 self-start">
              <PieChartIcon className="w-4 h-4 text-[#1c648e]" />
              <span className="text-xs text-slate-500 font-bold">Tỷ lệ nguồn dinh dưỡng</span>
            </div>

            {pieData.length > 0 ? (
              <>
                <div className="w-full h-[120px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={30}
                        outerRadius={50}
                        paddingAngle={3}
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(val: any) => [`${val} ml`, "Lượng nạp"]}
                        contentStyle={{ borderRadius: "10px", fontSize: "10px", fontWeight: "bold" }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="flex items-center justify-center gap-3 text-[11px] font-bold text-slate-600 flex-wrap">
                  {pieData.map((d) => (
                    <div key={d.name} className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: d.color }} />
                      <span>{d.name}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="w-full h-[120px] flex items-center justify-center text-slate-400 text-xs font-medium text-center px-4">
                Chưa có dữ liệu cữ ăn trong mốc thời gian này
              </div>
            )}
          </div>

        </div>
      </div>

      {/* Timeline Stream */}
      <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-white/20 pb-3">
          <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
            Dòng thời gian dinh dưỡng ({dateFilter === "today" ? "Hôm nay" : dateFilter === "yesterday" ? "Hôm qua" : dateFilter === "7days" ? "7 ngày qua" : "Tất cả"})
          </h3>
          <span className="text-xs font-bold text-slate-400">
            Hiển thị <span className="text-[#1c648e] font-black">{filteredFeeds.length}</span> cữ ăn/bú
          </span>
        </div>

        <div className="relative pl-6 border-l border-slate-100 space-y-5">
          {filteredFeeds
            .slice()
            .sort((a, b) => (parseTimeToMinutes(b.time) ?? 0) - (parseTimeToMinutes(a.time) ?? 0))
            .map((feed) => (
              <div key={feed.id} className="relative group flex items-start justify-between gap-4">
                <span className="absolute -left-[30.5px] top-1 w-2.5 h-2.5 rounded-full ring-4 bg-primary ring-primary/10" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400 font-bold">{feed.time}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                      feed.type === "Solids" ? "bg-amber-50 text-amber-700 border border-amber-100" : "bg-sky-50 text-sky-700 border border-sky-100"
                    }`}>
                      {feed.type === "Solids" ? "Ăn dặm" : feed.type === "Formula" ? "Sữa công thức" : "Sữa mẹ"}
                    </span>
                    <span className="text-[10px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                      {feed.date === "Today" || feed.date === todayDateStr ? "Hôm nay" : feed.date === "Yesterday" ? "Hôm qua" : feed.date}
                    </span>
                  </div>
                  <h4 className="text-xs sm:text-sm font-bold text-slate-800 mt-1">
                    {feed.type === "Solids" ? feed.details : `${feed.amount}ml ${feed.type === "Formula" ? "Sữa công thức" : "Sữa mẹ"}`}
                  </h4>
                </div>

                <button
                  type="button"
                  onClick={() => onDeleteFeed(feed.id)}
                  className="text-[10px] font-bold text-slate-400 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-all cursor-pointer"
                >
                  Xóa
                </button>
              </div>
            ))}

          {filteredFeeds.length === 0 && (
            <div className="text-center py-6 text-slate-400 text-xs font-medium">
              Không có nhật ký bú/ăn dặm nào trong mốc thời gian này.
            </div>
          )}
        </div>
      </div>

      {/* New Ingredients Tracker with Search & Filter */}
      <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/20 pb-3">
          <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
            Nguyên liệu mới & phản ứng của bé
          </h3>

          <div className="flex flex-wrap items-center gap-2">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2" />
              <input
                type="text"
                value={ingSearchQuery}
                onChange={(e) => setIngSearchQuery(e.target.value)}
                placeholder="Tìm tên thực phẩm..."
                className="pl-8 pr-3 py-1 bg-white/70 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-hidden focus:border-primary/40"
              />
            </div>

            {/* Reaction Filter Tabs */}
            <div className="flex bg-slate-100/80 p-0.5 rounded-xl border border-slate-200/60 text-[10px]">
              {[
                { id: "all", label: "Tất cả" },
                { id: "Loved it", label: "🥰 Thích" },
                { id: "Spat out", label: "😮‍💨 Nhổ ra" },
                { id: "Allergic Reaction", label: "⚠️ Dị ứng" }
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setIngReactionFilter(tab.id as any)}
                  className={`px-2 py-0.5 font-bold rounded-lg transition-all cursor-pointer ${
                    ingReactionFilter === tab.id
                      ? "bg-white text-[#1c648e] shadow-2xs"
                      : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <button
              type="button"
              onClick={() => setShowAddIngredientModal(true)}
              className="text-[10px] font-extrabold bg-primary hover:bg-primary/90 text-white px-3 py-1.5 rounded-xl transition-all cursor-pointer shadow-2xs"
            >
              + Theo dõi mới
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {filteredIngredients.map((ing) => {
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
                className="p-3 bg-white/40 border border-white/20 rounded-2xl flex items-center justify-between gap-3 shadow-2xs hover:bg-white/80 transition-all"
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
                    type="button"
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

          {filteredIngredients.length === 0 && (
            <div className="col-span-2 text-center py-6 text-slate-400 text-xs">
              Không tìm thấy báo cáo phản ứng dị ứng nào phù hợp.
            </div>
          )}
        </div>
      </div>

      {/* Floating Action Button (FAB) at Bottom Right */}
      <button
        type="button"
        onClick={() => setShowAddFeedModal(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-primary hover:bg-primary/90 text-white rounded-full flex items-center justify-center shadow-lg shadow-primary/20 hover:scale-105 transition-all cursor-pointer z-40"
        title="Thêm cữ bú mới"
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
                <h3 className="text-sm font-black text-slate-800 flex items-center gap-1.5">
                  🍼 Ghi nhận cữ ăn/uống
                </h3>
                <button
                  type="button"
                  onClick={() => setShowAddFeedModal(false)}
                  className="text-xs font-bold text-[#1c648e] bg-sky-50 hover:bg-sky-100 px-2.5 py-1 rounded-lg cursor-pointer"
                >
                  ✕ Đóng
                </button>
              </div>

              <form onSubmit={handleFeedSubmit} className="space-y-4 text-xs font-bold text-slate-600">
                <div className="space-y-1">
                  <label className="block">Loại thức ăn/uống</label>
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

                {feedType !== "Solids" ? (
                  <div className="space-y-2">
                    <label className="block">Lượng dùng (ml)</label>
                    <input
                      type="number"
                      value={feedAmount}
                      onChange={(e) => setFeedAmount(parseInt(e.target.value) || 0)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/40 focus:outline-hidden"
                    />
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {[60, 90, 120, 150, 180, 210].map((ml) => (
                        <button
                          key={ml}
                          type="button"
                          onClick={() => setFeedAmount(ml)}
                          className={`px-2.5 py-1 rounded-lg border text-[11px] font-bold transition-all cursor-pointer ${
                            feedAmount === ml ? "bg-primary text-white border-primary" : "bg-sky-50/70 border-sky-100 text-[#1c648e] hover:bg-sky-100"
                          }`}
                        >
                          {ml}ml
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <label className="block">Chi tiết món ăn dặm</label>
                    <input
                      type="text"
                      value={feedDetails}
                      onChange={(e) => setFeedDetails(e.target.value)}
                      placeholder="Ví dụ: Cháo rây 1:10, Bí đỏ nghiền"
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/40 focus:outline-hidden"
                    />
                    <div className="space-y-1 pt-1">
                      <span className="text-[10px] font-bold text-slate-400 block uppercase">Gợi ý món dặm chuẩn WHO:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {[
                          "🥣 Cháo rây 1:10",
                          "🎃 Bí đỏ nghiền",
                          "🥔 Khoai lang nghiền",
                          "🥑 Bơ dầm sữa",
                          "🥩 Cháo lợn băm rau ngót",
                          "🐟 Cháo cá hồi bí đỏ",
                          "🥦 Súp lơ hấp",
                          "🌾 Yến mạch táo"
                        ].map((preset) => (
                          <button
                            key={preset}
                            type="button"
                            onClick={() => setFeedDetails(preset)}
                            className="px-2 py-1 rounded-lg border border-amber-200 bg-amber-50 text-amber-900 text-[10px] font-bold hover:bg-amber-100 transition-all cursor-pointer"
                          >
                            {preset}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                <div className="space-y-1">
                  <label className="block">Thời gian</label>
                  <input
                    type="time"
                    value={feedTime}
                    onChange={(e) => setFeedTime(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/40 focus:outline-hidden"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-white py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer"
                >
                  Lưu nhật ký
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
                <h3 className="text-sm font-black text-slate-800 flex items-center gap-1.5">
                  🧪 Theo dõi nguyên liệu & dị ứng
                </h3>
                <button
                  type="button"
                  onClick={() => setShowAddIngredientModal(false)}
                  className="text-xs font-bold text-[#1c648e] bg-sky-50 hover:bg-sky-100 px-2.5 py-1 rounded-lg cursor-pointer"
                >
                  ✕ Đóng
                </button>
              </div>

              <form onSubmit={handleIngredientSubmit} className="space-y-4 text-xs font-bold text-slate-600">
                <div className="space-y-1">
                  <label className="block">Tên thực phẩm / nguyên liệu</label>
                  <input
                    type="text"
                    required
                    value={ingName}
                    onChange={(e) => setIngName(e.target.value)}
                    placeholder="Ví dụ: Tôm, Cua, Đậu nành, Lòng đỏ trứng"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/40 focus:outline-hidden"
                  />
                  <div className="flex flex-wrap gap-1 pt-1">
                    {["Tôm", "Cua", "Lòng đỏ trứng", "Đậu nành", "Kiwi", "Sữa bò"].map((preset) => (
                      <button
                        key={preset}
                        type="button"
                        onClick={() => setIngName(preset)}
                        className="px-2 py-0.5 rounded-md border border-slate-200 bg-slate-50 text-slate-700 text-[10px] font-semibold hover:bg-slate-100"
                      >
                        {preset}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="block">Phản ứng sinh học của bé</label>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { id: "Loved it", label: "🥰 Thích ăn" },
                      { id: "Neutral", label: "😐 Bình thường" },
                      { id: "Spat out", label: "😮‍💨 Nhổ ra" },
                      { id: "Allergic Reaction", label: "⚠️ Dị ứng/Mẩn đỏ" }
                    ].map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => setIngReaction(item.id as any)}
                        className={`p-2 rounded-xl border text-center text-xs transition-all cursor-pointer ${
                          ingReaction === item.id
                            ? item.id === "Allergic Reaction" ? "bg-rose-500 border-rose-500 text-white" : "bg-primary border-primary text-white"
                            : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100"
                        }`}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-white py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer"
                >
                  Lưu phản ứng
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
