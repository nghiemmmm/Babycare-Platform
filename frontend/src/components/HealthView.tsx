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

  const generateAITreatment = (title: string, temp: number, symptoms: string[]) => {
    const parts: string[] = [];

    if (temp >= 39.5) {
      parts.push("⚠️ Sốt nguy hiểm: Chườm ấm toàn thân liên tục và đưa bé đến Bệnh viện Nhi ngay.");
    } else if (temp >= 38.5) {
      parts.push(`Cho bé uống Paracetamol liều 10-15mg/kg theo chỉ dẫn và chườm ấm trán, nách, bẹn.`);
    } else if (temp >= 37.5) {
      parts.push("Chườm ấm trán nách, giữ phòng thoáng mát và theo dõi thân nhiệt mỗi 30 phút.");
    }

    const symText = (title + " " + symptoms.join(" ")).toLowerCase();
    if (symText.includes("ho") || symText.includes("họng") || symText.includes("cảm")) {
      parts.push("Dùng siro ho thảo dược, nhỏ mũi bằng nước muối sinh lý 0.9% và cho uống nước ấm.");
    }
    if (symText.includes("sổ mũi") || symText.includes("ngạt")) {
      parts.push("Làm sạch dịch mũi và duy trì độ ẩm phòng 55-60%.");
    }
    if (symText.includes("nôn") || symText.includes("tiêu chảy") || symText.includes("tiêu hóa")) {
      parts.push("Cho uống Oresol bù điện giải rải rác trong ngày và ăn thức ăn lỏng dễ tiêu.");
    }
    if (symText.includes("mọc răng") || symText.includes("nướu") || symText.includes("dãi")) {
      parts.push("Cho ngậm nướu lạnh và mát-xa nướu nhẹ nhàng cho bé.");
    }
    if (symText.includes("mẩn") || symText.includes("dị ứng") || symText.includes("ban")) {
      parts.push("Giữ da bé sạch thoáng, lau người bằng nước ấm dịu nhẹ và tránh chất gây kích ứng.");
    }

    if (parts.length === 0) {
      parts.push(`Cho bé ${activeBaby.name} nghỉ ngơi, theo dõi sinh hoạt và cho bú/uống nước đầy đủ.`);
    }

    return parts.join(" ");
  };

  const handleAddIncidentSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!incidentTitle) return;

    const aiTreatment = generateAITreatment(incidentTitle, incidentTemp, selectedSymptomChips);

    const newRecord: IncidentRecord = {
      id: `inc_${Date.now()}`,
      title: incidentTitle,
      date: "Today",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      status: "Confirmed",
      symptoms: selectedSymptomChips.length ? selectedSymptomChips : ["Sức khỏe mệt nhẹ"],
      treatment: aiTreatment,
      prescribedBy: "AI Y Khoa Gợi Ý",
      temp: incidentTemp
    };

    setIncidents((prev) => [newRecord, ...prev]);

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
  };

  const toggleIncidentStatus = (id: string) => {
    setIncidents((prev) =>
      prev.map((inc) =>
        inc.id === id
          ? { ...inc, status: inc.status === "Confirmed" ? "Resolved" : "Confirmed" }
          : inc
      )
    );
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
              Sổ Theo Dõi Sức Khỏe & Y Tế
            </h1>
            <p className="text-xs text-slate-500 font-medium">
              Nhật ký theo dõi bệnh trạng, lịch dùng thuốc và đếm ngược liều hạ sốt cho bé{" "}
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
            Thêm Ghi Chép Sức Khỏe
          </button>

          <button
            onClick={() => setShowAddMed(true)}
            className="inline-flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold px-4 py-2.5 rounded-2xl transition-all shadow-xs cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Thêm Thuốc Uống
          </button>
        </div>
      </div>

      {/* Main Grid Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT 2 COLUMNS: INCIDENTS & SYMPTOMS LOGS */}
        <div className="lg:col-span-2 space-y-6">
          {/* Incident Records Section */}
          <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-xs space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <h3 className="text-sm font-black text-slate-800 flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                Nhật Ký Bệnh Trạng & Triệu Chứng
              </h3>

              <span className="text-xs font-bold text-slate-400">
                {filteredIncidents.length} đợt theo dõi
              </span>
            </div>

            {/* Quick Symptom Filter Chips */}
            <div className="flex flex-wrap items-center gap-1.5 pt-1 pb-1">
              <span className="text-[11px] font-bold text-slate-400 mr-1">Lọc triệu chứng:</span>
              <button
                type="button"
                onClick={() => setSelectedSymptomFilter(null)}
                className={`text-[10px] font-bold px-2.5 py-1 rounded-xl border transition-all cursor-pointer ${
                  selectedSymptomFilter === null
                    ? "bg-primary text-white border-primary shadow-xs"
                    : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                }`}
              >
                Tất cả
              </button>
              {["Sốt", "Ho", "Sổ mũi", "Nôn", "Tiêu chảy", "Mọc răng", "Nổi mẩn"].map((sym) => (
                <button
                  key={sym}
                  type="button"
                  onClick={() => setSelectedSymptomFilter(selectedSymptomFilter === sym ? null : sym)}
                  className={`text-[10px] font-bold px-2.5 py-1 rounded-xl border transition-all cursor-pointer ${
                    selectedSymptomFilter === sym
                      ? "bg-primary text-white border-primary shadow-xs"
                      : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  {sym}
                </button>
              ))}
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

                      <button
                        type="button"
                        onClick={() => toggleIncidentStatus(inc.id)}
                        className={`text-[10px] font-bold px-3 py-1 rounded-xl border transition-all cursor-pointer flex items-center gap-1.5 ${
                          inc.status === "Confirmed"
                            ? "bg-amber-50 hover:bg-emerald-50 text-amber-800 hover:text-emerald-800 border-amber-200 hover:border-emerald-300"
                            : "bg-emerald-100 text-emerald-800 border-emerald-200 shadow-2xs"
                        }`}
                        title={inc.status === "Confirmed" ? "Bấm để đánh dấu Bé đã khỏi bệnh" : "Bé đã khỏi bệnh"}
                      >
                        {inc.status === "Confirmed" ? (
                          <>
                            <Clock className="w-3 h-3 text-amber-600 shrink-0" />
                            <span>Đang theo dõi • Đánh dấu khỏi</span>
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
                            <span>Đã khỏi bệnh ✓</span>
                          </>
                        )}
                      </button>
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
              Lưu Ý Dị Ứng & Tiền Sử Y Tế
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
      {/* 🚀 ULTRA-SUPPORTIVE SMART ADD INCIDENT MODAL */}
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
                    Thêm Ghi Chép Sức Khỏe Cho Bé
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

                <button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-white py-3 rounded-2xl font-black text-xs transition-all shadow-md cursor-pointer"
                >
                  Lưu Ghi Chép Sức Khỏe
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
                  Lưu Đơn Thuốc Uống
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
