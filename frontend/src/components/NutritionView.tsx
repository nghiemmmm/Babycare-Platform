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
  Apple,
  Milk,
  Clock,
  ChevronRight,
  Utensils,
  Search,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Award
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
const MEAL_TYPE_LABELS: Record<string, { title: string; icon: string; time: string }> = {
  sáng: { title: "Bữa Sáng", icon: "🌅", time: "07:30 - 08:30" },
  trưa: { title: "Bữa Trưa", icon: "☀️", time: "11:30 - 12:30" },
  tối: { title: "Bữa Tối", icon: "🌙", time: "17:30 - 18:30" },
  phụ: { title: "Bữa Phụ", icon: "🍎", time: "15:00 - 15:30" }
};

const REACTION_CONFIG: Record<string, { label: string; bg: string; icon: string }> = {
  "Loved it": { label: "😋 Rất thích", bg: "bg-emerald-50 text-emerald-700 border-emerald-200", icon: "😋" },
  Neutral: { label: "😐 Bình thường", bg: "bg-slate-50 text-slate-700 border-slate-200", icon: "😐" },
  "Spat out": { label: "🤢 Nhè ra", bg: "bg-amber-50 text-amber-700 border-amber-200", icon: "🤢" },
  "Allergic Reaction": {
    label: "⚠️ Nghi ngờ dị ứng",
    bg: "bg-rose-100 text-rose-800 border-rose-300 font-bold animate-pulse",
    icon: "⚠️"
  }
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
  safetyHandbook,
  isLoadingSafetyHandbook = false,
  onOpenSafetyHandbook
}: NutritionViewProps) {
  const [activeTab, setActiveTab] = useState<"ai" | "tracking" | "safety">("ai");
  const [selectedMealPlanDayIndex, setSelectedMealPlanDayIndex] = useState<number>(0);

  // Quick Food Safety Search
  const [searchFoodQuery, setSearchFoodQuery] = useState("");

  // Modals for tracking
  const [showAddFeedModal, setShowAddFeedModal] = useState(false);
  const [showAddIngredientModal, setShowAddIngredientModal] = useState(false);

  // Feed Form State
  const [feedType, setFeedType] = useState<"formula" | "breast">("formula");
  const [feedAmount, setFeedAmount] = useState<number>(150);
  const [feedNote, setFeedNote] = useState<string>("");

  // Ingredient Form State
  const [ingredientName, setIngredientName] = useState<string>("");
  const [ingredientCategory, setIngredientCategory] = useState<string>("Rau củ");
  const [ingredientAmount, setIngredientAmount] = useState<number>(50);
  const [ingredientReaction, setIngredientReaction] = useState<"Loved it" | "Neutral" | "Spat out" | "Allergic Reaction">("Loved it");

  // AI Modals
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [regenerateFeedback, setRegenerateFeedback] = useState("");
  const [showSafetyHandbookModal, setShowSafetyHandbookModal] = useState(false);

  // Submits
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

  // Calculations for Today's Stats
  const todayStr = new Date().toISOString().substring(0, 10);
  const todayFeeds = feeds.filter((f) => (f.loggedAt || f.date || "").includes(todayStr));
  const todayIngredients = ingredients.filter((i) => (i.loggedAt || i.date || "").includes(todayStr));

  const totalMilkMl = todayFeeds.reduce((sum, f) => sum + (f.amountMl || f.amount || 0), 0);
  const totalSolidsG = todayIngredients.reduce((sum, i) => sum + (i.amountG || 0), 0);
  const foodCategories = Array.from(new Set(todayIngredients.map((i) => i.category).filter(Boolean)));

  // Combine feeds + ingredients into timeline sorted descending
  const timelineItems = [
    ...todayFeeds.map((f) => ({
      id: f.id,
      itemType: "feed" as const,
      title: f.type === "formula" || f.type === "Formula" ? "Sữa công thức 🍼" : "Sữa mẹ 🤱",
      subtitle: `${f.amountMl || f.amount || 0} ml`,
      time: f.loggedAt || f.time || f.date || "",
      note: f.note || f.details,
      reactionBadge: null,
      icon: <Milk className="w-4 h-4 text-indigo-500" />,
      onDelete: () => onDeleteFeed && onDeleteFeed(f.id)
    })),
    ...todayIngredients.map((i) => {
      const reactionObj = i.reaction ? REACTION_CONFIG[i.reaction] : null;
      return {
        id: i.id,
        itemType: "ingredient" as const,
        title: i.name,
        subtitle: `${i.amountG || 0}g • ${i.category || "Ăn dặm"}`,
        time: i.loggedAt || i.date || "",
        note: null,
        reactionBadge: reactionObj,
        icon: <Apple className="w-4 h-4 text-emerald-500" />,
        onDelete: () => onDeleteIngredient && onDeleteIngredient(i.id)
      };
    })
  ].sort((a, b) => b.time.localeCompare(a.time));

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* ========================================================================= */}
      {/* 👑 HERO BANNER HEADER & TOP NAV SWITCHER */}
      {/* ========================================================================= */}
      <div className="relative overflow-hidden bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-rose-500/10 border border-amber-200/50 rounded-3xl p-6 sm:p-8 backdrop-blur-xl shadow-xs">
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          {/* Baby Info & Title */}
          <div className="flex items-center gap-4">
            <div className="relative">
              <img
                src={activeBaby.avatarUrl || "/static/img/leo.png"}
                alt={activeBaby.name}
                className="w-16 h-16 rounded-2xl object-cover border-2 border-white shadow-md"
              />
              <span className="absolute -bottom-1 -right-1 bg-amber-500 text-white p-1 rounded-full text-xs shadow-xs">
                <Utensils className="w-3.5 h-3.5" />
              </span>
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                  Dinh Dưỡng & Thực Đơn AI
                </h1>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-800 border border-amber-200">
                  Chuẩn WHO & AAP
                </span>
              </div>
              <p className="text-xs text-slate-600 font-medium">
                Hồ sơ bé <span className="font-bold text-slate-900">{activeBaby.name}</span> • 
                {activeBaby.allergies && activeBaby.allergies.length > 0 ? (
                  <span className="text-rose-600 font-bold ml-1">
                    ⚠️ Dị ứng: {activeBaby.allergies.join(", ")}
                  </span>
                ) : (
                  <span className="text-emerald-600 font-bold ml-1">✓ Chưa ghi nhận dị ứng</span>
                )}
              </p>
            </div>
          </div>

          {/* Quick Metrics Pills */}
          <div className="flex items-center gap-3 overflow-x-auto pb-1 lg:pb-0">
            <div className="bg-white/80 backdrop-blur-md px-4 py-2.5 rounded-2xl border border-white/80 shadow-2xs flex items-center gap-3 shrink-0">
              <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
                <Milk className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase">Sữa hôm nay</p>
                <p className="text-sm font-black text-slate-800">{totalMilkMl} ml</p>
              </div>
            </div>

            <div className="bg-white/80 backdrop-blur-md px-4 py-2.5 rounded-2xl border border-white/80 shadow-2xs flex items-center gap-3 shrink-0">
              <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
                <Apple className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase">Ăn dặm</p>
                <p className="text-sm font-black text-slate-800">{totalSolidsG} g</p>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Selector Segmented Controls */}
        <div className="mt-6 pt-5 border-t border-amber-200/40 flex items-center justify-between gap-3 overflow-x-auto">
          <div className="flex items-center gap-2 p-1 bg-white/70 backdrop-blur-md rounded-2xl border border-slate-200/60 shadow-2xs">
            <button
              onClick={() => setActiveTab("ai")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === "ai"
                  ? "bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-md"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              Thực Đơn 7 Ngày & Trợ Lý AI
            </button>

            <button
              onClick={() => setActiveTab("tracking")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === "tracking"
                  ? "bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-md"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Coffee className="w-3.5 h-3.5" />
              Nhật Ký Dinh Dưỡng Hôm Nay ({timelineItems.length})
            </button>

            <button
              onClick={() => setActiveTab("safety")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === "safety"
                  ? "bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-md"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              An Toàn & Dị Ứng WHO
            </button>
          </div>

          <button
            onClick={() => {
              setShowSafetyHandbookModal(true);
              if (onOpenSafetyHandbook) onOpenSafetyHandbook();
            }}
            className="hidden sm:inline-flex items-center gap-1.5 bg-white/80 hover:bg-white text-slate-700 text-xs font-bold px-3.5 py-2 rounded-xl border border-slate-200 shadow-2xs transition-all cursor-pointer shrink-0"
          >
            <BookOpen className="w-3.5 h-3.5 text-indigo-500" />
            Cẩm Nang Nhi Khoa
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 🌟 TAB 1: THỰC ĐƠN 7 NGÀY & TRỢ LÝ AI (2-COLUMN DASHBOARD) */}
      {/* ========================================================================= */}
      {activeTab === "ai" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* MAIN LEFT COLUMN (2/3): 7-DAY MEAL PLAN */}
          <div className="lg:col-span-2 space-y-6">
            {/* Header Actions */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-5 rounded-3xl border border-slate-100 shadow-xs">
              <div>
                <h2 className="text-sm font-black text-slate-900">
                  Thực Đơn Ăn Dặm 7 Ngày Dành Cho Bé {activeBaby.name}
                </h2>
                <p className="text-[11px] text-slate-500 font-medium">
                  {weeklyMealPlan
                    ? `Áp dụng từ ${weeklyMealPlan.startDate} đến ${weeklyMealPlan.endDate}`
                    : "Chưa có thực đơn tuần. Hãy bấm nút tạo dưới đây."}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => onGenerateWeeklyMealPlan && onGenerateWeeklyMealPlan()}
                  disabled={isGeneratingWeeklyPlan}
                  className="inline-flex items-center gap-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white text-xs font-bold px-4 py-2.5 rounded-2xl shadow-md transition-all cursor-pointer disabled:opacity-60"
                >
                  <Calendar className={`w-4 h-4 ${isGeneratingWeeklyPlan ? "animate-spin" : ""}`} />
                  {isGeneratingWeeklyPlan ? "Đang tạo thực đơn…" : "📅 Tạo Thực Đơn 7 Ngày AI"}
                </button>
              </div>
            </div>

            {/* Interactive 7-Day Meal Plan Grid Card */}
            {weeklyMealPlan ? (
              <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-xs space-y-6">
                {/* Status Bar */}
                <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                  <div className="flex items-center gap-2">
                    <Award className="w-5 h-5 text-amber-500" />
                    <span className="text-xs font-bold text-slate-800">
                      {weeklyMealPlan.summary || "Thực đơn dinh dưỡng chuẩn WHO cho bé"}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-bold px-3 py-1 rounded-full ${
                      weeklyMealPlan.status === "accepted"
                        ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                        : "bg-amber-100 text-amber-800 border border-amber-200"
                    }`}
                  >
                    {weeklyMealPlan.status === "accepted" ? "✓ Đã Chấp Nhận Áp Dụng" : "Chờ Duyệt"}
                  </span>
                </div>

                {/* Day Tabs Switcher */}
                <div className="flex items-center gap-2 overflow-x-auto pb-2">
                  {weeklyMealPlan.days.map((day, idx) => {
                    const isSelected = selectedMealPlanDayIndex === idx;
                    const dateParts = day.date.split("-");
                    const dateDisplay = `${dateParts[2]}/${dateParts[1]}`;
                    return (
                      <button
                        key={day.date}
                        onClick={() => setSelectedMealPlanDayIndex(idx)}
                        className={`flex flex-col items-center min-w-[72px] px-3 py-2 rounded-2xl text-xs font-bold transition-all cursor-pointer border ${
                          isSelected
                            ? "bg-primary text-white border-primary shadow-md"
                            : "bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200/60"
                        }`}
                      >
                        <span className="text-[10px] opacity-80 font-medium">Thứ {idx + 2 > 7 ? "CN" : idx + 2}</span>
                        <span className="text-xs font-black">{dateDisplay}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Selected Day Meals List */}
                {weeklyMealPlan.days[selectedMealPlanDayIndex] && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                    {MEAL_TYPES.map((mealType) => {
                      const config = MEAL_TYPE_LABELS[mealType];
                      const meal = weeklyMealPlan.days[selectedMealPlanDayIndex].meals.find(
                        (m) => m.mealType.toLowerCase() === mealType
                      );

                      return (
                        <div
                          key={mealType}
                          className="bg-slate-50/70 hover:bg-slate-50 border border-slate-200/60 rounded-2xl p-4 space-y-2 transition-all"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-black text-slate-800 flex items-center gap-1.5">
                              <span>{config.icon}</span>
                              {config.title}
                            </span>
                            <span className="text-[10px] font-bold text-slate-400 bg-white px-2 py-0.5 rounded-md border border-slate-200">
                              {config.time}
                            </span>
                          </div>

                          {meal ? (
                            <div className="space-y-1">
                              <p className="text-xs font-bold text-primary leading-snug">
                                {meal.foodName}
                              </p>
                              {meal.note && (
                                <p className="text-[11px] text-slate-500 font-medium leading-relaxed">
                                  {meal.note}
                                </p>
                              )}
                            </div>
                          ) : (
                            <p className="text-xs text-slate-400 font-medium italic py-1">
                              Chưa xếp món ăn cho bữa này.
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Plan Action Buttons */}
                <div className="flex items-center gap-3 pt-2 border-t border-slate-100">
                  {weeklyMealPlan.status === "pending" && (
                    <button
                      onClick={onAcceptWeeklyMealPlan}
                      disabled={isAcceptingWeeklyPlan}
                      className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2.5 rounded-2xl shadow-md transition-all cursor-pointer disabled:opacity-60"
                    >
                      <Check className="w-4 h-4" />
                      {isAcceptingWeeklyPlan ? "Đang xử lý…" : "✓ Chấp Nhận Áp Dụng Thực Đơn Này"}
                    </button>
                  )}

                  <button
                    onClick={() => setShowRegenerateModal(true)}
                    disabled={isGeneratingWeeklyPlan}
                    className="inline-flex items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold px-4 py-2.5 rounded-2xl transition-all cursor-pointer disabled:opacity-60"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isGeneratingWeeklyPlan ? "animate-spin" : ""}`} />
                    Tạo Lại Thực Đơn Khác
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-white border border-slate-100 rounded-3xl p-12 text-center space-y-4 shadow-xs">
                <div className="w-16 h-16 rounded-3xl bg-amber-50 text-amber-500 flex items-center justify-center mx-auto border border-amber-100">
                  <Calendar className="w-8 h-8" />
                </div>
                <div className="space-y-1 max-w-md mx-auto">
                  <h3 className="text-base font-black text-slate-800">Chưa Có Thực Đơn 7 Ngày AI</h3>
                  <p className="text-xs text-slate-500 font-medium">
                    Hãy bấm nút bên dưới để AI tự động lên thực đơn ăn dặm 7 ngày cân đối 4 nhóm chất chuẩn WHO cho bé {activeBaby.name}.
                  </p>
                </div>
                <button
                  onClick={() => onGenerateWeeklyMealPlan && onGenerateWeeklyMealPlan()}
                  disabled={isGeneratingWeeklyPlan}
                  className="inline-flex items-center gap-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white text-xs font-bold px-5 py-3 rounded-2xl shadow-lg transition-all cursor-pointer"
                >
                  <Sparkles className="w-4 h-4" />
                  Bắt Đầu Tạo Thực Đơn 7 Ngày AI
                </button>
              </div>
            )}
          </div>

          {/* RIGHT SIDEBAR COLUMN (1/3): AI RECOMMENDATIONS WIDGET */}
          <div className="space-y-6">
            {/* AI Smart Food Recommendation Widget */}
            <div className="bg-gradient-to-br from-amber-50/80 via-white to-white border border-amber-200/60 rounded-3xl p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-amber-200/60 pb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-amber-500" />
                  <h3 className="text-sm font-black text-slate-800">Gợi Ý Dinh Dưỡng AI</h3>
                </div>
                <button
                  onClick={onGenerateRecommendation}
                  disabled={isGeneratingRecommendation}
                  className="p-1.5 rounded-xl bg-white border border-amber-200 hover:bg-amber-100 text-amber-700 transition-all cursor-pointer"
                  title="Tải lại gợi ý"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isGeneratingRecommendation ? "animate-spin" : ""}`} />
                </button>
              </div>

              {recommendation ? (
                <div className="space-y-4">
                  <p className="text-xs text-slate-600 font-medium leading-relaxed bg-white/80 p-3 rounded-2xl border border-amber-100">
                    {recommendation.summary}
                  </p>

                  {/* Recommended Foods List */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-emerald-800 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      Món ăn khuyến nghị nên bổ sung:
                    </h4>
                    <div className="space-y-2">
                      {recommendation.recommendedFoods.map((item, idx) => (
                        <div key={idx} className="bg-white p-3 rounded-2xl border border-slate-100 shadow-2xs space-y-0.5">
                          <p className="text-xs font-bold text-slate-800">{item.foodName}</p>
                          <p className="text-[11px] text-slate-500 font-medium">{item.reason}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Foods to Avoid List */}
                  <div className="space-y-2 pt-2">
                    <h4 className="text-xs font-bold text-rose-800 flex items-center gap-1.5">
                      <XCircle className="w-4 h-4 text-rose-600" />
                      Món cần hạn chế / Tránh:
                    </h4>
                    <div className="space-y-2">
                      {recommendation.foodsToAvoid.map((item, idx) => (
                        <div key={idx} className="bg-rose-50/60 p-3 rounded-2xl border border-rose-100 space-y-0.5">
                          <div className="flex items-center justify-between">
                            <p className="text-xs font-bold text-rose-900">{item.foodName}</p>
                            {item.linkedTo && (
                              <span className="text-[9px] font-bold bg-rose-100 text-rose-700 px-2 py-0.5 rounded-md">
                                {item.linkedTo}
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-rose-700/80 font-medium">{item.reason}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-6 space-y-3">
                  <Apple className="w-8 h-8 text-amber-400 mx-auto" />
                  <p className="text-xs text-slate-500 font-medium">
                    Chưa có khuyến nghị cá nhân hóa cho bé {activeBaby.name}.
                  </p>
                  <button
                    onClick={onGenerateRecommendation}
                    disabled={isGeneratingRecommendation}
                    className="w-full py-2.5 rounded-2xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold transition-all shadow-md cursor-pointer"
                  >
                    {isGeneratingRecommendation ? "Đang phân tích…" : "Tạo Khuyên Nghị Dinh Dưỡng AI"}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 🥣 TAB 2: NHẬT KÝ SINH HOẠT DINH DƯỠNG HÔM NAY (TIMELINE & TRACKING) */}
      {/* ========================================================================= */}
      {activeTab === "tracking" && (
        <div className="space-y-6">
          {/* Header Action Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-5 rounded-3xl border border-slate-100 shadow-xs">
            <div>
              <h2 className="text-sm font-black text-slate-800">
                Nhật Ký & Dòng Thời Gian Dinh Dưỡng Hôm Nay
              </h2>
              <p className="text-[11px] font-semibold text-slate-400">
                Bé {activeBaby.name} • Ngày {todayStr} ({timelineItems.length} hoạt động)
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowAddFeedModal(true)}
                className="inline-flex items-center gap-1.5 bg-primary hover:bg-primary/95 text-white text-xs font-bold px-4 py-2.5 rounded-2xl transition-all shadow-xs cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                + Thêm cữ bú (Sữa)
              </button>

              <button
                onClick={() => setShowAddIngredientModal(true)}
                className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2.5 rounded-2xl transition-all shadow-xs cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                + Thêm nguyên liệu ăn dặm
              </button>
            </div>
          </div>

          {/* 📊 Summary Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white border border-slate-100 p-4 rounded-2xl shadow-xs space-y-1">
              <div className="flex items-center justify-between text-indigo-600">
                <span className="text-xs font-bold">Tổng Lượng Sữa</span>
                <Milk className="w-4 h-4" />
              </div>
              <p className="text-xl font-black text-slate-800">{totalMilkMl} <span className="text-xs font-bold text-slate-400">ml</span></p>
              <p className="text-[10px] font-semibold text-indigo-600/80">{todayFeeds.length} cữ bú trong ngày</p>
            </div>

            <div className="bg-white border border-slate-100 p-4 rounded-2xl shadow-xs space-y-1">
              <div className="flex items-center justify-between text-emerald-600">
                <span className="text-xs font-bold">Tổng Ăn Dặm</span>
                <Apple className="w-4 h-4" />
              </div>
              <p className="text-xl font-black text-slate-800">{totalSolidsG} <span className="text-xs font-bold text-slate-400">gam</span></p>
              <p className="text-[10px] font-semibold text-emerald-600/80">{todayIngredients.length} món ăn dặm</p>
            </div>

            <div className="bg-white border border-slate-100 p-4 rounded-2xl shadow-xs space-y-1">
              <div className="flex items-center justify-between text-amber-600">
                <span className="text-xs font-bold">Đa Dạng Nhóm Chất</span>
                <Sparkles className="w-4 h-4" />
              </div>
              <p className="text-xl font-black text-slate-800">{foodCategories.length} <span className="text-xs font-bold text-slate-400">nhóm</span></p>
              <p className="text-[10px] font-semibold text-amber-700/80 truncate">
                {foodCategories.length > 0 ? foodCategories.join(", ") : "Chưa thử món mới"}
              </p>
            </div>

            <div className="bg-white border border-slate-100 p-4 rounded-2xl shadow-xs space-y-1">
              <div className="flex items-center justify-between text-slate-600">
                <span className="text-xs font-bold">Cữ Ăn Gần Nhất</span>
                <Clock className="w-4 h-4 text-slate-400" />
              </div>
              <p className="text-xs font-black text-slate-800 truncate">
                {timelineItems[0] ? timelineItems[0].title : "Chưa có cữ ăn"}
              </p>
              <p className="text-[10px] font-semibold text-slate-400">
                {timelineItems[0] ? (timelineItems[0].time.substring(11, 16) || timelineItems[0].time.substring(0, 10)) : "Hôm nay"}
              </p>
            </div>
          </div>

          {/* 🕒 Timeline Section */}
          <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
                <Clock className="w-5 h-5 text-primary" />
                Dòng Thời Gian Ăn Uống (Từ Sáng Đến Tối)
              </h3>
            </div>

            {timelineItems.length === 0 ? (
              <div className="text-center py-12 space-y-2">
                <Coffee className="w-8 h-8 text-slate-300 mx-auto" />
                <p className="text-xs font-bold text-slate-600">Hôm nay chưa có lịch sử ăn bú nào</p>
                <p className="text-[11px] text-slate-400">
                  Bấm nút "+ Thêm cữ bú" hoặc "+ Thêm nguyên liệu" để bắt đầu theo dõi.
                </p>
              </div>
            ) : (
              <div className="relative border-l-2 border-slate-100 ml-4 pl-6 space-y-4 py-2">
                {timelineItems.map((item) => (
                  <div key={item.id} className="relative group">
                    <div className="absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-white border-2 border-primary shadow-xs flex items-center justify-center">
                      <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                    </div>

                    <div className="flex items-center justify-between bg-slate-50/80 hover:bg-slate-100 p-4 rounded-2xl border border-slate-100 transition-all">
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-white border border-slate-200/60 shadow-2xs">
                          {item.icon}
                        </div>
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2">
                            <p className="text-xs font-bold text-slate-800">{item.title}</p>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700">
                              {item.subtitle}
                            </span>
                            {item.reactionBadge && (
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${item.reactionBadge.bg}`}>
                                {item.reactionBadge.label}
                              </span>
                            )}
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
      )}

      {/* ========================================================================= */}
      {/* 🛡️ TAB 3: AN TOÀN THỰC PHẨM & KIỂM TRA DỊ ỨNG WHO */}
      {/* ========================================================================= */}
      {activeTab === "safety" && (
        <div className="space-y-6">
          {/* Quick Food Safety Search Bar */}
          <div className="bg-gradient-to-br from-indigo-50/80 via-white to-white border border-indigo-100 rounded-3xl p-6 space-y-4 shadow-xs">
            <div className="space-y-1">
              <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
                <Search className="w-4 h-4 text-indigo-600" />
                Tra Cứu Nhanh Tính An Toàn Thực Phẩm Cho Bé
              </h3>
              <p className="text-xs text-slate-500 font-medium">
                Nhập tên món ăn/nguyên liệu bất kỳ để kiểm tra ngay quy tắc an toàn y tế WHO.
              </p>
            </div>

            <div className="relative">
              <input
                type="text"
                value={searchFoodQuery}
                onChange={(e) => setSearchFoodQuery(e.target.value)}
                placeholder="Ví dụ: Mật ong, Sữa chua, Hải sản, Tôm, Bánh mì..."
                className="w-full bg-white border border-slate-200 rounded-2xl px-4 py-3 text-xs font-semibold text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500"
              />
            </div>
          </div>

          {/* Allergen Card */}
          <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                Tiền Sử Dị Ứng Của Bé {activeBaby.name}
              </h3>
            </div>

            {activeBaby.allergies && activeBaby.allergies.length > 0 ? (
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  {activeBaby.allergies.map((allergy, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 bg-rose-100 text-rose-800 border border-rose-200 text-xs font-bold px-3 py-1.5 rounded-xl"
                    >
                      ⚠️ {allergy}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-rose-600 font-medium">
                  Cảnh báo: AI sẽ tự động lọc bỏ các món chứa {activeBaby.allergies.join(", ")} khỏi thực đơn ăn dặm gợi ý.
                </p>
              </div>
            ) : (
              <p className="text-xs text-emerald-700 font-medium bg-emerald-50/80 p-3 rounded-2xl border border-emerald-100">
                ✓ Hồ sơ bé hiện chưa ghi nhận tiền sử dị ứng thực phẩm đặc biệt nào.
              </p>
            )}
          </div>

          {/* WHO Dangerous Foods */}
          <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-xs space-y-4">
            <h3 className="text-sm font-black text-slate-800 flex items-center gap-2 border-b border-slate-100 pb-3">
              <ShieldAlert className="w-5 h-5 text-rose-600" />
              Thực Phẩm Nguy Hiểm CẤM DÙNG Cho Trẻ Dưới 1 Tuổi (Chuẩn WHO)
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-rose-50/50 border border-rose-100 p-4 rounded-2xl space-y-1">
                <p className="text-xs font-bold text-rose-800">🍯 Mật ong nguyên chất</p>
                <p className="text-xs text-slate-600 font-medium leading-relaxed">
                  Bào tử vi khuẩn *Clostridium botulinum* trong mật ong có thể sinh độc tố ruột nguy hiểm cho trẻ dưới 12 tháng.
                </p>
              </div>

              <div className="bg-rose-50/50 border border-rose-100 p-4 rounded-2xl space-y-1">
                <p className="text-xs font-bold text-rose-800">🧂 Muối & Đường gia vị</p>
                <p className="text-xs text-slate-600 font-medium leading-relaxed">
                  Tuyệt đối không nêm muối/đường vào đồ ăn dặm để bảo vệ chức năng thận còn non nớt của trẻ.
                </p>
              </div>

              <div className="bg-rose-50/50 border border-rose-100 p-4 rounded-2xl space-y-1">
                <p className="text-xs font-bold text-rose-800">🥛 Sữa bò tươi nguyên kem</p>
                <p className="text-xs text-slate-600 font-medium leading-relaxed">
                  Hàm lượng đạm và khoáng chất cao khó hấp thu, không dùng thay thế sữa mẹ hoặc sữa công thức trước 1 tuổi.
                </p>
              </div>

              <div className="bg-rose-50/50 border border-rose-100 p-4 rounded-2xl space-y-1">
                <p className="text-xs font-bold text-rose-800">🥜 Hạt cứng nguyên hạt & Nhãn</p>
                <p className="text-xs text-slate-600 font-medium leading-relaxed">
                  Thực phẩm tròn, cứng có nguy cơ cao hóc đường thở dị vật cấp cứu.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODALS SECTION */}
      {/* ========================================================================= */}
      <AnimatePresence>
        {/* ADD FEED MODAL */}
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

        {/* ADD INGREDIENT MODAL */}
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

        {/* REGENERATE MEAL PLAN MODAL */}
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

        {/* SAFETY HANDBOOK MODAL */}
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
                  {safetyHandbook?.title || "Cẩm nang An toàn Dinh dưỡng (WHO/AAP)"}
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
                      className="bg-indigo-50/70 border border-indigo-100 rounded-2xl p-4 space-y-1.5 text-indigo-900"
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
