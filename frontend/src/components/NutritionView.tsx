import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Sparkles,
  Calendar,
  ShieldAlert,
  BookOpen,
  Plus,
  Trash2,
  Coffee,
  Check,
  RefreshCw,
  AlertTriangle,
  Info,
  Apple,
  Milk,
  Clock
} from "lucide-react";
import {
  BabyProfile,
  FeedLog,
  IngredientLog,
  NutritionRecommendation,
  WeeklyMealPlan,
  NutritionSafety,
  SafetyHandbook
} from "../types";

export interface NutritionViewProps {
  activeBaby: BabyProfile;
  feeds?: FeedLog[];
  ingredients?: IngredientLog[];
  onAddFeed?: (feed: Omit<FeedLog, "id">) => void;
  onDeleteFeed?: (id: string) => void;
  onAddIngredient?: (ingredient: Omit<IngredientLog, "id">) => void;
  onDeleteIngredient?: (id: string) => void;
  recommendation?: NutritionRecommendation | null;
  isGeneratingRecommendation?: boolean;
  onGenerateRecommendation?: () => void;
  weeklyMealPlan?: WeeklyMealPlan | null;
  isGeneratingWeeklyPlan?: boolean;
  isAcceptingWeeklyPlan?: boolean;
  onGenerateWeeklyMealPlan?: (feedback?: string) => void;
  onAcceptWeeklyMealPlan?: () => void;
  nutritionSafety?: NutritionSafety | null;
  safetyHandbook?: SafetyHandbook | null;
  isLoadingSafetyHandbook?: boolean;
  onOpenSafetyHandbook?: () => void;
}

const MEAL_TYPES = ["sáng", "trưa", "tối", "phụ"] as const;
const MEAL_TYPE_LABELS: Record<string, string> = {
  sáng: "Sáng 🌅",
  trưa: "Trưa ☀️",
  tối: "Tối 🌙",
  phụ: "Bữa phụ 🍎"
};

const HANDBOOK_LEVEL_STYLES: Record<string, string> = {
  info: "bg-indigo-50/70 border-indigo-100 text-indigo-900",
  danger: "bg-rose-50/70 border-rose-100 text-rose-900",
  warning: "bg-amber-50/70 border-amber-100 text-amber-900",
  success: "bg-emerald-50/70 border-emerald-100 text-emerald-900"
};

