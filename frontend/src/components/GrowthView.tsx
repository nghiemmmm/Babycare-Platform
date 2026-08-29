import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";
import { Scale, Ruler, Brain, Plus, Activity, AlertCircle, ChevronRight, Check } from "lucide-react";
import { BabyProfile, Measurement } from "../types";

interface GrowthViewProps {
  activeBaby: BabyProfile;
  measurements: Measurement[];
  onAddMeasurement: (m: Omit<Measurement, "id">) => void;
  onDeleteMeasurement: (id: string) => void;
}

// Static WHO standard median reference data (0-12 months) for boys & girls
const WHO_BOY_STANDARDS = [
  { month: 0, weightMedian: 3.3, heightMedian: 49.9, weight3rd: 2.4, weight97th: 4.3, height3rd: 46.1, height97th: 53.7 },
  { month: 2, weightMedian: 5.6, heightMedian: 58.4, weight3rd: 4.3, weight97th: 7.1, height3rd: 54.4, height97th: 62.4 },
  { month: 4, weightMedian: 7.0, heightMedian: 63.9, weight3rd: 5.6, weight97th: 8.7, height3rd: 60.1, height97th: 67.8 },
  { month: 6, weightMedian: 7.9, heightMedian: 67.6, weight3rd: 6.4, weight97th: 9.8, height3rd: 63.6, height97th: 71.6 },
  { month: 8, weightMedian: 8.6, heightMedian: 70.6, weight3rd: 7.0, weight97th: 10.7, height3rd: 66.5, height97th: 74.7 },
  { month: 10, weightMedian: 9.2, heightMedian: 73.3, weight3rd: 7.5, weight97th: 11.4, height3rd: 69.0, height97th: 77.6 },
  { month: 12, weightMedian: 9.6, heightMedian: 75.7, weight3rd: 7.8, weight97th: 12.0, height3rd: 71.3, height97th: 80.2 },
];

const WHO_GIRL_STANDARDS = [
  { month: 0, weightMedian: 3.2, heightMedian: 49.1, weight3rd: 2.4, weight97th: 4.2, height3rd: 45.4, height97th: 52.9 },
  { month: 2, weightMedian: 5.1, heightMedian: 57.1, weight3rd: 3.9, weight97th: 6.6, height3rd: 53.2, height97th: 60.9 },
  { month: 4, weightMedian: 6.4, heightMedian: 62.1, weight3rd: 5.0, weight97th: 8.2, height3rd: 58.0, height97th: 66.2 },
  { month: 6, weightMedian: 7.3, heightMedian: 65.7, weight3rd: 5.7, weight97th: 9.3, height3rd: 61.2, height97th: 70.3 },
  { month: 8, weightMedian: 8.0, heightMedian: 68.7, weight3rd: 6.3, weight97th: 10.2, height3rd: 64.0, height97th: 73.5 },
  { month: 10, weightMedian: 8.5, heightMedian: 71.5, weight3rd: 6.7, weight97th: 10.9, height3rd: 66.5, height97th: 76.4 },
  { month: 12, weightMedian: 8.9, heightMedian: 74.0, weight3rd: 7.0, weight97th: 11.5, height3rd: 68.9, height97th: 79.2 },
];

