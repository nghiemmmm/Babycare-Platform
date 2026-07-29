import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Check,
  Info,
  Calendar,
  Sparkles,
  BookOpen,
  RefreshCw
} from "lucide-react";
import { BabyProfile, NutritionRecommendation, WeeklyMealPlan, NutritionSafety, SafetyHandbook, FoodSafetyItem } from "../types";

interface NutritionViewProps {
  activeBaby: BabyProfile;
  recommendation: NutritionRecommendation | null;
  isGeneratingRecommendation: boolean;
  onGenerateRecommendation: () => Promise<void> | void;
  weeklyMealPlan: WeeklyMealPlan | null;
  isGeneratingWeeklyPlan: boolean;
  isAcceptingWeeklyPlan: boolean;
  onGenerateWeeklyMealPlan: (feedback?: string) => Promise<void> | void;
  onAcceptWeeklyMealPlan: () => Promise<void> | void;
  nutritionSafety: NutritionSafety | null;
  safetyHandbook: SafetyHandbook | null;
  isLoadingSafetyHandbook: boolean;
  onOpenSafetyHandbook: () => Promise<void> | void;
}

const SAFETY_CATEGORY_LABELS: Record<string, string> = {
  under_1_year: "Thực phẩm cần tránh (Dưới 1 tuổi)",
  choking_hazard: "Nguy cơ hóc dị vật (Dưới 3 tuổi)"
};

const HANDBOOK_LEVEL_STYLES: Record<string, string> = {
  info: "bg-blue-50 border-blue-100 text-blue-700",
  danger: "bg-red-50 border-red-100 text-red-700",
  warning: "bg-amber-50 border-amber-100 text-amber-700",
  success: "bg-emerald-50 border-emerald-100 text-emerald-700"
};

const MEAL_TYPE_ORDER = ["sáng", "trưa", "tối", "phụ"];
const MEAL_TYPE_LABELS: Record<string, string> = { "sáng": "Sáng", "trưa": "Trưa", "tối": "Tối", "phụ": "Phụ" };

function formatShortDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  const weekdays = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];
  return `${weekdays[d.getDay()]} ${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function daysUntil(dateStr: string): number {
  const target = new Date(dateStr + "T00:00:00");
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.ceil((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

export default function NutritionView({
  activeBaby,
  recommendation,
  isGeneratingRecommendation,
  onGenerateRecommendation,
  weeklyMealPlan,
  isGeneratingWeeklyPlan,
  isAcceptingWeeklyPlan,
  onGenerateWeeklyMealPlan,
  onAcceptWeeklyMealPlan,
  nutritionSafety,
  safetyHandbook,
  isLoadingSafetyHandbook,
  onOpenSafetyHandbook
}: NutritionViewProps) {
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [regenerateFeedback, setRegenerateFeedback] = useState("");
  const [weeklyPlanError, setWeeklyPlanError] = useState<string | null>(null);
  const [showSafetyHandbookModal, setShowSafetyHandbookModal] = useState(false);

  // Trạng thái mở/thu gọn lý do cho từng thực phẩm cần tránh - key theo tên món, độc lập với
  // dữ liệu foodsToAvoid (giờ lấy từ backend theo đúng tuổi thật của bé, không hardcode nữa).
  const [expandedFoodInfo, setExpandedFoodInfo] = useState<Record<string, boolean>>({});

  const foodsToAvoidByCategory = (nutritionSafety?.foodsToAvoid || []).reduce<Record<string, FoodSafetyItem[]>>(
    (acc, item) => {
      (acc[item.category] = acc[item.category] || []).push(item);
      return acc;
    },
    {}
  );

  const handleOpenSafetyHandbookModal = () => {
    setShowSafetyHandbookModal(true);
    onOpenSafetyHandbook();
  };

  const handleGenerateWeeklyPlanClick = async () => {
    setWeeklyPlanError(null);
    try {
      await onGenerateWeeklyMealPlan();
    } catch (err) {
      setWeeklyPlanError(err instanceof Error ? err.message : "Đã có lỗi xảy ra, vui lòng thử lại.");
    }
  };

  const handleRegenerateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setWeeklyPlanError(null);
    try {
      await onGenerateWeeklyMealPlan(regenerateFeedback.trim() || undefined);
      setShowRegenerateModal(false);
      setRegenerateFeedback("");
    } catch (err) {
      setWeeklyPlanError(err instanceof Error ? err.message : "Đã có lỗi xảy ra, vui lòng thử lại.");
    }
  };

  const handleAcceptClick = async () => {
    setWeeklyPlanError(null);
    try {
      await onAcceptWeeklyMealPlan();
    } catch (err) {
      setWeeklyPlanError(err instanceof Error ? err.message : "Đã có lỗi xảy ra, vui lòng thử lại.");
    }
  };

  const toggleAvoidInfo = (name: string) => {
    setExpandedFoodInfo((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  return (
    <div className="space-y-6 relative min-h-screen pb-20" id="nutrition-view">

      {/* Page Header */}
      <div className="flex items-center gap-3">
        <h1 className="text-primary font-bold text-2xl tracking-tight">Dinh dưỡng AI</h1>
        <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-100 rounded-full text-[9px] font-bold">
          Đồng bộ Gia đình Hoạt động
        </span>
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

        {/* Cột Trái: An toàn thực phẩm & tiện ích (5 cols) */}
        <div className="lg:col-span-5 space-y-6">

          {/* Allergen Safety Panel & Warnings */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
            <h3 className="text-primary font-bold text-xs uppercase tracking-wide text-slate-500">
              Kiểm tra dị ứng & an toàn
            </h3>

            {/* High Alert Box - dựa trên hồ sơ dị ứng thật của bé */}
            {activeBaby.allergies && activeBaby.allergies.length > 0 ? (
              <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-r-2xl space-y-1.5 animate-pulse">
                <span className="text-[10px] font-bold text-red-800 uppercase tracking-wider flex items-center gap-1">
                  ⚠️ Dị ứng đã ghi nhận
                </span>
                <p className="text-[11px] text-red-700 leading-relaxed font-semibold">
                  {activeBaby.name} có dị ứng với: {activeBaby.allergies.join(", ")}. Tránh các món chứa thành phần này và tham khảo ý kiến bác sĩ.
                </p>
              </div>
            ) : (
              <div className="p-4 bg-slate-50 border-l-4 border-slate-200 rounded-r-2xl">
                <p className="text-[11px] text-slate-500 leading-relaxed font-semibold">
                  Chưa ghi nhận dị ứng nào cho {activeBaby.name}.
                </p>
              </div>
            )}

            {/* Foods to Avoid - lấy từ backend, tính đúng theo tuổi thật của bé */}
            {!nutritionSafety ? (
              <p className="text-[11px] text-slate-400 font-semibold text-center py-2">Đang tải hướng dẫn an toàn…</p>
            ) : (
              Object.entries(foodsToAvoidByCategory).map(([category, items]) => (
                <div key={category} className="space-y-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    {SAFETY_CATEGORY_LABELS[category] || "Thực phẩm cần lưu ý"}
                  </span>

                  <div className="space-y-2">
                    {items.map((food) => (
                      <div key={food.name} className="bg-white/40 border border-white/20 rounded-xl p-2.5 space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-700">{food.name}</span>
                          <button
                            onClick={() => toggleAvoidInfo(food.name)}
                            className="text-slate-400 hover:text-slate-600 cursor-pointer"
                            title="Xem lý do"
                          >
                            <Info className="w-4 h-4 text-primary" />
                          </button>
                        </div>

                        <AnimatePresence>
                          {expandedFoodInfo[food.name] && (
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
              ))
            )}

            {/* View Full Safety Guide Button */}
            <button
              onClick={handleOpenSafetyHandbookModal}
              className="w-full inline-flex items-center justify-center gap-1.5 bg-blue-50 hover:bg-blue-100 border border-blue-100 text-blue-700 text-[10px] font-bold py-2 rounded-xl transition-all cursor-pointer"
            >
              <BookOpen className="w-4.5 h-4.5 text-blue-600" />
              Xem toàn bộ Hướng dẫn An toàn
            </button>
          </div>

        </div>

        {/* Cột Phải: Gợi ý dinh dưỡng AI (7 cols) */}
        <div className="lg:col-span-7 space-y-6">

          {/* AI Meal Plan Widget - gợi ý dinh dưỡng cá nhân hoá theo dị ứng/bệnh lý của bé */}
          <div className="bg-[#ecfdf5]/80 backdrop-blur-xl border border-emerald-100/60 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-emerald-500/10">
              <h3 className="text-emerald-950 font-bold text-xs uppercase tracking-wide flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-emerald-600" />
                Gợi ý dinh dưỡng từ AI
              </h3>
              {recommendation && (
                <button
                  onClick={() => onGenerateRecommendation()}
                  disabled={isGeneratingRecommendation}
                  className="text-[9px] bg-emerald-100 hover:bg-emerald-200 text-emerald-700 font-bold px-1.5 py-0.5 rounded-md uppercase transition-colors cursor-pointer disabled:opacity-60"
                >
                  {isGeneratingRecommendation ? "Đang làm mới…" : "Làm mới"}
                </button>
              )}
            </div>

            {isGeneratingRecommendation && !recommendation && (
              <div className="text-center py-6 space-y-2">
                <RefreshCw className="w-5 h-5 text-emerald-600 animate-spin mx-auto" />
                <p className="text-[11px] text-emerald-700 font-semibold">Đang phân tích hồ sơ của bé…</p>
              </div>
            )}

            {!isGeneratingRecommendation && !recommendation && (
              <div className="text-center py-4 space-y-3">
                <p className="text-[11px] text-emerald-800/80 font-semibold">
                  Chưa có gợi ý dinh dưỡng nào. Tạo gợi ý cá nhân hoá theo dị ứng và bệnh lý của {activeBaby.name}.
                </p>
                <button
                  onClick={() => onGenerateRecommendation()}
                  className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-bold px-3.5 py-2 rounded-xl transition-all cursor-pointer"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  Tạo gợi ý dinh dưỡng AI
                </button>
              </div>
            )}

            {recommendation && (
              <div className="space-y-4">
                <p className="text-[11px] text-emerald-900/80 font-semibold leading-relaxed">
                  {recommendation.summary}
                </p>

                {recommendation.recommendedFoods.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[9px] font-bold text-emerald-700 uppercase tracking-wider block">Nên ăn</span>
                    {recommendation.recommendedFoods.map((food, rIdx) => (
                      <div key={rIdx} className="bg-white/80 rounded-2xl p-3 space-y-1 border border-emerald-100/40">
                        <span className="text-xs font-bold text-slate-800">{food.foodName}</span>
                        <p className="text-[10px] text-slate-500 font-semibold leading-relaxed">{food.reason}</p>
                      </div>
                    ))}
                  </div>
                )}

                {recommendation.foodsToAvoid.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[9px] font-bold text-red-600 uppercase tracking-wider block">Nên tránh</span>
                    {recommendation.foodsToAvoid.map((food, aIdx) => (
                      <div key={aIdx} className="bg-white/80 rounded-2xl p-3 space-y-1 border border-red-100/60">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-800">{food.foodName}</span>
                          <span className="text-[9px] bg-red-50 text-red-600 font-bold px-1.5 py-0.2 rounded-md">
                            {food.linkedTo}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-500 font-semibold leading-relaxed">{food.reason}</p>
                      </div>
                    ))}
                  </div>
                )}

                <p className="text-[9px] text-emerald-700/70 font-semibold">
                  Cập nhật lúc {new Date(recommendation.generatedAt).toLocaleString("vi-VN")}
                </p>
              </div>
            )}
          </div>

        </div>

      </div>

      {/* Thực đơn ăn dặm 7 ngày AI (RAG) - trạng thái pending/accepted, khoá tạo mới 7 ngày sau khi chấp nhận */}
      <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-white/20 pb-2">
          <h3 className="text-primary font-bold text-sm tracking-tight flex items-center gap-1.5">
            <Calendar className="w-4.5 h-4.5 text-primary" />
            Thực đơn ăn dặm 7 ngày AI
          </h3>
          {weeklyMealPlan && (
            <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase ${
              weeklyMealPlan.status === "accepted" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
            }`}>
              {weeklyMealPlan.status === "accepted" ? "Đã chấp nhận" : "Chờ duyệt"}
            </span>
          )}
        </div>

        {weeklyPlanError && (
          <div className="px-4 py-2.5 rounded-xl bg-red-50 border border-red-100 text-red-600 text-xs font-semibold">
            {weeklyPlanError}
          </div>
        )}

        {isGeneratingWeeklyPlan && !weeklyMealPlan && (
          <div className="text-center py-8 space-y-2">
            <RefreshCw className="w-5 h-5 text-primary animate-spin mx-auto" />
            <p className="text-[11px] text-slate-500 font-semibold">Đang lên thực đơn 7 ngày cho bé…</p>
          </div>
        )}

        {!isGeneratingWeeklyPlan && !weeklyMealPlan && (
          <div className="text-center py-6 space-y-3">
            <p className="text-[11px] text-slate-500 font-semibold">
              Chưa có thực đơn 7 ngày nào. Tạo thực đơn cá nhân hoá theo dị ứng và bệnh lý của {activeBaby.name}.
            </p>
            <button
              onClick={handleGenerateWeeklyPlanClick}
              className="inline-flex items-center gap-1.5 bg-primary hover:bg-primary/95 text-white text-[11px] font-bold px-3.5 py-2 rounded-xl transition-all cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Tạo thực đơn 7 ngày AI
            </button>
          </div>
        )}

        {weeklyMealPlan && (
          <div className="space-y-4">
            <p className="text-[11px] text-slate-600 font-semibold leading-relaxed">{weeklyMealPlan.summary}</p>

            {weeklyMealPlan.status === "accepted" && daysUntil(weeklyMealPlan.endDate) >= 0 && (
              <div className="px-3.5 py-2 bg-emerald-50 border border-emerald-100 rounded-xl text-[11px] text-emerald-700 font-semibold">
                Đang áp dụng đến {formatShortDate(weeklyMealPlan.endDate)} — còn {daysUntil(weeklyMealPlan.endDate)} ngày nữa mới có thể tạo thực đơn mới.
              </div>
            )}

            {/* Lịch 7 ngày dạng grid, cuộn ngang trên màn hình nhỏ */}
            <div className="overflow-x-auto">
              <div className="grid gap-2 min-w-[720px]" style={{ gridTemplateColumns: `80px repeat(${weeklyMealPlan.days.length}, 1fr)` }}>
                <div />
                {weeklyMealPlan.days.map((day) => (
                  <div key={day.date} className="text-center text-[10px] font-bold text-slate-500 uppercase pb-1">
                    {formatShortDate(day.date)}
                  </div>
                ))}

                {MEAL_TYPE_ORDER.map((mealType) => (
                  <React.Fragment key={mealType}>
                    <div className="flex items-center text-[10px] font-bold text-slate-400 uppercase">
                      {MEAL_TYPE_LABELS[mealType]}
                    </div>
                    {weeklyMealPlan.days.map((day) => {
                      const meal = day.meals.find((m) => m.mealType.toLowerCase() === mealType);
                      return (
                        <div key={`${day.date}-${mealType}`} className="bg-white/60 border border-white/30 rounded-xl p-2 space-y-0.5 min-h-[56px]">
                          {meal ? (
                            <>
                              <p className="text-[10px] font-bold text-slate-700 leading-tight">{meal.foodName}</p>
                              {meal.note && <p className="text-[9px] text-slate-400 leading-tight">{meal.note}</p>}
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

            {/* Hành động theo trạng thái */}
            {weeklyMealPlan.status === "pending" && (
              <div className="flex items-center gap-2 pt-2">
                <button
                  onClick={handleAcceptClick}
                  disabled={isAcceptingWeeklyPlan}
                  className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-bold px-3.5 py-2 rounded-xl transition-all cursor-pointer disabled:opacity-60"
                >
                  <Check className="w-3.5 h-3.5" />
                  {isAcceptingWeeklyPlan ? "Đang xử lý…" : "Chấp nhận"}
                </button>
                <button
                  onClick={() => setShowRegenerateModal(true)}
                  disabled={isGeneratingWeeklyPlan}
                  className="inline-flex items-center gap-1.5 bg-white/60 hover:bg-white/80 border border-white/30 text-slate-700 text-[11px] font-bold px-3.5 py-2 rounded-xl transition-all cursor-pointer disabled:opacity-60"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isGeneratingWeeklyPlan ? "animate-spin" : ""}`} />
                  {isGeneratingWeeklyPlan ? "Đang tạo lại…" : "Tạo lại"}
                </button>
              </div>
            )}

            {weeklyMealPlan.status === "accepted" && daysUntil(weeklyMealPlan.endDate) < 0 && (
              <div className="pt-2">
                <button
                  onClick={() => setShowRegenerateModal(true)}
                  disabled={isGeneratingWeeklyPlan}
                  className="inline-flex items-center gap-1.5 bg-primary hover:bg-primary/95 text-white text-[11px] font-bold px-3.5 py-2 rounded-xl transition-all cursor-pointer disabled:opacity-60"
                >
                  <Sparkles className={`w-3.5 h-3.5 ${isGeneratingWeeklyPlan ? "animate-spin" : ""}`} />
                  {isGeneratingWeeklyPlan ? "Đang tạo…" : "Tạo thực đơn mới"}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

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
                  <p className="text-[10px] text-slate-400 font-semibold normal-case">
                    AI sẽ điều chỉnh thực đơn mới theo phản hồi này, để trống nếu chỉ muốn tạo thực đơn khác.
                  </p>
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
                      className={`border rounded-2xl p-3.5 space-y-1.5 ${HANDBOOK_LEVEL_STYLES[section.level] || HANDBOOK_LEVEL_STYLES.info}`}
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
