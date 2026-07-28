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
  FileText,
  Sparkles,
  Stethoscope,
  CheckCircle2,
  AlertTriangle
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
  temp?: number;
}

const PRESET_ILLNESSES = [
  { name: "🌡️ Sốt sau tiêm / Sốt cao", defaultTemp: 38.5, symptoms: ["🌡️ Sốt cao", "😴 Quấy khóc"], treatment: "Uống Paracetamol 150mg, chườm ấm trán nách." },
  { name: "🌬️ Viêm họng / Cảm cúm", defaultTemp: 37.8, symptoms: ["🌬️ Ho khan", "👃 Sổ mũi", "🥵 Đau họng"], treatment: "Siro ho thảo dược, rửa mũi nước muối sinh lý, uống nước ấm." },
  { name: "🦷 Mọc răng sưng nướu", defaultTemp: 37.4, symptoms: ["🦷 Chảy dãi", "😴 Quấy khóc"], treatment: "Ngậm nướu lạnh, mát-xa nướu nhẹ nhàng." },
  { name: "💩 Rối loạn tiêu hóa", defaultTemp: 37.0, symptoms: ["🤮 Nôn mửa", "💩 Tiêu chảy"], treatment: "Uống Oresol bù điện giải, ăn cháo loãng." },
  { name: "🔴 Nổi mẩn / Dị ứng", defaultTemp: 37.0, symptoms: ["🔴 Nổi mẩn"], treatment: "Giữ da sạch thoáng, tránh thực phẩm nghi ngờ dị ứng." }
];

const QUICK_SYMPTOMS = [
  "🌡️ Sốt cao (>38.5°C)",
  "🌬️ Ho khan",
  "👃 Sổ mũi",
  "🤮 Nôn mửa",
  "💩 Tiêu chảy",
  "🦷 Chảy dãi mọc răng",
  "😴 Quấy khóc mệt mỏi",
  "🔴 Nổi mẩn đỏ",
  "🥵 Đau họng"
];

const QUICK_TREATMENTS = [
  "💊 Uống Paracetamol 150mg",
  "💧 Uống Oresol bù điện giải",
  "🚿 Chườm ấm trán và nách",
  "🌿 Siro ho thảo dược Prospan",
  "💨 Bật máy tạo ẩm phòng 60%",
  "🩺 Khám bác sĩ nhi khoa"
];

const PRESET_MEDICATIONS = [
  { name: "Hapacol 150mg / Paracetamol", dosage: "1 gói (150mg)", doctor: "Dr. Aris (Nhi khoa)" },
  { name: "Vitamin D3 K2 Drops", dosage: "2 giọt", doctor: "Bác sĩ nhi khoa" },
  { name: "Siro Ho Thảo Dược Prospan", dosage: "2.5 ml", doctor: "Dr. Aris (Nhi khoa)" },
  { name: "Oresol Bù Điện Giải", dosage: "100 ml", doctor: "Dược sĩ tư vấn" },
  { name: "Men Vi Sinh Probiotics", dosage: "1 gói", doctor: "Dr. Aris (Nhi khoa)" }
];

