import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  AlertCircle,
  Plus,
  RefreshCw,
  Clock,
  Pill,
  Droplet,
  Trash2,
  Check,
  ChevronRight,
  TrendingUp,
  Shield,
  Activity,
  Heart,
  Thermometer,
  Eye,
  FileText
} from "lucide-react";
import { BabyProfile, MedicationLog } from "../types";

interface HealthViewProps {
  activeBaby: BabyProfile;
  medications: MedicationLog[];
  onAddMedication: (med: Omit<MedicationLog, "id">) => void;
  onDeleteMedication: (id: string) => void;
}

interface IncidentRecord {
  id: string;
  title: string;
  date: string;
  time: string;
  status: "Confirmed" | "Resolved";
  symptoms: string[];
  treatment: string;
  prescribedBy: string;
}

export default function HealthView({
  activeBaby,
  medications,
  onAddMedication,
  onDeleteMedication
}: HealthViewProps) {
  // Incident logs state
  const [incidents, setIncidents] = useState<IncidentRecord[]>([
    {
      id: "inc1",
      title: "Viêm họng cấp tính",
      date: "Hôm nay",
      time: "08:15 AM",
      status: "Confirmed",
      symptoms: ["🌡️ Sốt 38.8°C", "🌬️ Ho khan", "🥵 Đau họng"],
      treatment: "Paracetamol 150mg mỗi 6 giờ, giọt Vitamin D3, uống nước ấm. Giữ độ ẩm phòng trên 55%.",
      prescribedBy: "Bác sĩ nhi khoa Aris"
    },
    {
      id: "inc2",
      title: "Kích ứng mọc răng nhẹ",
      date: "Hôm qua",
      time: "04:30 PM",
      status: "Resolved",
      symptoms: ["🦷 Chảy nước dãi", "🥱 Giấc ngủ gián đoạn"],
      treatment: "Dùng ngậm nướu lạnh, mát-xa nướu nhẹ nhàng, theo dõi nhiệt độ.",
      prescribedBy: "Phụ huynh ghi nhận"
    }
  ]);

  // Symptom filter state
  const [selectedSymptomFilter, setSelectedSymptomFilter] = useState<string | null>(null);

  // Form states for adding incidents
  const [showAddIncident, setShowAddIncident] = useState(false);
  const [incidentTitle, setIncidentTitle] = useState("");
  const [incidentSymptoms, setIncidentSymptoms] = useState("");
  const [incidentTreatment, setIncidentTreatment] = useState("");
  const [incidentDoctor, setIncidentDoctor] = useState("");

  // Form states for adding medications
  const [showAddMed, setShowAddMed] = useState(false);
  const [medName, setMedName] = useState("");
  const [medDosage, setMedDosage] = useState("");
  const [medDoctor, setMedDoctor] = useState("Dr. Aris");

  // Countdown timer for next dose (Paracetamol) - e.g. next allowed is 6 hours from last admin
  const [countdownSeconds, setCountdownSeconds] = useState(3600 * 3.5); // 3.5 hours default countdown

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdownSeconds((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatCountdown = (totalSecs: number) => {
    const hrs = Math.floor(totalSecs / 3600);
    const mins = Math.floor((totalSecs % 3600) / 60);
    const secs = totalSecs % 60;
    return `${String(hrs).padStart(2, "0")}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  const handleAddIncidentSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!incidentTitle) return;

    const symptomsList = incidentSymptoms
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    const newRecord: IncidentRecord = {
      id: `inc_${Date.now()}`,
      title: incidentTitle,
      date: "Today",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      status: "Confirmed",
      symptoms: symptomsList.length ? symptomsList : ["General Discomfort"],
      treatment: incidentTreatment || "Rest and general observation.",
      prescribedBy: incidentDoctor || "Caregiver Logged"
    };

    setIncidents((prev) => [newRecord, ...prev]);
    setShowAddIncident(false);
    setIncidentTitle("");
    setIncidentSymptoms("");
    setIncidentTreatment("");
    setIncidentDoctor("");
  };

  const handleAddMedSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!medName || !medDosage) return;

    onAddMedication({
      babyId: activeBaby.id,
      name: medName,
      dosage: medDosage,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      date: "Today",
      prescribedBy: medDoctor || "Self Supplement"
    });

    setShowAddMed(false);
    setMedName("");
    setMedDosage("");
    // Reset countdown timer to 6 hours for new dose
    if (medName.toLowerCase().includes("hapacol") || medName.toLowerCase().includes("paracetamol")) {
      setCountdownSeconds(3600 * 6);
    }
  };

  // Collect all unique symptoms from incidents to build filter tabs
  const allSymptoms = Array.from(new Set(incidents.flatMap((i) => i.symptoms)));

  const filteredIncidents = selectedSymptomFilter
    ? incidents.filter((inc) => inc.symptoms.includes(selectedSymptomFilter))
    : incidents;

  return (
    <div className="space-y-6" id="health-view">
      
      {/* A. Safety Alert Banner (Top) */}
      <div className="bg-red-50 border-l-4 border-red-500 rounded-r-2xl p-4 flex items-start gap-3 shadow-xs animate-pulse">
        <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <h4 className="text-xs font-bold text-red-800">CẢNH BÁO AN TOÀN: KHOẢNG CÁCH LIỀU DÙNG THUỐC</h4>
          <p className="text-[11px] text-red-700 leading-relaxed font-semibold">
            Paracetamol (Hapacol 150mg) yêu cầu khoảng cách liều tối thiểu từ 4-6 giờ giữa các lần uống. Ghi nhận hiện tại cho thấy liều gần nhất vừa được dùng quá gần đây. Luôn tham khảo ý kiến bác sĩ nhi khoa trước khi cho bé dùng thêm thuốc hạ sốt.
          </p>
        </div>
      </div>

      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-primary font-bold text-2xl tracking-tight">Nhật ký Sức khỏe</h1>
          <p className="text-xs text-slate-500 font-semibold mt-0.5">
            Theo dõi các triệu chứng, đơn thuốc và khoảng cách liều dùng thuốc an toàn của {activeBaby.name}.
          </p>
        </div>
        <div className="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 border border-emerald-100 rounded-full px-3 py-1 text-xs font-bold shadow-xs">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
          Đồng bộ Gia đình thời gian thực hoạt động
        </div>
      </div>

      {/* B. Columns Layout (65% / 35%) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Medical Incident Timeline (65%) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Timeline Header & Filters */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-primary font-bold text-sm tracking-tight flex items-center gap-1.5">
                  <Activity className="w-4.5 h-4.5 text-primary" />
                  Triệu chứng & Bệnh án nhi khoa
                </h3>
                <p className="text-[10px] text-slate-400 mt-0.5 font-semibold">Nhật ký theo dõi sức khỏe từ khi sinh ra</p>
              </div>

              <button
                onClick={() => setShowAddIncident(true)}
                className="inline-flex items-center gap-1 bg-sky-100 hover:bg-sky-200 text-sky-700 border border-sky-100 rounded-full px-4 py-2 text-xs font-bold transition-all cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                Thêm bệnh án mới
              </button>
            </div>

            {/* Quick symptom filter pill buttons */}
            <div className="flex flex-wrap items-center gap-2 pt-2">
              <button
                onClick={() => setSelectedSymptomFilter(null)}
                className={`px-3 py-1 rounded-full border text-[10px] font-bold transition-all cursor-pointer ${
                  selectedSymptomFilter === null
                    ? "bg-primary border-primary text-white"
                    : "bg-white/40 border-white/20 text-slate-500 hover:text-slate-700"
                }`}
              >
                Tất cả triệu chứng
              </button>
              {allSymptoms.map((symp, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedSymptomFilter(symp)}
                  className={`px-3 py-1 rounded-full border text-[10px] font-bold transition-all cursor-pointer ${
                    selectedSymptomFilter === symp
                      ? "bg-primary border-primary text-white"
                      : "bg-white/40 border-white/20 text-slate-500 hover:text-slate-700"
                  }`}
                >
                  {symp}
                </button>
              ))}
            </div>

            {/* Medical incident cards */}
            <div className="space-y-4 pt-2">
              {filteredIncidents.map((inc) => (
                <div
                  key={inc.id}
                  className="bg-white/70 border border-white/40 rounded-2xl p-5 shadow-xs relative space-y-3 group"
                >
                  {/* Status indicator badge */}
                  <span
                    className={`absolute top-5 right-5 text-[9px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider ${
                      inc.status === "Confirmed"
                        ? "bg-rose-50 border border-rose-100 text-rose-600 animate-pulse"
                        : "bg-emerald-50 border border-emerald-100 text-emerald-600"
                    }`}
                  >
                    {inc.status === "Confirmed" ? "Đang theo dõi" : "Đã khỏi"}
                  </span>

                  <div className="space-y-1">
                    <span className="text-[10px] text-slate-400 font-bold">{inc.date === "Today" ? "Hôm nay" : inc.date === "Yesterday" ? "Hôm qua" : inc.date} • {inc.time}</span>
                    <h4 className="text-sm font-black text-slate-800">{inc.title}</h4>
                  </div>

                  {/* Symptom pills */}
                  <div className="flex flex-wrap gap-1.5">
                    {inc.symptoms.map((sym, sIdx) => (
                      <span
                        key={sIdx}
                        className="px-2 py-0.5 bg-slate-100 border border-slate-200 text-slate-600 rounded-lg text-[9px] font-bold"
                      >
                        {sym}
                      </span>
                    ))}
                  </div>

                  {/* Nested light blue treatment plan block */}
                  <div className="p-3 bg-blue-50/50 border border-blue-100 rounded-xl space-y-1.5">
                    <h5 className="text-[10px] font-bold text-blue-800 uppercase tracking-wide">
                      📋 Hướng điều trị & Lời khuyên của bác sĩ
                    </h5>
                    <p className="text-[11px] text-blue-700 leading-relaxed font-semibold">
                      {inc.treatment}
                    </p>
                    <span className="text-[9px] font-bold text-blue-500 block">
                      Nguồn: {inc.prescribedBy}
                    </span>
                  </div>
                </div>
              ))}

              {filteredIncidents.length === 0 && (
                <div className="text-center py-8 text-slate-400 text-xs">
                  Không tìm thấy ghi chép sức khỏe nào khớp bộ lọc.
                </div>
              )}
            </div>
          </div>

        </div>

        {/* Right Column: Medication Management (35%) */}
        <div className="space-y-6">
          
          {/* Next Dose Countdown Card */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-5 space-y-4 text-center">
            <div className="space-y-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Độ an toàn cho liều tiếp theo
              </span>
              <h3 className="text-primary font-bold text-sm">Hapacol 150mg (Paracetamol)</h3>
            </div>

            {/* Countdown Display */}
            <div className="bg-slate-50 border border-slate-200 rounded-2xl py-4 font-mono font-bold text-3xl text-slate-700 tracking-wider">
              {countdownSeconds > 0 ? formatCountdown(countdownSeconds) : "00:00:00"}
            </div>

            <p className="text-[10px] text-slate-400 font-semibold px-2">
              {countdownSeconds > 0
                ? "CẢNH BÁO: Không sử dụng thuốc quá sớm để tránh quá liều acetaminophen gây độc cho gan của bé."
                : "Khoảng cách liều dùng đã an toàn. Có thể cho bé dùng liều tiếp theo nếu triệu chứng sốt kéo dài."}
            </p>

            {/* Disabled / Active DO NOT ADMINISTER Button */}
            <button
              disabled={countdownSeconds > 0}
              className={`w-full py-2.5 rounded-xl font-bold transition-all text-xs cursor-pointer shadow-md ${
                countdownSeconds > 0
                  ? "bg-red-100 text-red-500 cursor-not-allowed border border-red-200 shadow-none font-extrabold"
                  : "bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/10"
              }`}
            >
              {countdownSeconds > 0 ? "⚠️ KHÔNG ĐƯỢC CHO UỐNG" : "✓ CÓ THỂ CHO UỐNG BÂY GIỜ"}
            </button>
          </div>

          {/* Recent Doses List */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/20 pb-2">
              <h3 className="text-primary font-bold text-xs uppercase tracking-wide text-slate-500">
                Nhật ký dùng thuốc gần đây
              </h3>
              <button
                onClick={() => setShowAddMed(true)}
                className="text-[10px] font-bold text-primary hover:underline cursor-pointer"
              >
                + Ghi nhận liều dùng
              </button>
            </div>

            <div className="space-y-2.5">
              {medications.map((med) => {
                const isLiquid = med.dosage.toLowerCase().includes("drop") || med.dosage.toLowerCase().includes("ml") || med.dosage.toLowerCase().includes("giọt");
                const Icon = isLiquid ? Droplet : Pill;
                const iconColor = isLiquid ? "text-sky-500 bg-sky-50" : "text-purple-500 bg-purple-50";

                return (
                  <div
                    key={med.id}
                    className="p-3 bg-white/40 border border-white/20 rounded-2xl flex items-center justify-between gap-3 shadow-xs hover:bg-white/80 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-xl ${iconColor}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h4 className="text-xs font-bold text-slate-700">{med.name}</h4>
                        <span className="text-[9px] text-slate-400 font-semibold">
                          {med.dosage} • {med.time} ({med.date === "Today" ? "Hôm nay" : med.date})
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={() => onDeleteMedication(med.id)}
                      className="text-slate-400 hover:text-rose-500 transition-colors cursor-pointer"
                      title="Xóa nhật ký dùng thuốc"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })}

              {medications.length === 0 && (
                <div className="text-center py-6 text-slate-400 text-xs">
                  Không có nhật ký dùng thuốc nào hôm nay.
                </div>
              )}
            </div>

            {/* View Medication History Outlined button */}
            <button className="w-full inline-flex items-center justify-center gap-1 border border-dashed border-slate-300 text-slate-500 hover:text-slate-800 text-[10px] font-bold py-2 rounded-xl transition-colors cursor-pointer">
              <FileText className="w-3.5 h-3.5" />
              Xem lịch sử dùng thuốc
            </button>
          </div>

        </div>

      </div>

      {/* --- ADD RECORD MODALS --- */}
      <AnimatePresence>
        {showAddIncident && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-black text-slate-800">Ghi chép bệnh trạng mới</h3>
                <button onClick={() => setShowAddIncident(false)} className="text-xs font-bold text-slate-400 hover:text-slate-600 cursor-pointer">
                  Hủy
                </button>
              </div>

              <form onSubmit={handleAddIncidentSubmit} className="space-y-4 text-xs font-bold text-slate-600">
                <div className="space-y-1">
                  <label className="block">Tên bệnh / Triệu chứng</label>
                  <input
                    type="text"
                    required
                    value={incidentTitle}
                    onChange={(e) => setIncidentTitle(e.target.value)}
                    placeholder="Ví dụ: Sốt cao, Phát ban, Viêm họng cấp"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 font-medium"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block">Các triệu chứng (cách nhau bằng dấu phẩy)</label>
                  <input
                    type="text"
                    value={incidentSymptoms}
                    onChange={(e) => setIncidentSymptoms(e.target.value)}
                    placeholder="Ví dụ: Sốt 38.5 độ, sổ mũi, ho"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 font-medium"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block">Hướng dẫn điều trị</label>
                  <textarea
                    value={incidentTreatment}
                    onChange={(e) => setIncidentTreatment(e.target.value)}
                    placeholder="Ví dụ: Uống 150mg paracetamol, chườm ấm"
                    rows={2}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 font-medium resize-none"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block">Bác sĩ điều trị / Nguồn kê đơn</label>
                  <input
                    type="text"
                    value={incidentDoctor}
                    onChange={(e) => setIncidentDoctor(e.target.value)}
                    placeholder="Ví dụ: Bác sĩ nhi khoa"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 font-medium"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-white py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer"
                >
                  Lưu Nhật ký bệnh trạng
                </button>
              </form>
            </motion.div>
          </div>
        )}

        {showAddMed && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-black text-slate-800">Ghi nhận liều dùng thuốc</h3>
                <button onClick={() => setShowAddMed(false)} className="text-xs font-bold text-slate-400 hover:text-slate-600 cursor-pointer">
                  Hủy
                </button>
              </div>

              <form onSubmit={handleAddMedSubmit} className="space-y-4 text-xs font-bold text-slate-600">
                <div className="space-y-1">
                  <label className="block">Tên thuốc</label>
                  <input
                    type="text"
                    required
                    value={medName}
                    onChange={(e) => setMedName(e.target.value)}
                    placeholder="Ví dụ: Hapacol 150mg"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 font-medium"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block">Liều lượng</label>
                  <input
                    type="text"
                    required
                    value={medDosage}
                    onChange={(e) => setMedDosage(e.target.value)}
                    placeholder="Ví dụ: 150mg, 2 giọt, 5ml"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 font-medium"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block">Người kê đơn</label>
                  <input
                    type="text"
                    value={medDoctor}
                    onChange={(e) => setMedDoctor(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 font-medium"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-white py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer"
                >
                  Lưu Nhật ký dùng thuốc
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