export default function NutritionView({
  activeBaby,
  feeds = [],
  ingredients = [],
  onAddFeed,
  onDeleteFeed,
  onAddIngredient,
  onDeleteIngredient,
  recommendation,
  isGeneratingRecommendation = false,
  onGenerateRecommendation,
  weeklyMealPlan,
  isGeneratingWeeklyPlan = false,
  isAcceptingWeeklyPlan = false,
  onGenerateWeeklyMealPlan,
  onAcceptWeeklyMealPlan,
  nutritionSafety,
  safetyHandbook,
  isLoadingSafetyHandbook = false,
  onOpenSafetyHandbook
}: NutritionViewProps) {
  const [activeTab, setActiveTab] = useState<"ai" | "tracking">("ai");

  // Modals for tracking
  const [showAddFeedModal, setShowAddFeedModal] = useState(false);
  const [showAddIngredientModal, setShowAddIngredientModal] = useState(false);

  // Feed Form
  const [feedType, setFeedType] = useState<"formula" | "breast">("formula");
  const [feedAmount, setFeedAmount] = useState<number>(150);
  const [feedNote, setFeedNote] = useState<string>("");

  // Ingredient Form
  const [ingredientName, setIngredientName] = useState<string>("");
  const [ingredientCategory, setIngredientCategory] = useState<string>("Rau củ");
  const [ingredientAmount, setIngredientAmount] = useState<number>(50);
  const [ingredientReaction, setIngredientReaction] = useState<"Loved it" | "Neutral" | "Spat out" | "Allergic Reaction">("Loved it");

  // Modals for AI
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [regenerateFeedback, setRegenerateFeedback] = useState("");
  const [showSafetyHandbookModal, setShowSafetyHandbookModal] = useState(false);

  const handleAddFeedSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onAddFeed) {
      onAddFeed({
        babyId: activeBaby.id,
        type: feedType,
        amountMl: feedAmount,
        loggedAt: new Date().toISOString(),
        note: feedNote || undefined
      });
    }
    setShowAddFeedModal(false);
    setFeedNote("");
  };

  const handleAddIngredientSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ingredientName.trim()) return;
    if (onAddIngredient) {
      onAddIngredient({
        babyId: activeBaby.id,
        name: ingredientName,
        category: ingredientCategory,
        amountG: ingredientAmount,
        reaction: ingredientReaction,
        loggedAt: new Date().toISOString()
      });
    }
    setShowAddIngredientModal(false);
    setIngredientName("");
  };

  const handleRegenerateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onGenerateWeeklyMealPlan) {
      onGenerateWeeklyMealPlan(regenerateFeedback.trim() || undefined);
    }
    setShowRegenerateModal(false);
    setRegenerateFeedback("");
  };

  const handleHandbookClick = () => {
    setShowSafetyHandbookModal(true);
    if (onOpenSafetyHandbook) {
      onOpenSafetyHandbook();
    }
  };

  const daysUntil = (endDateStr: string) => {
    const end = new Date(endDateStr).getTime();
    const now = new Date().getTime();
    return Math.ceil((end - now) / (1000 * 3600 * 24));
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* --- HEADER TITLE & TAB SWITCHER --- */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white/70 backdrop-blur-md p-6 rounded-3xl border border-slate-100 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2.5 rounded-2xl bg-amber-500/10 text-amber-600">
              <Apple className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-black text-slate-800 tracking-tight">
                Dinh Dưỡng & Ăn Dặm
              </h1>
              <p className="text-xs font-semibold text-slate-500">
                Thực đơn AI chuẩn WHO & Nhật ký ăn uống cho bé {activeBaby.name}
              </p>
            </div>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1.5 bg-slate-100/80 p-1.5 rounded-2xl border border-slate-200/50 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab("ai")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === "ai"
                ? "bg-white text-primary shadow-xs"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            AI Tư Vấn & Thực Đơn 7 Ngày
          </button>
          <button
            onClick={() => setActiveTab("tracking")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === "tracking"
                ? "bg-white text-primary shadow-xs"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            <Coffee className="w-3.5 h-3.5" />
            Nhật Ký Cữ Bú & Nguyên Liệu ({feeds.length + ingredients.length})
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: AI TƯ VẤN & THỰC ĐƠN 7 NGÀY */}
      {/* ========================================================================= */}
      {activeTab === "ai" && (
        <div className="space-y-6">
          {/* Quick Action Bar */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={onGenerateRecommendation}
              disabled={isGeneratingRecommendation}
              className="inline-flex items-center gap-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white text-xs font-bold px-4 py-2.5 rounded-2xl shadow-md transition-all cursor-pointer disabled:opacity-60"
            >
              <Sparkles className={`w-4 h-4 ${isGeneratingRecommendation ? "animate-spin" : ""}`} />
              {isGeneratingRecommendation ? "Đang tạo gợi ý AI…" : "✨ Tạo gợi ý dinh dưỡng AI"}
            </button>

            <button
              onClick={() => onGenerateWeeklyMealPlan && onGenerateWeeklyMealPlan()}
              disabled={isGeneratingWeeklyPlan}
              className="inline-flex items-center gap-2 bg-primary hover:bg-primary/95 text-white text-xs font-bold px-4 py-2.5 rounded-2xl shadow-md transition-all cursor-pointer disabled:opacity-60"
            >
              <Calendar className={`w-4 h-4 ${isGeneratingWeeklyPlan ? "animate-spin" : ""}`} />
              {isGeneratingWeeklyPlan ? "Đang tạo thực đơn 7 ngày…" : "📅 Tạo thực đơn 7 ngày AI"}
            </button>

            <button
              onClick={handleHandbookClick}
              className="inline-flex items-center gap-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold px-4 py-2.5 rounded-2xl shadow-xs transition-all cursor-pointer"
            >
              <BookOpen className="w-4 h-4 text-indigo-500" />
              📖 Cẩm nang an toàn dinh dưỡng
            </button>
          </div>

          {/* --- AI RECOMMENDATION CARD --- */}
          {recommendation && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gradient-to-br from-amber-50/80 via-orange-50/40 to-white border border-amber-100/80 rounded-3xl p-6 shadow-xs space-y-4"
            >
              <div className="flex items-center justify-between border-b border-amber-100/60 pb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-amber-500" />
                  <h2 className="text-sm font-black text-slate-800">
                    Khuyến Nghị Dinh Dưỡng AI Cho Bé {activeBaby.name}
                  </h2>
                </div>
                <span className="text-[10px] font-bold text-amber-700 bg-amber-100/80 px-2.5 py-1 rounded-full">
                  Cập nhật: {recommendation.generatedAt.substring(0, 10)}
                </span>
              </div>

              <p className="text-xs text-slate-600 font-medium leading-relaxed">
                {recommendation.summary}
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                {/* Món khuyến nghị */}
                <div className="bg-emerald-50/60 border border-emerald-100 rounded-2xl p-4 space-y-2">
                  <h3 className="text-xs font-bold text-emerald-800 flex items-center gap-1.5">
                    <Apple className="w-4 h-4 text-emerald-600" />
                    Món ăn khuyến nghị nên bổ sung
                  </h3>
                  <div className="space-y-2">
                    {recommendation.recommendedFoods.map((food, idx) => (
                      <div key={idx} className="bg-white/80 rounded-xl p-2.5 border border-emerald-100/60">
                        <p className="text-xs font-bold text-slate-800">{food.foodName}</p>
                        <p className="text-[11px] text-slate-500 font-medium">{food.reason}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Món cần tránh */}
                <div className="bg-rose-50/60 border border-rose-100 rounded-2xl p-4 space-y-2">
                  <h3 className="text-xs font-bold text-rose-800 flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                    Thực phẩm cần hạn chế / Tránh
                  </h3>
                  <div className="space-y-2">
                    {recommendation.foodsToAvoid.map((food, idx) => (
                      <div key={idx} className="bg-white/80 rounded-xl p-2.5 border border-rose-100/60">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold text-slate-800">{food.foodName}</p>
                          {food.linkedTo && (
                            <span className="text-[9px] font-bold bg-rose-100 text-rose-700 px-2 py-0.5 rounded-md">
                              {food.linkedTo}
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-500 font-medium">{food.reason}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* --- 7-DAY WEEKLY MEAL PLAN MATRIX --- */}
          {weeklyMealPlan && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white border border-slate-100 rounded-3xl p-6 shadow-xs space-y-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-primary" />
                  <h2 className="text-sm font-black text-slate-800">
                    Thực Đơn Ăn Dặm 7 Ngày ({weeklyMealPlan.startDate} ~ {weeklyMealPlan.endDate})
                  </h2>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] font-bold px-2.5 py-1 rounded-full ${
                      weeklyMealPlan.status === "accepted"
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-amber-100 text-amber-700"
                    }`}
                  >
                    {weeklyMealPlan.status === "accepted" ? "Đã áp dụng ✓" : "Đang chờ duyệt"}
                  </span>
                </div>
              </div>

              {/* Matrix Table */}
              <div className="overflow-x-auto">
                <div className="min-w-[640px] grid grid-cols-8 gap-2">
                  <div className="font-bold text-[10px] text-slate-400 uppercase self-center">
                    Bữa ăn
                  </div>
                  {weeklyMealPlan.days.map((day) => (
                    <div key={day.date} className="text-center font-bold text-[11px] text-slate-700 bg-slate-50 py-1.5 rounded-xl border border-slate-100">
                      {day.date.substring(5)}
                    </div>
                  ))}

                  {MEAL_TYPES.map((mealType) => (
                    <React.Fragment key={mealType}>
                      <div className="flex items-center text-[10px] font-bold text-slate-400 uppercase">
                        {MEAL_TYPE_LABELS[mealType]}
                      </div>
                      {weeklyMealPlan.days.map((day) => {
                        const meal = day.meals.find((m) => m.mealType.toLowerCase() === mealType);
                        return (
                          <div
                            key={`${day.date}-${mealType}`}
                            className="bg-slate-50/60 border border-slate-100 rounded-xl p-2 space-y-0.5 min-h-[56px]"
                          >
                            {meal ? (
                              <>
                                <p className="text-[10px] font-bold text-slate-700 leading-tight">
                                  {meal.foodName}
                                </p>
                                {meal.note && (
                                  <p className="text-[9px] text-slate-400 leading-tight">{meal.note}</p>
                                )}
                              </>
                            ) : (
                              <p className="text-[9px] text-slate-300">—</p>
                            )}
                          </div>
                        );
                      })}
                    </React.Fragment>
                  ))}
                </div>
              </div>

              {/* Action buttons for meal plan */}
              {weeklyMealPlan.status === "pending" && (
                <div className="flex items-center gap-2 pt-2">
                  <button
                    onClick={onAcceptWeeklyMealPlan}
                    disabled={isAcceptingWeeklyPlan}
                    className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-bold px-3.5 py-2 rounded-xl transition-all cursor-pointer disabled:opacity-60"
                  >
                    <Check className="w-3.5 h-3.5" />
                    {isAcceptingWeeklyPlan ? "Đang xử lý…" : "Chấp nhận thực đơn này"}
                  </button>
                  <button
                    onClick={() => setShowRegenerateModal(true)}
                    disabled={isGeneratingWeeklyPlan}
                    className="inline-flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-bold px-3.5 py-2 rounded-xl transition-all cursor-pointer disabled:opacity-60"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isGeneratingWeeklyPlan ? "animate-spin" : ""}`} />
                    {isGeneratingWeeklyPlan ? "Đang tạo lại…" : "Tạo lại với phản hồi"}
                  </button>
                </div>
              )}
            </motion.div>
          )}

          {/* --- FOOD SAFETY ALERTS & ALLERGEN CHECKER SECTION (ALWAYS VISIBLE) --- */}
          <div className="bg-gradient-to-br from-rose-50/70 via-amber-50/40 to-white border border-rose-100 rounded-3xl p-6 space-y-4 shadow-xs">
            <div className="flex items-center justify-between border-b border-rose-100/80 pb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-rose-600" />
                <h3 className="text-sm font-black text-slate-800">
                  Cảnh Báo An Toàn Thực Phẩm Chuẩn WHO & Kiểm Tra Dị Ứng
                </h3>
              </div>
              <span className="text-[10px] font-bold text-rose-700 bg-rose-100/80 px-2.5 py-1 rounded-full">
                Tiêu chuẩn Y tế Nhi khoa WHO
              </span>
            </div>

            {/* Allergen Check for Active Baby */}
            <div className="bg-white rounded-2xl p-4 border border-rose-100 shadow-xs space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  Tiền sử dị ứng ghi nhận cho bé {activeBaby.name}:
                </p>
                <span className="text-[10px] font-bold text-slate-400">Từ hồ sơ y tế</span>
              </div>

              {activeBaby.allergies && activeBaby.allergies.length > 0 ? (
                <div className="flex flex-wrap items-center gap-2 pt-1">
                  {activeBaby.allergies.map((allergy, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 bg-rose-100 text-rose-800 border border-rose-200 text-xs font-bold px-3 py-1 rounded-xl"
                    >
                      ⚠️ {allergy}
                    </span>
                  ))}
                  <p className="text-[11px] text-rose-600 font-medium w-full mt-1">
                    Cảnh báo: Tuyệt đối tránh cho bé ăn các món chứa {activeBaby.allergies.join(", ")} hoặc các chế phẩm liên quan.
                  </p>
                </div>
              ) : (
                <p className="text-xs text-emerald-700 font-medium bg-emerald-50/80 p-2.5 rounded-xl border border-emerald-100">
                  ✓ Hồ sơ bé hiện chưa ghi nhận tiền sử dị ứng thực phẩm đặc biệt nào.
                </p>
              )}
            </div>

            {/* WHO Food Safety Rules for Infants */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-700">
                🚫 Thực phẩm nguy hiểm CẤM DÙNG cho trẻ dưới 1 tuổi (Chuẩn WHO):
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-white rounded-2xl p-3.5 border border-rose-100 space-y-1">
                  <p className="text-xs font-bold text-rose-700">🍯 Mật ong nguyên chất</p>
                  <p className="text-[11px] text-slate-500 font-medium leading-relaxed">
                    Nguy cơ ngộ độc bào tử vi khuẩn *Clostridium botulinum* ở ruột trẻ dưới 12 tháng.
                  </p>
                </div>
                <div className="bg-white rounded-2xl p-3.5 border border-rose-100 space-y-1">
                  <p className="text-xs font-bold text-rose-700">🧂 Muối & Đường nêm</p>
                  <p className="text-[11px] text-slate-500 font-medium leading-relaxed">
                    Không nêm gia vị muối/đường vào đồ ăn dặm để tránh gây quá tải cho thận của bé.
                  </p>
                </div>
                <div className="bg-white rounded-2xl p-3.5 border border-rose-100 space-y-1">
                  <p className="text-xs font-bold text-rose-700">🥛 Sữa bò tươi nguyên kem</p>
                  <p className="text-[11px] text-slate-500 font-medium leading-relaxed">
                    Đạm và khoáng chất quá cao khó tiêu hóa, không thay thế sữa mẹ/sữa công thức.
                  </p>
                </div>
                <div className="bg-white rounded-2xl p-3.5 border border-rose-100 space-y-1">
                  <p className="text-xs font-bold text-rose-700">🥜 Hạt nguyên hạt / Nhãn</p>
                  <p className="text-[11px] text-slate-500 font-medium leading-relaxed">
                    Tránh thực phẩm hình tròn, cứng, dễ gây tắc đường thở và hóc dị vật nguy hiểm.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: NHẬT KÝ CỮ BÚ & NGUYÊN LIỆU ÁN DẶM */}
      {/* ========================================================================= */}
      {/* ========================================================================= */}
      {/* TAB 2: NHẬT KÝ CỮ BÚ & NGUYÊN LIỆU ÁN DẶM (SUMMARY & TIMELINE) */}
      {/* ========================================================================= */}
      {activeTab === "tracking" && (() => {
        const todayStr = new Date().toISOString().substring(0, 10);
        const todayFeeds = feeds.filter((f) => (f.loggedAt || f.date || "").includes(todayStr));
        const todayIngredients = ingredients.filter((i) => (i.loggedAt || i.date || "").includes(todayStr));

        const totalMilkMl = todayFeeds.reduce((sum, f) => sum + (f.amountMl || f.amount || 0), 0);
        const totalFeedSessions = todayFeeds.length;
        const totalSolidsG = todayIngredients.reduce((sum, i) => sum + (i.amountG || 0), 0);
        
        const categoriesList = Array.from(new Set(todayIngredients.map((i) => i.category).filter(Boolean)));

        // Combine into unified timeline sorted by time descending
        const timelineItems = [
          ...todayFeeds.map((f) => ({
            id: f.id,
            itemType: "feed" as const,
            title: f.type === "formula" || f.type === "Formula" ? "Sữa công thức 🍼" : "Sữa mẹ 🤱",
            subtitle: `${f.amountMl || f.amount || 0} ml`,
            time: f.loggedAt || f.time || f.date || "",
            note: f.note || f.details,
            badgeBg: "bg-indigo-50 text-indigo-700 border-indigo-100",
            icon: <Milk className="w-4 h-4 text-indigo-600" />,
            onDelete: () => onDeleteFeed && onDeleteFeed(f.id)
          })),
          ...todayIngredients.map((i) => {
            const reactionLabels: Record<string, string> = {
              "Loved it": "😋 Rất thích",
              "Neutral": "😐 Bình thường",
              "Spat out": "🤢 Nhè ra",
              "Allergic Reaction": "⚠️ Nghi ngờ dị ứng"
            };
            const reactionText = i.reaction ? (reactionLabels[i.reaction] || i.reaction) : null;
            return {
              id: i.id,
              itemType: "ingredient" as const,
              title: i.name,
              subtitle: `${i.amountG || 0}g • ${i.category || "Ăn dặm"}`,
              time: i.loggedAt || i.date || "",
              note: reactionText,
              badgeBg: i.reaction === "Allergic Reaction" ? "bg-rose-100 text-rose-800 border-rose-200 font-extrabold" : "bg-emerald-50 text-emerald-700 border-emerald-100",
              icon: <Apple className="w-4 h-4 text-emerald-600" />,
              onDelete: () => onDeleteIngredient && onDeleteIngredient(i.id)
            };
          })
        ].sort((a, b) => b.time.localeCompare(a.time));

        return (
          <div className="space-y-6">
            {/* Header Action Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-slate-100 shadow-xs">
              <div>
                <h2 className="text-sm font-black text-slate-800">
                  Nhật Ký Dinh Dưỡng Hôm Nay cho bé {activeBaby.name}
                </h2>
                <p className="text-[11px] font-semibold text-slate-400">
                  Ngày {todayStr} • {timelineItems.length} hoạt động đã ghi nhận
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowAddFeedModal(true)}
                  className="inline-flex items-center gap-1.5 bg-primary hover:bg-primary/95 text-white text-xs font-bold px-3.5 py-2 rounded-xl transition-all shadow-xs cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  + Thêm cữ bú (Sữa)
                </button>

                <button
                  onClick={() => setShowAddIngredientModal(true)}
                  className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3.5 py-2 rounded-xl transition-all shadow-xs cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  + Thêm nguyên liệu ăn dặm
                </button>
              </div>
            </div>

            {/* --- 📊 1. TỔNG QUAN DINH DƯỠNG HÀNG NGÀY (DAILY SUMMARY STATS) --- */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              {/* Stat Card 1: Milk Volume */}
              <div className="bg-gradient-to-br from-indigo-50/80 via-white to-white border border-indigo-100/80 p-4 rounded-2xl shadow-xs space-y-1">
                <div className="flex items-center justify-between text-indigo-600">
                  <span className="text-xs font-bold">Tổng Lượng Sữa</span>
                  <Milk className="w-4 h-4" />
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-xl font-black text-slate-800">{totalMilkMl}</span>
                  <span className="text-xs font-bold text-slate-500">ml</span>
                </div>
                <p className="text-[10px] font-semibold text-indigo-600/80">
                  {totalFeedSessions} cữ bú trong ngày
                </p>
              </div>

              {/* Stat Card 2: Solids Amount */}
              <div className="bg-gradient-to-br from-emerald-50/80 via-white to-white border border-emerald-100/80 p-4 rounded-2xl shadow-xs space-y-1">
                <div className="flex items-center justify-between text-emerald-600">
                  <span className="text-xs font-bold">Tổng Ăn Dặm</span>
                  <Apple className="w-4 h-4" />
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-xl font-black text-slate-800">{totalSolidsG}</span>
                  <span className="text-xs font-bold text-slate-500">gam</span>
                </div>
                <p className="text-[10px] font-semibold text-emerald-600/80">
                  {todayIngredients.length} nguyên liệu ăn dặm
                </p>
              </div>

              {/* Stat Card 3: Food Diversity */}
              <div className="bg-gradient-to-br from-amber-50/80 via-white to-white border border-amber-100/80 p-4 rounded-2xl shadow-xs space-y-1">
                <div className="flex items-center justify-between text-amber-600">
                  <span className="text-xs font-bold">Đa Dạng Nhóm Chất</span>
                  <Sparkles className="w-4 h-4" />
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-xl font-black text-slate-800">{categoriesList.length}</span>
                  <span className="text-xs font-bold text-slate-500">nhóm chất</span>
                </div>
                <p className="text-[10px] font-semibold text-amber-700/80 truncate">
                  {categoriesList.length > 0 ? categoriesList.join(", ") : "Chưa nạp món mới"}
                </p>
              </div>

              {/* Stat Card 4: Latest Activity */}
              <div className="bg-gradient-to-br from-slate-50 via-white to-white border border-slate-200/80 p-4 rounded-2xl shadow-xs space-y-1">
                <div className="flex items-center justify-between text-slate-600">
                  <span className="text-xs font-bold">Hoạt Động Gần Nhất</span>
                  <Clock className="w-4 h-4 text-slate-400" />
                </div>
                <p className="text-xs font-extrabold text-slate-800 truncate">
                  {timelineItems[0] ? timelineItems[0].title : "Chưa có cữ ăn"}
                </p>
                <p className="text-[10px] font-semibold text-slate-400">
                  {timelineItems[0]
                    ? timelineItems[0].time.substring(11, 16) || timelineItems[0].time.substring(0, 10)
                    : "Hôm nay"}
                </p>
              </div>
            </div>

            {/* --- 🕒 2. DÒNG THỜI GIAN DINH DƯỠNG HÔM NAY (TODAY'S TIMELINE) --- */}
            <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-primary" />
                  <h3 className="text-sm font-black text-slate-800">
                    Dòng Thời Gian Dinh Dưỡng Hôm Nay
                  </h3>
                </div>
                <span className="text-xs font-bold text-slate-400">
                  Sắp xếp theo thứ tự thời gian
                </span>
              </div>

              {timelineItems.length === 0 ? (
                <div className="text-center py-12 space-y-2">
                  <Coffee className="w-8 h-8 text-slate-300 mx-auto" />
                  <p className="text-xs font-bold text-slate-600">Hôm nay chưa có cữ ăn nào được ghi nhận</p>
                  <p className="text-[11px] text-slate-400">
                    Hãy bấm nút "+ Thêm cữ bú" hoặc "+ Thêm nguyên liệu ăn dặm" ở trên để lưu sinh hoạt cho bé.
                  </p>
                </div>
              ) : (
                <div className="relative border-l-2 border-slate-100 ml-4 pl-6 space-y-4 py-2">
                  {timelineItems.map((item) => (
                    <div key={item.id} className="relative group">
                      {/* Timeline Dot */}
                      <div className="absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-white border-2 border-primary shadow-xs flex items-center justify-center">
                        <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                      </div>

                      {/* Card item */}
                      <div className="flex items-center justify-between bg-slate-50/80 hover:bg-slate-100/80 p-3.5 rounded-2xl border border-slate-100 transition-all">
                        <div className="flex items-center gap-3">
                          <div className="p-2.5 rounded-xl bg-white border border-slate-200/60 shadow-2xs">
                            {item.icon}
                          </div>
                          <div className="space-y-0.5">
                            <div className="flex items-center gap-2">
                              <p className="text-xs font-bold text-slate-800">{item.title}</p>
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${item.badgeBg}`}>
                                {item.subtitle}
                              </span>
                            </div>
                            <p className="text-[10px] text-slate-400 font-medium flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {item.time.substring(11, 16) || item.time.substring(0, 10)}
                            </p>
                            {item.note && (
                              <p className="text-[11px] text-slate-500 font-medium italic">
                                Ghi chú: {item.note}
                              </p>
                            )}
                          </div>
                        </div>

                        <button
                          onClick={item.onDelete}
                          className="p-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                          title="Xóa bản ghi này"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })()}

      {/* ========================================================================= */}
      {/* MODALS SECTION */}
      {/* ========================================================================= */}

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
                <h3 className="text-sm font-black text-slate-800">Thêm cữ bú mới</h3>
                <button
                  onClick={() => setShowAddFeedModal(false)}
                  className="text-xs font-bold text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  Hủy
                </button>
              </div>

              <form onSubmit={handleAddFeedSubmit} className="space-y-4 text-xs font-bold text-slate-600">
                <div className="space-y-1">
                  <label className="block">Loại sữa</label>
                  <select
                    value={feedType}
                    onChange={(e) => setFeedType(e.target.value as any)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 focus:border-primary focus:outline-hidden font-semibold"
                  >
                    <option value="formula">Sữa công thức 🍼</option>
                    <option value="breast">Sữa mẹ 🤱</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="block">Lượng sữa (ml)</label>
                  <input
                    type="number"
                    min={10}
                    max={500}
                    value={feedAmount}
                    onChange={(e) => setFeedAmount(Number(e.target.value))}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 focus:border-primary focus:outline-hidden font-semibold"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="block">Ghi chú (tùy chọn)</label>
                  <input
                    type="text"
                    value={feedNote}
                    onChange={(e) => setFeedNote(e.target.value)}
                    placeholder="Ví dụ: bú ngoan, ợ hơi tốt..."
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 focus:border-primary focus:outline-hidden font-medium"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-white py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer"
                >
                  Lưu cữ bú
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* --- ADD INGREDIENT MODAL --- */}
      <AnimatePresence>
        {showAddIngredientModal && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-black text-slate-800">Thêm nguyên liệu ăn dặm</h3>
                <button
                  onClick={() => setShowAddIngredientModal(false)}
                  className="text-xs font-bold text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  Hủy
                </button>
              </div>

              <form onSubmit={handleAddIngredientSubmit} className="space-y-4 text-xs font-bold text-slate-600">
                <div className="space-y-1">
                  <label className="block">Tên nguyên liệu / Món ăn</label>
                  <input
                    type="text"
                    value={ingredientName}
                    onChange={(e) => setIngredientName(e.target.value)}
                    placeholder="Ví dụ: Bí đỏ, Cháo thịt lợn, Cá hồi..."
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 focus:border-primary focus:outline-hidden font-medium"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="block">Nhóm thực phẩm</label>
                  <select
                    value={ingredientCategory}
                    onChange={(e) => setIngredientCategory(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 focus:border-primary focus:outline-hidden font-semibold"
                  >
                    <option value="Rau củ">Rau củ / Trái cây 🥦</option>
                    <option value="Đạm / Thịt cá">Đạm / Thịt cá 🥩</option>
                    <option value="Tinh bột / Cháo">Tinh bột / Cháo 🥣</option>
                    <option value="Sữa / Phô mai">Sữa / Phô mai 🧀</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="block">Khối lượng (gam)</label>
                  <input
                    type="number"
                    min={5}
                    max={500}
                    value={ingredientAmount}
                    onChange={(e) => setIngredientAmount(Number(e.target.value))}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 focus:border-primary focus:outline-hidden font-semibold"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="block">Phản ứng của bé khi thử món</label>
                  <select
                    value={ingredientReaction}
                    onChange={(e) => setIngredientReaction(e.target.value as any)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 focus:border-primary focus:outline-hidden font-semibold text-slate-800"
                  >
                    <option value="Loved it">😋 Rất thích / Ăn ngoan (Loved it)</option>
                    <option value="Neutral">😐 Bình thường / Chấp nhận (Neutral)</option>
                    <option value="Spat out">🤢 Nhè ra / Không hợp vị (Spat out)</option>
                    <option value="Allergic Reaction">⚠️ Nghi ngờ dị ứng / Nổi mẩn (Allergic Reaction)</option>
                  </select>
                </div>

                <button
                  type="submit"
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer"
                >
                  Lưu nguyên liệu
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* --- REGENERATE WEEKLY MEAL PLAN MODAL --- */}
      <AnimatePresence>
        {showRegenerateModal && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-black text-slate-800">Tạo lại thực đơn 7 ngày</h3>
                <button
                  onClick={() => setShowRegenerateModal(false)}
                  className="text-xs font-bold text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  Hủy
                </button>
              </div>

              <form onSubmit={handleRegenerateSubmit} className="space-y-4 text-xs font-bold text-slate-600">
                <div className="space-y-1">
                  <label className="block">Phản hồi cho AI (không bắt buộc)</label>
                  <textarea
                    value={regenerateFeedback}
                    onChange={(e) => setRegenerateFeedback(e.target.value)}
                    placeholder="Ví dụ: bé không thích cá, tránh món cay, muốn nhiều rau củ hơn..."
                    rows={3}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 focus:border-primary/45 focus:outline-hidden font-medium resize-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isGeneratingWeeklyPlan}
                  className="w-full bg-primary hover:bg-primary/95 text-white py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer disabled:opacity-60"
                >
                  {isGeneratingWeeklyPlan ? "Đang tạo lại…" : "Tạo thực đơn mới"}
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* --- SAFETY HANDBOOK MODAL --- */}
      <AnimatePresence>
        {showSafetyHandbookModal && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[80vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-black text-slate-800">
                  {safetyHandbook?.title || "Cẩm nang An toàn Dinh dưỡng"}
                </h3>
                <button
                  onClick={() => setShowSafetyHandbookModal(false)}
                  className="text-xs font-bold text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  Đóng
                </button>
              </div>

              {isLoadingSafetyHandbook && !safetyHandbook && (
                <p className="text-[11px] text-slate-400 font-semibold text-center py-6">Đang tải cẩm nang…</p>
              )}

              {safetyHandbook && (
                <div className="space-y-3">
                  {safetyHandbook.sections.map((section, idx) => (
                    <div
                      key={idx}
                      className={`border rounded-2xl p-3.5 space-y-1.5 ${
                        HANDBOOK_LEVEL_STYLES[section.level] || HANDBOOK_LEVEL_STYLES.info
                      }`}
                    >
                      <h4 className="text-xs font-bold">{section.title}</h4>
                      <p className="text-[11px] leading-relaxed font-medium">{section.description}</p>
                      {section.items && section.items.length > 0 && (
                        <ul className="list-disc list-inside text-[11px] leading-relaxed font-medium space-y-0.5">
                          {section.items.map((item, itemIdx) => (
                            <li key={itemIdx}>{item}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