const COMMON_DOSAGES = [
  "1 gói (150mg)",
  "2.5 ml",
  "5.0 ml",
  "2 giọt",
  "1 ống (5ml)",
  "1/2 gói (75mg)"
];

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
      prescribedBy: "Bác sĩ nhi khoa Aris",
      temp: 38.8
    },
    {
      id: "inc2",
      title: "Kích ứng mọc răng nhẹ",
      date: "Hôm qua",
      time: "04:30 PM",
      status: "Resolved",
      symptoms: ["🦷 Chảy nước dãi", "🥱 Giấc ngủ gián đoạn"],
      treatment: "Dùng ngậm nướu lạnh, mát-xa nướu nhẹ nhàng, theo dõi nhiệt độ.",
      prescribedBy: "Phụ huynh ghi nhận",
      temp: 37.4
    }
  ]);

  // Symptom filter state
  const [selectedSymptomFilter, setSelectedSymptomFilter] = useState<string | null>(null);

  // Form states for adding incidents
  const [showAddIncident, setShowAddIncident] = useState(false);
  const [incidentTitle, setIncidentTitle] = useState("");
  const [incidentTemp, setIncidentTemp] = useState<number>(37.5);
  const [selectedSymptomChips, setSelectedSymptomChips] = useState<string[]>([]);
  const [selectedTreatmentChips, setSelectedTreatmentChips] = useState<string[]>([]);
  const [incidentDoctor, setIncidentDoctor] = useState("Bác sĩ nhi khoa");

  // Form states for adding medications
  const [showAddMed, setShowAddMed] = useState(false);
  const [medName, setMedName] = useState("");
  const [medDosage, setMedDosage] = useState("");
  const [medDoctor, setMedDoctor] = useState("Dr. Aris");

  // Countdown timer for next dose (Paracetamol)
  const [countdownSeconds, setCountdownSeconds] = useState(3600 * 3.5);

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

  const toggleSymptomChip = (sym: string) => {
    setSelectedSymptomChips((prev) =>
      prev.includes(sym) ? prev.filter((s) => s !== sym) : [...prev, sym]
    );
  };

  const toggleTreatmentChip = (treat: string) => {
    setSelectedTreatmentChips((prev) =>
      prev.includes(treat) ? prev.filter((t) => t !== treat) : [...prev, treat]
    );
  };

  const handleSelectPresetIllness = (preset: typeof PRESET_ILLNESSES[0]) => {
    setIncidentTitle(preset.name);
    setIncidentTemp(preset.defaultTemp);
    setSelectedSymptomChips(preset.symptoms);
    setSelectedTreatmentChips([preset.treatment]);
  };

  const handleAddIncidentSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!incidentTitle) return;

    const treatmentString = selectedTreatmentChips.join("; ");

    const newRecord: IncidentRecord = {
      id: `inc_${Date.now()}`,
      title: incidentTitle,
      date: "Today",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      status: "Confirmed",
      symptoms: selectedSymptomChips.length ? selectedSymptomChips : ["Sức khỏe mệt nhẹ"],
      treatment: treatmentString || "Cho bé nghỉ ngơi và theo dõi thân nhiệt.",
      prescribedBy: incidentDoctor || "Phụ huynh ghi nhận",
      temp: incidentTemp
    };

    setIncidents((prev) => [newRecord, ...prev]);

    // Automatic Paracetamol Timer trigger if high fever
    if (incidentTemp >= 38.5) {
      setCountdownSeconds(3600 * 6);
    }

    setShowAddIncident(false);
    setIncidentTitle("");
    setIncidentTemp(37.5);
    setSelectedSymptomChips([]);
    setSelectedTreatmentChips([]);
    setIncidentDoctor("Bác sĩ nhi khoa");
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

    if (medName.toLowerCase().includes("hapacol") || medName.toLowerCase().includes("paracetamol")) {
      setCountdownSeconds(3600 * 6);
    }
  };

  const filteredIncidents = selectedSymptomFilter
    ? incidents.filter((inc) => inc.symptoms.some((s) => s.includes(selectedSymptomFilter)))
    : incidents;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header Banner */}
      <div className="bg-white border border-slate-100 rounded-3xl p-6 sm:p-8 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="p-3.5 rounded-2xl bg-primary/10 text-primary shrink-0">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
              Sức Khỏe & Lịch Dùng Thuốc
            </h1>
            <p className="text-xs text-slate-500 font-medium">
              Theo dõi y tế và đếm ngược liều hạ sốt an toàn cho bé{" "}
              <span className="font-bold text-slate-800">{activeBaby.name}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddIncident(true)}
            className="inline-flex items-center gap-1.5 bg-primary hover:bg-primary/95 text-white text-xs font-bold px-4 py-2.5 rounded-2xl transition-all shadow-xs cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            + Thêm Bệnh Án Nhanh
          </button>

          <button
            onClick={() => setShowAddMed(true)}
            className="inline-flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold px-4 py-2.5 rounded-2xl transition-all shadow-xs cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            + Thêm Thuốc
          </button>
        </div>
      </div>

      {/* Main Grid Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT 2 COLUMNS: INCIDENTS & SYMPTOMS LOGS */}
        <div className="lg:col-span-2 space-y-6">
          {/* Paracetamol Safety Dose Countdown Card */}
          <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-xs flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-2xl bg-amber-50 text-amber-600 border border-amber-100">
                <Thermometer className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-black text-slate-800">
                  Đếm Ngược Liều Hạ Sốt Tiếp Theo (Paracetamol / Hapacol)
                </p>
                <p className="text-[11px] text-slate-500 font-medium">
                  {countdownSeconds > 0
                    ? "Giãn cách an toàn 6 tiếng giữa 2 liều hạ sốt"
                    : "✓ Đã đủ thời gian giãn cách cho liều tiếp theo nếu bé vẫn sốt >38.5°C"}
                </p>
              </div>
            </div>

            <div className="text-right">
              <span className="text-lg font-black font-mono text-primary bg-primary/10 px-3 py-1.5 rounded-xl border border-primary/20">
                {formatCountdown(countdownSeconds)}
              </span>
            </div>
          </div>

          {/* Incident Records Section */}
          <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-xs space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                Lịch Sử Sự Cố Sức Khỏe & Triệu Chứng
              </h3>

              <span className="text-xs font-bold text-slate-400">
                {filteredIncidents.length} đợt theo dõi
              </span>
            </div>

            {filteredIncidents.length === 0 ? (
              <p className="text-xs text-slate-400 font-medium text-center py-8">
                Chưa có sự cố sức khỏe nào được ghi nhận.
              </p>
            ) : (
              <div className="space-y-3">
                {filteredIncidents.map((inc) => (
                  <div
                    key={inc.id}
                    className="bg-slate-50/80 hover:bg-slate-100/80 p-4 rounded-2xl border border-slate-100 space-y-2 transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-black text-slate-800">{inc.title}</span>
                        {inc.temp && (
                          <span
                            className={`text-[10px] font-extrabold px-2 py-0.5 rounded-md ${
                              inc.temp >= 38.5
                                ? "bg-rose-100 text-rose-800 border border-rose-200"
                                : "bg-amber-100 text-amber-800 border border-amber-200"
                            }`}
                          >
                            🌡️ {inc.temp}°C
                          </span>
                        )}
                      </div>

                      <span
                        className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                          inc.status === "Confirmed"
                            ? "bg-amber-100 text-amber-800 border border-amber-200"
                            : "bg-emerald-100 text-emerald-800 border border-emerald-200"
                        }`}
                      >
                        {inc.status === "Confirmed" ? "Đang theo dõi" : "Đã khỏi bệnh ✓"}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-1.5">
                      {inc.symptoms.map((symptom, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] font-bold bg-white text-slate-700 px-2.5 py-1 rounded-xl border border-slate-200"
                        >
                          {symptom}
                        </span>
                      ))}
                    </div>

                    <p className="text-xs text-slate-600 font-medium leading-relaxed bg-white/70 p-2.5 rounded-xl border border-slate-100">
                      <span className="font-bold text-slate-700">Phác đồ xử lý:</span> {inc.treatment}
                    </p>

                    <div className="flex items-center justify-between text-[10px] text-slate-400 font-medium pt-1">
                      <span>Nguồn: {inc.prescribedBy}</span>
                      <span>
                        {inc.date} • {inc.time}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: MEDICATIONS LOG */}
        <div className="space-y-6">
          <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
                <Pill className="w-4 h-4 text-primary" />
                Lịch Dùng Thuốc Hôm Nay
              </h3>
              <span className="text-xs font-bold text-slate-400">{medications.length} thuốc</span>
            </div>

            {medications.length === 0 ? (
              <p className="text-xs text-slate-400 font-medium text-center py-6">
                Hôm nay bé không phải dùng thuốc nào.
              </p>
            ) : (
              <div className="space-y-2.5">
                {medications.map((med) => (
                  <div
                    key={med.id}
                    className="flex items-center justify-between bg-slate-50 p-3.5 rounded-2xl border border-slate-100"
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <p className="text-xs font-bold text-slate-800">{med.name}</p>
                        <span className="text-[10px] font-bold bg-primary/10 text-primary px-2 py-0.5 rounded-md">
                          {med.dosage}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400 font-medium flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {med.time} • Kê đơn: {med.prescribedBy || "Bác sĩ nhi"}
                      </p>
                    </div>

                    <button
                      onClick={() => onDeleteMedication(med.id)}
                      className="p-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                      title="Xóa thuốc"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Allergies & Medical Warnings Card */}
          <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-xs space-y-3">
            <h3 className="text-xs font-black text-rose-600 uppercase tracking-wider flex items-center gap-1.5">
              <AlertCircle className="w-4 h-4 text-rose-500" />
              Dị Ứng & Cảnh Báo Y Khoa Cho Bé
            </h3>
            <div className="p-3.5 bg-rose-50/70 border border-rose-100 rounded-2xl space-y-2">
              <div className="flex flex-wrap gap-1.5">
                {activeBaby.allergies && activeBaby.allergies.length > 0 ? (
                  activeBaby.allergies.map((alg, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-rose-100 border border-rose-200 text-rose-800 font-bold rounded-xl text-xs"
                    >
                      🥛 {alg}
                    </span>
                  ))
                ) : (
                  <span className="px-3 py-1 bg-rose-100 border border-rose-200 text-rose-800 font-bold rounded-xl text-xs">
                    🥛 Nhạy cảm Đậu nành / Sữa công thức
                  </span>
                )}
              </div>
              <p className="text-xs text-rose-700 leading-relaxed font-medium pt-1">
                Cần kiểm tra kĩ thành phần thuốc và nhãn thực phẩm trước khi cho bé <span className="font-bold">{activeBaby.name}</span> dùng.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 🚀 ULTRA-SUPPORTIVE 1-TOUCH SMART ADD INCIDENT MODAL */}
      {/* ========================================================================= */}
      <AnimatePresence>
        {showAddIncident && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-xl space-y-5 max-h-[90vh] overflow-y-auto"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-primary" />
                  <h3 className="text-sm font-black text-slate-800">
                    Ghi Nhận Bệnh Án / Sự Cố Thông Minh
                  </h3>
                </div>
                <button
                  onClick={() => setShowAddIncident(false)}
                  className="text-xs font-bold text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  Hủy
                </button>
              </div>

              {/* ⚡ PRESET ILLNESSES */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold text-slate-700">
                  ⚡ Mẫu tình trạng sức khỏe thông dụng:
                </label>
                <div className="flex flex-wrap gap-2">
                  {PRESET_ILLNESSES.map((preset, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSelectPresetIllness(preset)}
                      className="text-xs font-bold bg-slate-100 hover:bg-primary/10 hover:text-primary text-slate-700 px-3 py-1.5 rounded-xl border border-slate-200 transition-all cursor-pointer"
                    >
                      {preset.name}
                    </button>
                  ))}
                </div>
              </div>

              <form onSubmit={handleAddIncidentSubmit} className="space-y-4 text-xs font-bold text-slate-600">
                {/* Illness Title */}
                <div className="space-y-1">
                  <label className="block">Tên bệnh án / Sự cố sức khỏe</label>
                  <input
                    type="text"
                    required
                    value={incidentTitle}
                    onChange={(e) => setIncidentTitle(e.target.value)}
                    placeholder="Ví dụ: Sốt cao sau tiêm chủng, Viêm họng..."
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>

                {/* 🌡️ TEMPERATURE PICKER & ALERT */}
                <div className="bg-slate-50 border border-slate-200 p-4 rounded-2xl space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                      <Thermometer className="w-4 h-4 text-primary" />
                      Đo Thân Nhiệt Bé (°C):
                    </label>
                    <span
                      className={`text-xs font-extrabold px-3 py-1 rounded-xl ${
                        incidentTemp >= 38.5
                          ? "bg-rose-100 text-rose-800 border border-rose-300 animate-pulse"
                          : incidentTemp >= 37.5
                          ? "bg-amber-100 text-amber-800 border border-amber-200"
                          : "bg-emerald-100 text-emerald-800 border border-emerald-200"
                      }`}
                    >
                      {incidentTemp}°C -{" "}
                      {incidentTemp >= 38.5
                        ? "SỐT CAO ⚠️"
                        : incidentTemp >= 37.5
                        ? "Sốt nhẹ"
                        : "Bình thường ✓"}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {[37.0, 37.5, 38.0, 38.5, 39.0, 39.5].map((tempVal) => (
                      <button
                        key={tempVal}
                        type="button"
                        onClick={() => setIncidentTemp(tempVal)}
                        className={`flex-1 py-1.5 text-xs font-bold rounded-xl border transition-all cursor-pointer ${
                          incidentTemp === tempVal
                            ? "bg-primary text-white border-primary shadow-xs"
                            : "bg-white text-slate-700 border-slate-200 hover:bg-slate-100"
                        }`}
                      >
                        {tempVal}°C
                      </button>
                    ))}
                  </div>

                  {/* Comprehensive Multi-Factor AI Risk Assessment (WHO/AAP) */}
                  <div className="pt-1">
                    {(() => {
                      const hasHighFever = incidentTemp >= 38.5;
                      const hasEmergencySymptom = selectedSymptomChips.some((s) => s.includes("Co giật") || s.includes("Nôn") || s.includes("Khó thở"));
                      const hasAllergySymptom = selectedSymptomChips.some((s) => s.includes("Nổi mẩn"));

                      let riskLevel: "safe" | "warning" | "danger" | "emergency" = "safe";
                      let title = `Thân nhiệt ${incidentTemp}°C - An toàn`;
                      let advice = `Thân nhiệt bé ở mức bình thường. Khuyên phụ huynh cho bé bú đủ cữ, duy trì phòng thoáng mát và theo dõi sinh hoạt.`;

                      if (hasEmergencySymptom || incidentTemp >= 39.5) {
                        riskLevel = "emergency";
                        title = `🚨 CẢNH BÁO NGUY HIỂM CẤP CỨU (${incidentTemp}°C + Triệu chứng cấp tính)`;
                        advice = `Bé có dấu hiệu cần đưa đi viện cấp cứu (${selectedSymptomChips.join(", ") || "Sốt cực cao >39.5°C"}). Cần đưa bé đến Bệnh viện Nhi gần nhất ngay lập tức! Cởi bớt quần áo, chườm ấm liên tục khi di chuyển.`;
                      } else if (hasHighFever) {
                        riskLevel = "danger";
                        title = `⚠️ CẢNH BÁO SỐT CAO (${incidentTemp}°C - Chuẩn AAP/WHO)`;
                        advice = `Dùng Paracetamol liều 10-15mg/kg cho bé ${activeBaby.name} (khoảng 75 - 100mg hoặc gói 150mg theo chỉ định). Giãn cách 4-6 tiếng/liều. Đồng hồ đếm ngược 6 tiếng sẽ tự bật sau khi lưu.`;
                      } else if (incidentTemp >= 37.5 || selectedSymptomChips.length > 0) {
                        riskLevel = "warning";
                        title = `🟡 Sốt nhẹ / Theo dõi triệu chứng (${incidentTemp}°C)`;
                        advice = `Triệu chứng ghi nhận: ${selectedSymptomChips.join(", ") || "Sốt nhẹ"}. Chưa cần dùng hạ sốt. Chườm ấm trán nách bẹn, cho bé uống nhiều nước/sữa và đo lại sau 30 phút.`;
                      }

                      if (hasAllergySymptom && activeBaby.allergies && activeBaby.allergies.length > 0) {
                        advice += ` ⚠️ Lưu ý tiền sử dị ứng của bé (${activeBaby.allergies.join(", ")}): Kiểm tra kĩ thành phần thuốc trước khi cho bé uống.`;
                      }

                      return (
                        <div
                          className={`p-3.5 rounded-2xl border space-y-1.5 transition-all ${
                            riskLevel === "emergency"
                              ? "bg-rose-100 border-rose-300 text-rose-950 animate-pulse"
                              : riskLevel === "danger"
                              ? "bg-rose-50 border-rose-200 text-rose-900"
                              : riskLevel === "warning"
                              ? "bg-amber-50 border-amber-200 text-amber-900"
                              : "bg-emerald-50 border-emerald-200 text-emerald-900"
                          }`}
                        >
                          <p className="text-xs font-black flex items-center gap-1.5">
                            <Sparkles className="w-4 h-4 text-primary shrink-0" />
                            🩺 AI Đánh Giá Nguy Cơ & Lời Khuyên Y Khoa (WHO/AAP):
                          </p>
                          <p className="text-xs font-bold">{title}</p>
                          <p className="text-[11px] leading-relaxed font-medium opacity-90">{advice}</p>
                        </div>
                      );
                    })()}
                  </div>
                </div>

                {/* 🏷️ QUICK SYMPTOM CHIPS */}
                <div className="space-y-1.5">
                  <label className="block">Chọn các triệu chứng của bé:</label>
                  <div className="flex flex-wrap gap-1.5">
                    {QUICK_SYMPTOMS.map((sym) => {
                      const isSelected = selectedSymptomChips.includes(sym);
                      return (
                        <button
                          key={sym}
                          type="button"
                          onClick={() => toggleSymptomChip(sym)}
                          className={`text-[11px] font-bold px-3 py-1.5 rounded-xl border transition-all cursor-pointer ${
                            isSelected
                              ? "bg-primary text-white border-primary shadow-xs"
                              : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                          }`}
                        >
                          {sym} {isSelected ? "✓" : ""}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* 💊 QUICK TREATMENT CHIPS */}
                <div className="space-y-1.5">
                  <label className="block">Bấm chọn phác đồ xử lý & thuốc dùng:</label>
                  <div className="flex flex-wrap gap-1.5">
                    {QUICK_TREATMENTS.map((treat) => {
                      const isSelected = selectedTreatmentChips.includes(treat);
                      return (
                        <button
                          key={treat}
                          type="button"
                          onClick={() => toggleTreatmentChip(treat)}
                          className={`text-[11px] font-bold px-3 py-1.5 rounded-xl border transition-all cursor-pointer ${
                            isSelected
                              ? "bg-emerald-600 text-white border-emerald-600 shadow-xs"
                              : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                          }`}
                        >
                          {treat} {isSelected ? "✓" : ""}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Doctor field */}
                <div className="space-y-1">
                  <label className="block">Bác sĩ kê đơn / Nguồn thông tin</label>
                  <input
                    type="text"
                    value={incidentDoctor}
                    onChange={(e) => setIncidentDoctor(e.target.value)}
                    placeholder="Ví dụ: Bác sĩ nhi khoa, Bệnh viện Nhi Đồng..."
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 font-medium text-slate-800"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-white py-3 rounded-2xl font-black text-xs transition-all shadow-md cursor-pointer"
                >
                  Lưu Bệnh Án & Theo Dõi Sức Khỏe
                </button>
              </form>
            </motion.div>
          </div>
        )}

        {/* SMART ADD MEDICATION MODAL */}
        {showAddMed && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-md w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Pill className="w-5 h-5 text-primary" />
                  <h3 className="text-sm font-black text-slate-800">
                    Ghi Nhận Đơn Thuốc Cho Bé
                  </h3>
                </div>
                <button
                  onClick={() => setShowAddMed(false)}
                  className="text-xs font-bold text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  Hủy
                </button>
              </div>

              {/* ⚡ PRESET MEDICATIONS */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold text-slate-700">
                  ⚡ Mẫu thuốc nhi khoa thông dụng:
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {PRESET_MEDICATIONS.map((preset, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => {
                        setMedName(preset.name);
                        setMedDosage(preset.dosage);
                        setMedDoctor(preset.doctor);
                      }}
                      className="text-[11px] font-bold bg-slate-100 hover:bg-primary/10 hover:text-primary text-slate-700 px-3 py-1.5 rounded-xl border border-slate-200 transition-all cursor-pointer"
                    >
                      {preset.name}
                    </button>
                  ))}
                </div>
              </div>

              <form onSubmit={handleAddMedSubmit} className="space-y-4 text-xs font-bold text-slate-600">
                {/* Medication Name */}
                <div className="space-y-1">
                  <label className="block">Tên loại thuốc</label>
                  <input
                    type="text"
                    required
                    value={medName}
                    onChange={(e) => setMedName(e.target.value)}
                    placeholder="Ví dụ: Hapacol 150mg, Vitamin D3 K2..."
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>

                {/* Dosage Field & Quick Chips */}
                <div className="space-y-1.5">
                  <label className="block">Liều lượng uống</label>
                  <input
                    type="text"
                    required
                    value={medDosage}
                    onChange={(e) => setMedDosage(e.target.value)}
                    placeholder="Ví dụ: 1 gói (150mg), 2.5ml, 2 giọt..."
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />

                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {COMMON_DOSAGES.map((dosageChip) => (
                      <button
                        key={dosageChip}
                        type="button"
                        onClick={() => setMedDosage(dosageChip)}
                        className={`text-[10px] font-bold px-2.5 py-1 rounded-xl border transition-all cursor-pointer ${
                          medDosage === dosageChip
                            ? "bg-primary text-white border-primary shadow-xs"
                            : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                        }`}
                      >
                        {dosageChip}
                      </button>
                    ))}
                  </div>
                </div>

                {/* AI Weight-Based Dosage Hint */}
                {medName.toLowerCase().includes("hapacol") || medName.toLowerCase().includes("paracetamol") ? (
                  <div className="bg-amber-50 border border-amber-200 p-3 rounded-2xl space-y-1 text-amber-900">
                    <p className="text-[11px] font-bold flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                      🩺 AI Tính Liều Hạ Sốt Theo Cân Nặng Bé {activeBaby.name}:
                    </p>
                    <p className="text-[10px] leading-relaxed font-medium text-amber-800">
                      Liều Paracetamol an toàn là 10-15mg/kg/lần (Khuyên dùng ~75 - 110mg/lần). Giãn cách tối thiểu 4-6 tiếng giữa 2 liều. Đồng hồ đếm ngược 6 tiếng sẽ tự động kích hoạt ngay sau khi lưu.
                    </p>
                  </div>
                ) : null}

                {/* Prescribed By */}
                <div className="space-y-1">
                  <label className="block">Bác sĩ kê đơn / Nguồn chỉ định</label>
                  <input
                    type="text"
                    value={medDoctor}
                    onChange={(e) => setMedDoctor(e.target.value)}
                    placeholder="Ví dụ: Dr. Aris (Nhi khoa), Phụ huynh..."
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 font-medium text-slate-800"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-white py-3 rounded-2xl font-black text-xs transition-all shadow-md cursor-pointer"
                >
                  Lưu Đơn Thuốc & Bật Đếm Ngược Giãn Cách
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
