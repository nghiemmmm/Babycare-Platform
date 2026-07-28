import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  FileDown,
  Plus,
  Compass,
  AlertTriangle,
  Check,
  X,
  Clock,
  Apple,
  Search,
  Book,
  Heart,
  Droplet,
  Info,
  Calendar,
  Sparkles,
  ArrowRight,
  Filter,
  Camera,
  ChevronDown,
  BookOpen
} from "lucide-react";
import { BabyProfile, FeedLog, IngredientLog } from "../types";

interface NutritionViewProps {
  activeBaby: BabyProfile;
  feeds: FeedLog[];
  ingredients: IngredientLog[];
  onAddFeed: (f: Omit<FeedLog, "id">) => void;
  onDeleteFeed: (id: string) => void;
  onAddIngredient: (ing: Omit<IngredientLog, "id">) => void;
  onDeleteIngredient: (id: string) => void;
}

interface FoodSafetyItem {
  name: string;
  reason: string;
  showInfo: boolean;
}

export default function NutritionView({
  activeBaby,
  feeds,
  ingredients,
  onAddFeed,
  onDeleteFeed,
  onAddIngredient,
  onDeleteIngredient
}: NutritionViewProps) {
  // Modal visibility states
  const [showAddFeedModal, setShowAddFeedModal] = useState(false);
  const [showAddIngredientModal, setShowAddIngredientModal] = useState(false);
  const [showSafetyModal, setShowSafetyModal] = useState(false);
  const [activeInfoAlert, setActiveInfoAlert] = useState<string | null>(null);

  // Form states for Feed
  const [feedType, setFeedType] = useState<"Formula" | "Breast" | "Solids">("Formula");
  const [feedAmount, setFeedAmount] = useState(180);
  const [feedDetails, setFeedDetails] = useState("Formula Milk");
  const [feedTime, setFeedTime] = useState("");

  // Form states for Ingredient
  const [ingName, setIngName] = useState("");
  const [ingReaction, setIngReaction] = useState<"Loved it" | "Spat out" | "Neutral" | "Allergic Reaction">("Loved it");

  // Foods to avoid list with local explanation toggle states
  const [foodsToAvoid, setFoodsToAvoid] = useState<FoodSafetyItem[]>([
    { name: "Mật ong", reason: "Nguy cơ ngộ độc clostridium botulinum ở trẻ dưới 12 tháng, một bệnh nhiễm độc đường tiêu hóa hiếm gặp nhưng rất nghiêm trọng.", showInfo: false },
    { name: "Muối gia vị", reason: "Thận của trẻ dưới 1 tuổi chưa đủ phát triển để lọc muối bổ sung.", showInfo: false },
    { name: "Đường gia vị", reason: "Có thể gây sâu răng, hình thành thói quen ăn ngọt có hại cho sức khỏe và thiếu giá trị dinh dưỡng.", showInfo: false }
  ]);

  const [allergenAlerts, setAllergenAlerts] = useState<{
    allergens: string[];
    warning_message: string;
    has_alert: boolean;
  }>({
    allergens: ["🥛 Nhạy cảm sữa bò", "🥜 Đề phòng Đậu phộng"],
    warning_message: `${activeBaby.name} chưa ghi nhận dị ứng nghiêm trọng. Cần cẩn trọng khi cho bé thử nhóm thực phẩm mới.`,
    has_alert: false
  });

  React.useEffect(() => {
    const fetchSafetyGuidelines = async () => {
      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || "";
        const token = localStorage.getItem("token") || "mock-token";
        const res = await fetch(`${baseUrl}/api/v1/nutrition/safety-guidelines?baby_id=${activeBaby.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data.foods_to_avoid) && data.foods_to_avoid.length > 0) {
            setFoodsToAvoid(data.foods_to_avoid.map((f: any) => ({
              name: f.name,
              reason: f.reason,
              showInfo: false
            })));
          }
          if (data.allergen_alerts) {
            setAllergenAlerts(data.allergen_alerts);
          }
        }
      } catch (err) {
        console.error("Error fetching safety guidelines:", err);
      }
    };
    fetchSafetyGuidelines();
  }, [activeBaby.id, ingredients]);

  React.useEffect(() => {
    const now = new Date();
    setFeedTime(`${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`);
  }, []);

  // Compute stats
  const totalMilk = feeds
    .filter((f) => f.babyId === activeBaby.id && f.type !== "Solids" && f.date === "Today")
    .reduce((acc, f) => acc + f.amount, 0);

  const solidsCount = feeds.filter((f) => f.babyId === activeBaby.id && f.type === "Solids" && f.date === "Today").length;

  const handleFeedSubmit = (e: React.FormEvent) => {
    e.preventDefault();

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

  const toggleAvoidInfo = (index: number) => {
    setFoodsToAvoid(prev =>
      prev.map((item, idx) => (idx === index ? { ...item, showInfo: !item.showInfo } : item))
    );
  };

  return (
    <div className="space-y-6 relative min-h-screen pb-20" id="nutrition-view">
      
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <h1 className="text-primary font-bold text-2xl tracking-tight">Dinh dưỡng & Ăn dặm</h1>
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

      {/* Main Grid Layout (65% / 35%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Cột Trái (65%): Theo dõi Dinh dưỡng & Nguyên liệu (7-8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* Feeding Log Summary Cards & Progress Bars */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-6">
            <h3 className="text-primary font-bold text-xs uppercase tracking-wider text-slate-500">
              Tổng quan Dinh dưỡng Hàng ngày
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Milk Intake Card */}
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

              {/* Solids Card */}
              <div className="bg-white/40 border border-white/20 rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-500 font-bold uppercase">Cữ ăn dặm</span>
                  <Apple className="w-4.5 h-4.5 text-amber-500" />
                </div>
                <div>
                  <h4 className="text-xl font-bold text-primary">{solidsCount} / 3 Bữa</h4>
                  <p className="text-[9px] text-slate-400 font-semibold mt-0.5">Mục tiêu: 3 bữa nhẹ</p>
                </div>
                {/* Progress bar */}
                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-amber-500 h-full rounded-full transition-all duration-500"
                    style={{ width: `${Math.min((solidsCount / 3) * 100, 100)}%` }}
                  />
                </div>
              </div>

              {/* Next Feed Card */}
              <div className="bg-white/40 border border-white/20 rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-500 font-bold uppercase">Cữ bú tiếp theo</span>
                  <Clock className="w-4.5 h-4.5 text-primary animate-pulse" />
                </div>
                <div>
                  <h4 className="text-xl font-bold text-primary">02:30 PM</h4>
                  <p className="text-[9px] text-slate-400 font-semibold mt-0.5">Trong khoảng 45 phút nữa</p>
                </div>
                {/* Alert/Status Progress indicator bar */}
                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-primary h-full rounded-full w-[70%]" />
                </div>
              </div>
            </div>
          </div>

          {/* Today's Feeding Timeline */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
            <h3 className="text-primary font-bold text-xs uppercase tracking-wider text-slate-500">
              Dòng thời gian Dinh dưỡng Hôm nay
            </h3>

            <div className="relative pl-6 border-l border-slate-100 space-y-5">
              {feeds
                .filter((f) => f.babyId === activeBaby.id && f.date === "Today")
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

              {feeds.filter((f) => f.babyId === activeBaby.id && f.date === "Today").length === 0 && (
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



        </div>

        {/* Cột Phải (35%): AI Insights & Cảnh báo (Allergen Safety) (4-5 cols) */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Allergen Safety Panel & Warnings */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
            <h3 className="text-primary font-bold text-xs uppercase tracking-wide text-slate-500">
              Kiểm tra dị ứng & an toàn
            </h3>

            {/* High Alert Box */}
            <div className={`p-4 rounded-r-2xl space-y-2 border-l-4 ${
              allergenAlerts.has_alert
                ? "bg-red-50 border-red-500 animate-pulse"
                : "bg-amber-50 border-amber-400"
            }`}>
              <span className="text-[10px] font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1">
                ⚠️ Dị ứng & Cảnh báo Y khoa
              </span>
              <div className="flex flex-wrap gap-1.5">
                {allergenAlerts.allergens.map((alg, aIdx) => (
                  <span
                    key={aIdx}
                    className={`px-2.5 py-0.5 border font-bold rounded-full text-[9px] ${
                      allergenAlerts.has_alert
                        ? "bg-red-100 border-red-200 text-red-700"
                        : "bg-amber-100 border-amber-200 text-amber-800"
                    }`}
                  >
                    ⚠️ {alg}
                  </span>
                ))}
              </div>
              <p className={`text-[11px] leading-relaxed font-semibold ${
                allergenAlerts.has_alert ? "text-red-700" : "text-amber-800"
              }`}>
                {allergenAlerts.warning_message}
              </p>
            </div>

            {/* Foods to Avoid (Until 1 year) */}
            <div className="space-y-2">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Thực phẩm cần tránh (Dưới 1 tuổi)
              </span>

              <div className="space-y-2">
                {foodsToAvoid.map((food, idx) => (
                  <div key={idx} className="bg-white/40 border border-white/20 rounded-xl p-2.5 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-700">{food.name}</span>
                      <button
                        onClick={() => toggleAvoidInfo(idx)}
                        className="text-slate-400 hover:text-slate-600 cursor-pointer"
                        title="Xem lý do"
                      >
                        <Info className="w-4 h-4 text-primary" />
                      </button>
                    </div>

                    <AnimatePresence>
                      {food.showInfo && (
                        <motion.p
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          className="text-[10px] text-slate-500 leading-relaxed font-semibold"
                        >
                          {food.reason}
                        </motion.p>
                      )}
                    </AnimatePresence>
                  </div>
                ))}
              </div>
            </div>

            {/* View Full Safety Guide Button */}
            <button
              onClick={() => setShowSafetyModal(true)}
              className="w-full inline-flex items-center justify-center gap-1.5 bg-blue-50 hover:bg-blue-100 border border-blue-100 text-blue-700 text-[10px] font-bold py-2 rounded-xl transition-all cursor-pointer"
            >
              <BookOpen className="w-4.5 h-4.5 text-blue-600" />
              Xem toàn bộ Hướng dẫn An toàn
            </button>
          </div>

          {/* AI Meal Plan Widget */}
          <div className="bg-[#ecfdf5]/80 backdrop-blur-xl border border-emerald-100/60 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-emerald-500/10">
              <h3 className="text-emerald-950 font-bold text-xs uppercase tracking-wide flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-emerald-600" />
                Thực đơn ăn dặm từ AI
              </h3>
              <span className="px-1.5 py-0.2 bg-emerald-100 text-emerald-700 font-bold text-[8px] rounded uppercase">
                Đang ăn dặm
              </span>
            </div>

            <div className="space-y-3">
              {[
                { name: "Súp bơ nghiền (Bơ)", desc: "Giàu chất béo không bão hòa tốt cho não bộ. Có thể trộn với sữa công thức để điều chỉnh độ đặc.", reaction: "Khuyên dùng cao" },
                { name: "Súp cải bó xôi (Cải bó xôi)", desc: "Nguồn cung cấp sắt và vitamin tuyệt vời. Hấp chín và xay mịn.", reaction: "Dùng vào tuần tới" }
              ].map((rec, rIdx) => (
                <div key={rIdx} className="bg-white/80 rounded-2xl p-3 space-y-1.5 border border-emerald-100/40">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800">{rec.name}</span>
                    <span className="text-[9px] bg-emerald-50 text-emerald-600 font-bold px-1.5 py-0.2 rounded-md">
                      {rec.reaction}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-500 font-semibold leading-relaxed">
                    {rec.desc}
                  </p>
                </div>
              ))}
            </div>

            <button className="w-full inline-flex items-center justify-center gap-1 text-[10px] font-bold text-emerald-700 hover:text-emerald-900 transition-colors mt-2 cursor-pointer">
              Xem thực đơn hàng tuần
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

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
                      onChange={(e) => setFeedTime(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/45 focus:outline-hidden font-medium"
                    />
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

        {/* --- FULL SAFETY GUIDE MODAL --- */}
        {showSafetyModal && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[85vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-blue-600" />
                  <h3 className="text-sm font-black text-slate-800">Cẩm nang An toàn Dinh dưỡng (WHO/AAP)</h3>
                </div>
                <button
                  onClick={() => setShowSafetyModal(false)}
                  className="text-xs font-bold text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-3 text-xs text-slate-600 leading-relaxed font-medium">
                <div className="p-3 bg-blue-50/70 border border-blue-100 rounded-2xl space-y-1">
                  <h4 className="font-bold text-blue-900 flex items-center gap-1">📌 Quy tắc 3 ngày thử món mới (Rule of 3)</h4>
                  <p>Khi cho bé thử nguyên liệu ăn dặm mới (ví dụ: bơ, trứng, cá), cho bé ăn liên tục 3 ngày để dễ dàng xác định chính xác thực phẩm gây dị ứng nếu có phản ứng.</p>
                </div>

                <div className="p-3 bg-red-50/70 border border-red-100 rounded-2xl space-y-1">
                  <h4 className="font-bold text-red-900 flex items-center gap-1">🚨 Dấu hiệu dị ứng cần đi cấp cứu ngay</h4>
                  <ul className="list-disc pl-4 space-y-0.5 text-red-800">
                    <li>Khó thở, thở khò khè hoặc sưng môi, lưỡi, mắt.</li>
                    <li>Nổi mẩn đỏ toàn thân, ngứa ngáy nhiều.</li>
                    <li>Nôn mửa nhiều lần hoặc tiêu chảy cấp.</li>
                  </ul>
                </div>

                <div className="p-3 bg-amber-50/70 border border-amber-100 rounded-2xl space-y-1">
                  <h4 className="font-bold text-amber-900 flex items-center gap-1">⚠️ Phòng ngừa hóc dị vật (Choking Hazards)</h4>
                  <p>Cắt đôi hoặc bổ 4 các loại quả tròn nhỏ (nho, cà chua bi, cherry). Tránh cho trẻ dưới 3 tuổi ăn hạt nguyên hạt, kẹo cứng, popcorn.</p>
                </div>

                <div className="p-3 bg-emerald-50/70 border border-emerald-100 rounded-2xl space-y-1">
                  <h4 className="font-bold text-emerald-900 flex items-center gap-1">🥛 An toàn hâm sữa & Bảo quản</h4>
                  <p>Sữa mẹ/Sữa công thức đã pha chỉ dùng trong 2 giờ ở nhiệt độ phòng. Hâm sữa bằng nước ấm dưới 40°C, không hâm bằng lò vi sóng.</p>
                </div>
              </div>

              <button
                onClick={() => setShowSafetyModal(false)}
                className="w-full bg-[#1c648e] hover:bg-[#154c6d] text-white py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer text-xs"
              >
                Đã hiểu hướng dẫn
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