export default function GrowthView({
  activeBaby,
  measurements,
  onAddMeasurement,
  onDeleteMeasurement,
}: GrowthViewProps) {
  const [metricToggle, setMetricToggle] = useState<"weight" | "height">("weight");
  const [selectedLog, setSelectedLog] = useState<Measurement | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  // New Measurement Form State
  const [date, setDate] = useState("");
  const [ageMonths, setAgeMonths] = useState(6);
  const [weight, setWeight] = useState(7.2);
  const [height, setHeight] = useState(66);
  const [headCirc, setHeadCirc] = useState(42.5);
  const [notes, setNotes] = useState("");

  const isBoy = activeBaby.gender !== "Girl";
  const whoRef = isBoy ? WHO_BOY_STANDARDS : WHO_GIRL_STANDARDS;

  // Compile data for Recharts chart
  const chartData = whoRef.map((ref) => {
    const matchedLog = measurements.find((m) => m.babyId === activeBaby.id && Math.abs(m.ageInMonths - ref.month) <= 0.5);
    
    return {
      monthName: ref.month === 0 ? "Birth" : `${ref.month}M`,
      month: ref.month,
      "WHO Median": metricToggle === "weight" ? ref.weightMedian : ref.heightMedian,
      "WHO 3rd Percentile": metricToggle === "weight" ? ref.weight3rd : ref.height3rd,
      "WHO 97th Percentile": metricToggle === "weight" ? ref.weight97th : ref.height97th,
      [activeBaby.name]: matchedLog ? (metricToggle === "weight" ? matchedLog.weight : matchedLog.height) : undefined,
    };
  });

  const babyMeasurements = measurements
    .filter((m) => m.babyId === activeBaby.id)
    .sort((a, b) => b.ageInMonths - a.ageInMonths);

  const latestMeasure = babyMeasurements[0] || null;

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    let status = "Normal";
    if (metricToggle === "height" || true) {
      const matchStandard = whoRef.find(r => r.month === Number(ageMonths)) || whoRef[3];
      if (height < (matchStandard.heightMedian - 1.5)) {
        status = "Height Alert (Risk of Stunting)";
      } else if (weight < (matchStandard.weightMedian - 1.5)) {
        status = "Weight Alert (Underweight)";
      }
    }

    onAddMeasurement({
      babyId: activeBaby.id,
      date: date || new Date().toISOString().split("T")[0],
      ageInMonths: Number(ageMonths),
      weight: Number(weight),
      height: Number(height),
      headCircumference: Number(headCirc),
      status,
      notes
    });

    setShowAddModal(false);
    setDate("");
    setNotes("");
  };

  return (
    <div className="space-y-6" id="growth-view">
      
      {/* View Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
            Theo dõi tăng trưởng WHO
          </h1>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            So sánh bách phân vị cân nặng, chiều cao và vòng đầu của bé với chuẩn Tổ chức Y tế Thế giới (WHO).
          </p>
        </div>
        <button
          onClick={() => {
            const today = new Date().toISOString().split("T")[0];
            setDate(today);
            setShowAddModal(true);
          }}
          className="inline-flex items-center gap-2 bg-primary hover:bg-primary/90 text-white px-6 py-2.5 rounded-full text-xs font-bold transition-all shadow-md shadow-primary/20 cursor-pointer"
          id="btn-add-measurement"
        >
          <Plus className="w-4 h-4" />
          Thêm số đo mới
        </button>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Weight Card */}
        <motion.div
          whileHover={{ y: -2 }}
          className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-5 flex items-center gap-4 relative overflow-hidden"
        >
          <div className={`p-3 rounded-xl ${latestMeasure?.status?.includes("Weight Alert") ? "bg-rose-50 text-rose-500" : "bg-emerald-50 text-emerald-600"}`}>
            <Scale className="w-6 h-6" />
          </div>
          <div className="space-y-0.5">
            <span className="text-xs text-slate-500 font-bold">Cân nặng hiện tại</span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-xl sm:text-2xl font-black text-slate-900">{latestMeasure ? `${latestMeasure.weight} kg` : "-- kg"}</span>
              <span className={`text-xs font-semibold ${latestMeasure?.status?.includes("Weight Alert") ? "text-rose-500" : "text-emerald-600"}`}>
                {latestMeasure ? (latestMeasure.status.includes("Weight Alert") ? "Dưới chuẩn WHO" : "Chuẩn WHO") : "Chưa có số đo"}
              </span>
            </div>
            <span className={`inline-flex items-center gap-1 text-xs font-bold px-2.5 py-0.5 rounded-full mt-1 ${latestMeasure?.status?.includes("Weight Alert") ? "bg-rose-50 text-rose-700" : "bg-emerald-50 text-emerald-700"}`}>
              {latestMeasure?.status?.includes("Weight Alert") ? <AlertCircle className="w-2.5 h-2.5" /> : <Check className="w-2.5 h-2.5" />}
              {latestMeasure ? (latestMeasure.status.includes("Weight Alert") ? "Cảnh báo Cân nặng (Nhẹ cân)" : "Bình thường (bách phân vị 50)") : "🌱 Bắt đầu theo dõi"}
            </span>
          </div>
        </motion.div>

        {/* Height Card */}
        <motion.div
          whileHover={{ y: -2 }}
          className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-5 flex items-center gap-4 relative overflow-hidden"
        >
          <div className={`p-3 rounded-xl ${latestMeasure?.status?.includes("Height Alert") ? "bg-rose-50 text-rose-500" : "bg-sky-50 text-sky-600"}`}>
            <Ruler className="w-6 h-6" />
          </div>
          <div className="space-y-0.5">
            <span className="text-xs text-slate-500 font-bold">Chiều cao hiện tại</span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-xl sm:text-2xl font-black text-slate-900">{latestMeasure ? `${latestMeasure.height} cm` : "-- cm"}</span>
              <span className={`text-xs font-semibold ${latestMeasure?.status?.includes("Height Alert") ? "text-rose-500" : "text-slate-400"}`}>
                {latestMeasure ? (latestMeasure.status.includes("Height Alert") ? "Dưới chuẩn WHO" : "Chuẩn WHO") : "Chưa có số đo"}
              </span>
            </div>
            <span className={`inline-flex items-center gap-1 text-xs font-bold px-2.5 py-0.5 rounded-full mt-1 ${latestMeasure?.status?.includes("Height Alert") ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-sky-700"}`}>
              {latestMeasure?.status?.includes("Height Alert") ? <AlertCircle className="w-2.5 h-2.5" /> : <Check className="w-2.5 h-2.5" />}
              {latestMeasure ? (latestMeasure.status.includes("Height Alert") ? "Cảnh báo Chiều cao (Nguy cơ thấp còi)" : "Phát triển tốt") : "🌱 Bắt đầu theo dõi"}
            </span>
          </div>
        </motion.div>

        {/* Head Circumference Card */}
        <motion.div
          whileHover={{ y: -2 }}
          className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-5 flex items-center gap-4 relative overflow-hidden"
        >
          <div className="p-3 bg-indigo-50 rounded-xl text-indigo-500">
            <Brain className="w-6 h-6" />
          </div>
          <div className="space-y-0.5">
            <span className="text-xs text-slate-500 font-bold">Vòng đầu hiện tại</span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-xl sm:text-2xl font-black text-slate-900">{latestMeasure ? `${latestMeasure.headCircumference} cm` : "-- cm"}</span>
              <span className="text-xs text-[#1c648e] font-semibold">{latestMeasure ? "Tăng trưởng đều đặn" : "Chưa có số đo"}</span>
            </div>
            <span className="inline-flex items-center gap-1 text-xs bg-indigo-50 text-indigo-700 font-bold px-2.5 py-0.5 rounded-full mt-1">
              <Check className="w-2.5 h-2.5" /> {latestMeasure ? "Bình thường" : "🌱 Bắt đầu theo dõi"}
            </span>
          </div>
        </motion.div>
      </div>

      {/* Chart and History Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Growth Chart Panel */}
        <div className="lg:col-span-2 bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
                <Activity className="w-4 h-4 text-primary" />
                Phân tích biểu đồ tăng trưởng
              </h3>
              <p className="text-xs text-slate-500 font-medium">So sánh kết quả của {activeBaby.name} với chuẩn WHO cho {activeBaby.gender === "Girl" ? "bé gái" : "bé trai"} (0-12 Tháng)</p>
            </div>

            {/* Metric Toggle Buttons */}
            <div className="inline-flex rounded-full p-0.5 bg-white/40 border border-white/20 self-start sm:self-center">
              <button
                onClick={() => setMetricToggle("weight")}
                className={`px-4 py-1.5 text-xs font-semibold rounded-full transition-colors cursor-pointer ${
                  metricToggle === "weight" ? "bg-primary text-white" : "text-slate-500 hover:text-slate-800"
                }`}
              >
                Cân nặng (kg)
              </button>
              <button
                onClick={() => setMetricToggle("height")}
                className={`px-4 py-1.5 text-xs font-semibold rounded-full transition-colors cursor-pointer ${
                  metricToggle === "height" ? "bg-primary text-white" : "text-slate-500 hover:text-slate-800"
                }`}
              >
                Chiều cao (cm)
              </button>
            </div>
          </div>

          {/* Chart Container */}
          <div className="h-[280px] w-full text-xs">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="monthName" stroke="#94a3b8" fontSize={11} />
                <YAxis
                  stroke="#94a3b8"
                  fontSize={11}
                  domain={metricToggle === "weight" ? [2, 13] : [44, 82]}
                />
                <Tooltip
                  contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0", backgroundColor: "rgba(255, 255, 255, 0.9)" }}
                  labelStyle={{ fontSize: "10px", fontWeight: "bold", color: "#1c648e" }}
                  itemStyle={{ fontSize: "10px", padding: "1px 0" }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                
                <Line
                  type="monotone"
                  dataKey="WHO 97th Percentile"
                  stroke="#fda4af"
                  strokeDasharray="4 4"
                  strokeWidth={1.2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="WHO Median"
                  stroke="#7cb9e8"
                  strokeDasharray="5 5"
                  strokeWidth={1.5}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="WHO 3rd Percentile"
                  stroke="#fecdd3"
                  strokeDasharray="4 4"
                  strokeWidth={1.2}
                  dot={false}
                />
                
                <Line
                  type="monotone"
                  dataKey={activeBaby.name}
                  stroke="#1c648e"
                  strokeWidth={3}
                  dot={{ r: 5, strokeWidth: 1 }}
                  activeDot={{ r: 8 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* History & Details Sidebar */}
        <div className="space-y-6">
          
          {/* List of measurements */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-5 space-y-4">
            <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">Lịch sử đo đạc</h3>
            
            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
              {babyMeasurements.length === 0 ? (
                <div className="text-center text-slate-400 py-8 text-xs font-medium">
                  Chưa có nhật ký đo đạc nào. Hãy bấm "Thêm số đo mới" ở trên để theo dõi biểu đồ!
                </div>
              ) : (
                babyMeasurements.map((log) => (
                  <div
                    key={log.id}
                    onClick={() => setSelectedLog(log)}
                    className={`p-3 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                      selectedLog?.id === log.id
                        ? "bg-primary/10 border-primary/20"
                        : "bg-white/40 hover:bg-white/80 border-white/20"
                    }`}
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-700">{log.ageInMonths} Tháng</span>
                        <span className="text-[10px] text-slate-400 font-medium">{log.date}</span>
                      </div>
                      <p className="text-[11px] text-slate-500 font-mono">
                        {log.weight}kg | {log.height}cm | {log.headCircumference}cm
                      </p>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {log.status.includes("Alert") ? (
                        <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" title={log.status} />
                      ) : (
                        <span className="w-2 h-2 rounded-full bg-emerald-500" title="Normal" />
                      )}
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Details Panel */}
          {selectedLog && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-4 space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700">Phân tích chi tiết: {selectedLog.ageInMonths} Tháng</span>
                <button
                  onClick={() => onDeleteMeasurement(selectedLog.id)}
                  className="text-[10px] font-semibold text-rose-500 hover:underline cursor-pointer"
                >
                  Xóa bản ghi
                </button>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                {selectedLog.notes || "Không có nhật ký chi tiết cho giai đoạn tăng trưởng này."}
              </p>
              <div className="p-2.5 bg-white border border-slate-200 rounded-xl">
                <p className="text-[10px] font-bold text-primary uppercase tracking-wide">Tình trạng phát triển</p>
                <p className="text-xs text-slate-700 mt-0.5 font-medium">{selectedLog.status.replace("Height Alert (Risk of Stunting)", "Cảnh báo Chiều cao (Nguy cơ thấp còi)").replace("Weight Alert (Underweight)", "Cảnh báo Cân nặng (Nhẹ cân)").replace("Normal", "Bình thường")}</p>
              </div>
            </motion.div>
          )}

        </div>

      </div>

      {/* Add New Measurement Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-3xl max-w-md w-full p-6 shadow-xl space-y-4"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-800">Thêm nhật ký tăng trưởng mới</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-medium cursor-pointer"
              >
                Hủy
              </button>
            </div>

            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-600 block">Ngày đo</label>
                  <input
                    type="date"
                    required
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 focus:border-primary/40 focus:bg-white focus:outline-hidden rounded-xl px-3.5 py-2 text-sm text-slate-800 transition-colors"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-600 block">Tuổi (Tháng)</label>
                  <input
                    type="number"
                    min="0"
                    max="24"
                    required
                    value={ageMonths}
                    onChange={(e) => setAgeMonths(Number(e.target.value))}
                    className="w-full bg-slate-50 border border-slate-200 focus:border-primary/40 focus:bg-white focus:outline-hidden rounded-xl px-3.5 py-2 text-sm text-slate-800 transition-colors"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-600 block">Cân nặng (kg)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={weight}
                    onChange={(e) => setWeight(Number(e.target.value))}
                    className="w-full bg-slate-50 border border-slate-200 focus:border-primary/40 focus:bg-white focus:outline-hidden rounded-xl px-2 py-2 text-sm text-slate-800 text-center transition-colors"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-600 block">Chiều cao (cm)</label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={height}
                    onChange={(e) => setHeight(Number(e.target.value))}
                    className="w-full bg-slate-50 border border-slate-200 focus:border-primary/40 focus:bg-white focus:outline-hidden rounded-xl px-2 py-2 text-sm text-slate-800 text-center transition-colors"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-600 block">Vòng đầu (cm)</label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={headCirc}
                    onChange={(e) => setHeadCirc(Number(e.target.value))}
                    className="w-full bg-slate-50 border border-slate-200 focus:border-primary/40 focus:bg-white focus:outline-hidden rounded-xl px-2 py-2 text-sm text-slate-800 text-center transition-colors"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-600 block">Ghi chú bác sĩ / Ghi chú lâm sàng</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Ví dụ: Bé ngủ ngoan, kiểm tra mọc răng, nhận xét của bác sĩ..."
                  rows={3}
                  className="w-full bg-slate-50 border border-slate-200 focus:border-primary/40 focus:bg-white focus:outline-hidden rounded-xl px-3.5 py-2 text-sm text-slate-800 transition-colors resize-none"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-primary hover:bg-primary/90 text-white py-2.5 rounded-xl font-medium text-sm transition-colors shadow-sm cursor-pointer"
              >
                Lưu Nhật ký Tăng trưởng
              </button>
            </form>
          </motion.div>
        </div>
      )}

    </div>
  );
}
