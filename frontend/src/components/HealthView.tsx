import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { apiFetch, authStorage } from "../lib/authClient";
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
  FileText,
  Sparkles,
  CheckCircle2,
  Bell,
  Calendar,
  Pause,
  Play,
  CheckCheck,
  History,
  Package
} from "lucide-react";
import {
  BabyProfile,
  MedicationLog,
  MedicationPlan,
  MedicationDoseLog,
  TodayDoseItem,
  PlanStatus
} from "../types";

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
  {
    name: "🌡️ Sốt sau tiêm / Sốt cao",
    defaultTemp: 38.5,
    symptoms: ["🌡️ Sốt cao (>38.5°C)", "😴 Quấy khóc mệt mỏi"],
    treatment: "Uống Paracetamol 10-15mg/kg, chườm ấm trán nách, cho bú nhiều cữ nhỏ."
  },
  {
    name: "🌬️ Viêm họng / Cảm cúm",
    defaultTemp: 37.8,
    symptoms: ["🌬️ Ho khan", "👃 Sổ mũi", "🥵 Đau họng"],
    treatment: "Siro ho thảo dược, rửa mũi nước muối sinh lý 0.9%, uống nước ấm."
  },
  {
    name: "🦷 Mọc răng sưng nướu",
    defaultTemp: 37.4,
    symptoms: ["🦷 Chảy dãi mọc răng", "😴 Quấy khóc mệt mỏi"],
    treatment: "Ngậm nướu lạnh, mát-xa nướu nhẹ nhàng, giữ vệ sinh khoang miệng."
  },
  {
    name: "💩 Rối loạn tiêu hóa",
    defaultTemp: 37.0,
    symptoms: ["🤮 Nôn mửa", "💩 Tiêu chảy"],
    treatment: "Uống Oresol bù điện giải, bổ sung men vi sinh, ăn cháo loãng."
  },
  {
    name: "🔴 Nổi mẩn / Dị ứng",
    defaultTemp: 37.0,
    symptoms: ["🔴 Nổi mẩn đỏ"],
    treatment: "Giữ da sạch thoáng, lau người bằng nước ấm dịu nhẹ, tránh thức ăn nghi dị ứng."
  }
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

const PRESET_PLANS = [
  {
    name: "Amoxicillin",
    alternative_name: "Augmentin",
    strength: "250 mg / 5 mL",
    dose: "5",
    unit: "mL",
    route: "Oral (Đường uống)",
    frequency: "3 lần/ngày",
    schedule_times: ["08:00", "14:00", "20:00"],
    meal_timing: "after_food",
    duration_days: 7,
    purpose: "Kháng sinh viêm họng / viêm phế quản",
    instructions: "Uống sau khi ăn no 30 phút, uống nhiều nước ấm.",
    prescribed_by: "Bác sĩ Nhi khoa"
  },
  {
    name: "Hapacol 150mg",
    alternative_name: "Paracetamol",
    strength: "150 mg / gói",
    dose: "1",
    unit: "gói",
    route: "Oral (Đường uống)",
    frequency: "Khi sốt > 38.5°C (Cách 4-6h)",
    schedule_times: ["08:00"],
    meal_timing: "when_fever",
    duration_days: 3,
    purpose: "Hạ sốt, giảm đau sau tiêm hoặc mọc răng",
    instructions: "Duy trì khoảng cách tối thiểu 4-6 tiếng giữa 2 lần uống.",
    prescribed_by: "Bác sĩ Nhi khoa"
  },
  {
    name: "Vitamin D3 K2 Drops",
    alternative_name: "Lineabon D3K2",
    strength: "400 IU / 2 giọt",
    dose: "2",
    unit: "giọt",
    route: "Oral (Đường uống)",
    frequency: "1 lần/ngày",
    schedule_times: ["08:00"],
    meal_timing: "after_food",
    duration_days: 30,
    purpose: "Bổ sung Vitamin D3 giúp phát triển chiều cao",
    instructions: "Nhỏ trực tiếp vào miệng bé hoặc đầu ti mẹ vào buổi sáng.",
    prescribed_by: "Bác sĩ dinh dưỡng"
  },
  {
    name: "Siro Ho Thảo Dược Prospan",
    alternative_name: "Cao lá thường xuân",
    strength: "35 mg / 5 mL",
    dose: "2.5",
    unit: "mL",
    route: "Oral (Đường uống)",
    frequency: "2 lần/ngày",
    schedule_times: ["08:00", "20:00"],
    meal_timing: "after_food",
    duration_days: 5,
    purpose: "Giảm ho, long đờm, dịu rát họng",
    instructions: "Uống sau bữa ăn sáng và tối.",
    prescribed_by: "Bác sĩ Nhi khoa"
  },
  {
    name: "Men Vi Sinh BioGaia",
    alternative_name: "L. reuteri Protectis",
    strength: "100 triệu CFU / 5 giọt",
    dose: "5",
    unit: "giọt",
    route: "Oral (Đường uống)",
    frequency: "1 lần/ngày",
    schedule_times: ["09:00"],
    meal_timing: "with_food",
    duration_days: 14,
    purpose: "Hỗ trợ tiêu hóa, giảm nôn trớ và đau bụng",
    instructions: "Nhỏ vào thìa hoặc trộn cùng sữa ấm (< 40°C).",
    prescribed_by: "Bác sĩ Nhi khoa"
  }
];

const MEAL_TIMING_MAP: Record<string, { label: string; bg: string; text: string }> = {
  after_food: { label: "Sau ăn 30p", bg: "bg-blue-50 border-blue-200", text: "text-blue-700" },
  before_food: { label: "Trước ăn 30p", bg: "bg-amber-50 border-amber-200", text: "text-amber-700" },
  with_food: { label: "Cùng bữa ăn", bg: "bg-purple-50 border-purple-200", text: "text-purple-700" },
  empty_stomach: { label: "Bụng đói", bg: "bg-rose-50 border-rose-200", text: "text-rose-700" },
  anytime: { label: "Bất kỳ lúc nào", bg: "bg-slate-50 border-slate-200", text: "text-slate-700" },
  when_fever: { label: "Khi sốt > 38.5°C", bg: "bg-rose-50 border-rose-300", text: "text-rose-800" }
};

export default function HealthView({
  activeBaby,
  medications,
  onAddMedication,
  onDeleteMedication
}: HealthViewProps) {
  // Incidents state
  const [incidents, setIncidents] = useState<IncidentRecord[]>([]);
  const [selectedSymptomFilter, setSelectedSymptomFilter] = useState<string | null>(null);
  const [dismissedReminders, setDismissedReminders] = useState<string[]>([]);

  // Medication Management Tabs & States
  const [medTab, setMedTab] = useState<"today" | "cabinet" | "history">("today");
  const [todayDoses, setTodayDoses] = useState<TodayDoseItem[]>([]);
  const [medPlans, setMedPlans] = useState<MedicationPlan[]>([]);
  const [doseHistory, setDoseHistory] = useState<MedicationDoseLog[]>([]);
  const [isLoadingMeds, setIsLoadingMeds] = useState(false);

  // Form states for adding incident
  const [showAddIncident, setShowAddIncident] = useState(false);
  const [incidentTitle, setIncidentTitle] = useState("");
  const [incidentTemp, setIncidentTemp] = useState<number>(37.5);
  const [selectedSymptomChips, setSelectedSymptomChips] = useState<string[]>([]);
  const [incidentDoctor, setIncidentDoctor] = useState("Bác sĩ nhi khoa");

  // Form states for adding medication plan
  const [showAddPlanModal, setShowAddPlanModal] = useState(false);
  const [planName, setPlanName] = useState("");
  const [planAltName, setPlanAltName] = useState("");
  const [planStrength, setPlanStrength] = useState("");
  const [planDose, setPlanDose] = useState("");
  const [planUnit, setPlanUnit] = useState("mL");
  const [planRoute, setPlanRoute] = useState("Oral (Đường uống)");
  const [planFrequency, setPlanFrequency] = useState("3 lần/ngày");
  const [planScheduleTimes, setPlanScheduleTimes] = useState<string[]>(["08:00", "14:00", "20:00"]);
  const [planMealTiming, setPlanMealTiming] = useState("after_food");
  const [planStartDate, setPlanStartDate] = useState(new Date().toISOString().slice(0, 10));
  const [planDurationDays, setPlanDurationDays] = useState<number>(7);
  const [planPurpose, setPlanPurpose] = useState("");
  const [planInstructions, setPlanInstructions] = useState("");
  const [planDoctor, setPlanDoctor] = useState("Bác sĩ nhi khoa");

  // Fetch Health Records
  const fetchHealthRecords = async () => {
    if (!activeBaby?.id) return;
    try {
      const res = await apiFetch(`/api/v1/babies/${activeBaby.id}/health-records`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          const mapped: IncidentRecord[] = data.map((item) => {
            const recDate = item.recorded_at ? new Date(item.recorded_at) : new Date();
            return {
              id: item.id || `inc_${Date.now()}`,
              title: item.diagnosis || "Bệnh lý / Triệu chứng",
              date: recDate.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" }),
              time: recDate.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
              status: (item.status === "Resolved" ? "Resolved" : "Confirmed") as "Confirmed" | "Resolved",
              symptoms: Array.isArray(item.symptoms) && item.symptoms.length > 0 ? item.symptoms : ["Sức khỏe mệt nhẹ"],
              treatment: item.treatment || "Theo dõi sinh hoạt và nghỉ ngơi.",
              prescribedBy: item.doctor_name || "AI Y Khoa Gợi Ý",
              temp: item.temp ? Number(item.temp) : undefined
            };
          });
          setIncidents(mapped);
        }
      }
    } catch (err) {
      console.error("Failed to fetch health records:", err);
    }
  };

  // Fetch Medication Management Data
  const fetchMedicationData = async () => {
    if (!activeBaby?.id) return;
    setIsLoadingMeds(true);
    try {
      const [resDoses, resPlans, resHistory] = await Promise.all([
        apiFetch(`/api/v1/babies/${activeBaby.id}/medication-doses/today`),
        apiFetch(`/api/v1/babies/${activeBaby.id}/medication-plans`),
        apiFetch(`/api/v1/babies/${activeBaby.id}/medication-doses/history`)
      ]);
      if (resDoses.ok) setTodayDoses(await resDoses.json());
      if (resPlans.ok) setMedPlans(await resPlans.json());
      if (resHistory.ok) setDoseHistory(await resHistory.json());
    } catch (err) {
      console.error("Failed to fetch medication data:", err);
    } finally {
      setIsLoadingMeds(false);
    }
  };

  useEffect(() => {
    fetchHealthRecords();
    fetchMedicationData();
  }, [activeBaby?.id]);

  useEffect(() => {
    const handleSync = () => {
      fetchMedicationData();
      fetchHealthRecords();
    };
    window.addEventListener("baby-data-updated", handleSync);
    return () => window.removeEventListener("baby-data-updated", handleSync);
  }, [activeBaby?.id]);

  // Generate smart AI pediatric treatment suggestion
  const generateAITreatment = (title: string, temp: number, symptoms: string[]) => {
    const parts: string[] = [];

    if (temp >= 39.5) {
      parts.push("⚠️ Sốt nguy hiểm: Chườm ấm toàn thân liên tục và đưa bé đến Bệnh viện Nhi ngay.");
    } else if (temp >= 38.5) {
      parts.push("Cho bé uống Paracetamol liều 10-15mg/kg theo chỉ dẫn và chườm ấm trán, nách, bẹn.");
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

  const handleSelectPresetIllness = (preset: typeof PRESET_ILLNESSES[0]) => {
    setIncidentTitle(preset.name);
    setIncidentTemp(preset.defaultTemp);
    setSelectedSymptomChips(preset.symptoms);
  };

  const toggleSymptomChip = (sym: string) => {
    setSelectedSymptomChips((prev) =>
      prev.includes(sym) ? prev.filter((s) => s !== sym) : [...prev, sym]
    );
  };

  // Submit Incident with Optimistic UI & Firestore persistence
  const handleAddIncidentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!incidentTitle.trim()) return;

    const symptomsToSave = selectedSymptomChips.length > 0 ? selectedSymptomChips : ["Sức khỏe mệt nhẹ"];
    const aiTreatment = generateAITreatment(incidentTitle, incidentTemp, symptomsToSave);

    const newRecord: IncidentRecord = {
      id: `inc_${Date.now()}`,
      title: incidentTitle.trim(),
      date: "Hôm nay",
      time: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
      status: "Confirmed",
      symptoms: symptomsToSave,
      treatment: aiTreatment,
      prescribedBy: incidentDoctor || "AI Y Khoa Gợi Ý",
      temp: incidentTemp
    };

    setIncidents((prev) => [newRecord, ...prev]);
    setSelectedSymptomFilter(null);
    setShowAddIncident(false);
    setIncidentTitle("");
    setIncidentTemp(37.5);
    setSelectedSymptomChips([]);

    try {
      const res = await apiFetch(`/api/v1/babies/${activeBaby.id}/health-records`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          diagnosis: newRecord.title,
          temp: newRecord.temp,
          symptoms: newRecord.symptoms,
          treatment: newRecord.treatment,
          doctor_name: newRecord.prescribedBy,
          status: newRecord.status
        })
      });
      if (res.ok) {
        const created = await res.json();
        if (created.id) {
          setIncidents((prev) =>
            prev.map((item) => (item.id === newRecord.id ? { ...item, id: created.id } : item))
          );
        }
        window.dispatchEvent(new CustomEvent("baby-data-updated", { detail: { babyId: activeBaby.id } }));
      }
    } catch (err) {
      console.error("Failed to save health record:", err);
    }
  };

  const toggleIncidentStatus = async (id: string) => {
    const target = incidents.find((i) => i.id === id);
    if (!target) return;
    const nextStatus = target.status === "Confirmed" ? "Resolved" : "Confirmed";
    setIncidents((prev) =>
      prev.map((i) => (i.id === id ? { ...i, status: nextStatus } : i))
    );
    try {
      await apiFetch(`/api/v1/babies/${activeBaby.id}/health-records/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus })
      });
    } catch (e) {
      console.error("Failed to update status:", e);
    }
  };

  // Toast Notification for Real-time sync across devices
  const [syncToast, setSyncToast] = useState<{ message: string; visible: boolean }>({ message: "", visible: false });

  const showSyncNotification = (msg: string) => {
    setSyncToast({ message: msg, visible: true });
    setTimeout(() => {
      setSyncToast((prev) => ({ ...prev, visible: false }));
    }, 4500);
  };

  // Action: Log Dose with Real-time Multi-Caregiver State Transition (Auto-attributed to logged-in user)
  const handleLogDoseAction = async (
    dose: TodayDoseItem,
    actionStatus: "taken" | "skipped" | "snoozed",
    customNote?: string
  ) => {
    // Automatically retrieve the authenticated caregiver's name from session/storage
    const actor = authStorage.name || "Phụ huynh";
    const todayStr = new Date().toISOString().slice(0, 10);
    const nowIso = new Date().toISOString();
    const timeStr = new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });

    // Optimistic UI state transition
    setTodayDoses((prev) =>
      prev.map((d) =>
        d.dose_id === dose.dose_id
          ? {
              ...d,
              status: actionStatus,
              taken_at: actionStatus === "taken" ? nowIso : undefined,
              administered_by: actor
            }
          : d
      )
    );

    let defaultNote = "Đã cho bé uống đúng liều";
    if (actionStatus === "skipped") defaultNote = "Người chăm sóc ghi nhận bỏ qua cữ này";
    if (actionStatus === "snoozed") defaultNote = "Hoãn nhắc lại sau 15 phút";

    const noteToSave = customNote || defaultNote;

    try {
      await apiFetch(`/api/v1/babies/${activeBaby.id}/medication-doses/log`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan_id: dose.plan_id,
          medication_name: dose.medication_name,
          scheduled_date: todayStr,
          scheduled_time: dose.scheduled_time,
          taken_at: actionStatus === "taken" ? nowIso : undefined,
          dose_taken: dose.dose_display,
          status: actionStatus,
          administered_by: actor,
          notes: noteToSave
        })
      });

      if (actionStatus === "taken") {
        showSyncNotification(
          `✓ ${actor} đã cho bé uống ${dose.medication_name} (${dose.dose_display}) lúc ${timeStr}. Toàn bộ người chăm sóc trong gia đình đã được cập nhật!`
        );
      } else if (actionStatus === "snoozed") {
        showSyncNotification(`⏰ ${actor} đã hoãn nhắc nhở cữ thuốc ${dose.medication_name} thêm 15 phút.`);
      } else {
        showSyncNotification(`✕ ${actor} đã ghi nhận bỏ qua cữ ${dose.medication_name}.`);
      }

      fetchMedicationData();
      window.dispatchEvent(new CustomEvent("baby-data-updated", { detail: { babyId: activeBaby.id } }));
    } catch (err) {
      console.error("Failed to log dose action:", err);
    }
  };

  // Action: Submit Medication Plan
  const handleCreatePlanSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      name: planName.trim(),
      alternative_name: planAltName.trim() || undefined,
      strength: planStrength.trim() || undefined,
      dose: planDose.trim(),
      unit: planUnit.trim(),
      route: planRoute,
      frequency: planFrequency,
      schedule_times: planScheduleTimes,
      meal_timing: planMealTiming,
      start_date: planStartDate,
      duration_days: Number(planDurationDays),
      purpose: planPurpose.trim() || undefined,
      instructions: planInstructions.trim() || undefined,
      prescribed_by: planDoctor.trim() || "Bác sĩ nhi khoa",
      status: "active"
    };
    try {
      const res = await apiFetch(`/api/v1/babies/${activeBaby.id}/medication-plans`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setShowAddPlanModal(false);
        fetchMedicationData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdatePlanStatus = async (planId: string, newStatus: PlanStatus) => {
    await apiFetch(`/api/v1/babies/${activeBaby.id}/medication-plans/${planId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    fetchMedicationData();
  };

  const handleDeletePlan = async (planId: string) => {
    if (!window.confirm("Bạn có chắc muốn xóa đơn thuốc này khỏi tủ thuốc?")) return;
    await apiFetch(`/api/v1/babies/${activeBaby.id}/medication-plans/${planId}`, { method: "DELETE" });
    fetchMedicationData();
  };

  const handleSelectPresetPlan = (preset: typeof PRESET_PLANS[0]) => {
    setPlanName(preset.name);
    setPlanAltName(preset.alternative_name || "");
    setPlanStrength(preset.strength || "");
    setPlanDose(preset.dose);
    setPlanUnit(preset.unit);
    setPlanRoute(preset.route);
    setPlanFrequency(preset.frequency);
    setPlanScheduleTimes(preset.schedule_times);
    setPlanMealTiming(preset.meal_timing);
    setPlanDurationDays(preset.duration_days);
    setPlanPurpose(preset.purpose);
    setPlanInstructions(preset.instructions);
    setPlanDoctor(preset.prescribed_by);
  };

  const filteredIncidents = selectedSymptomFilter
    ? incidents.filter((inc) => inc.symptoms?.some((s) => s.includes(selectedSymptomFilter)))
    : incidents;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16" id="health-view">
      {/* Header Banner */}
      <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-2xl bg-primary/10 text-primary shrink-0">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Sổ theo dõi sức khỏe & Quản lý thuốc
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Quản lý lịch dùng thuốc có cấu trúc, nhắc lịch đúng giờ và nhật ký theo dõi sức khỏe cho bé{" "}
              <span className="font-semibold text-slate-800">{activeBaby.name}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddPlanModal(true)}
            className="inline-flex items-center gap-1.5 bg-primary hover:bg-primary/95 text-white text-xs font-semibold px-4 py-2.5 rounded-xl transition-all shadow-xs cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Thêm đơn thuốc mới
          </button>
          <button
            onClick={() => setShowAddIncident(true)}
            className="inline-flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-4 py-2.5 rounded-xl transition-all shadow-xs cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Ghi chép sức khỏe
          </button>
        </div>
      </div>

      {/* Main Grid Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN: INCIDENTS & ALLERGIES (5 / 12) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-xs space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                Theo dõi triệu chứng & sức khỏe
              </h3>
              <span className="text-xs font-medium text-slate-400">
                {filteredIncidents.length} đợt theo dõi
              </span>
            </div>

            {/* 🔔 DAILY HEALTH FOLLOW-UP RECOVERY BANNER */}
            {(() => {
              const activeMonitoringInc = incidents.find(
                (i) => i.status === "Confirmed" && !dismissedReminders.includes(i.id)
              );
              if (!activeMonitoringInc) return null;

              return (
                <div className="bg-amber-50/90 border border-amber-200 p-4 rounded-2xl space-y-2.5 shadow-2xs">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-xl bg-amber-100 text-amber-700 shrink-0">
                        <Bell className="w-4 h-4 animate-bounce" />
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
                          🔔 Nhắc nhở theo dõi sức khỏe cho bé
                        </h4>
                        <p className="text-xs text-amber-800 leading-relaxed pt-0.5">
                          Bé <span className="font-semibold">{activeBaby.name}</span> đã khỏi đợt{" "}
                          <span className="font-semibold text-amber-950">"{activeMonitoringInc.title}"</span> chưa phụ huynh?
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => toggleIncidentStatus(activeMonitoringInc.id)}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3.5 py-1.5 rounded-xl transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      ✓ Bé đã khỏi bệnh
                    </button>

                    <button
                      type="button"
                      onClick={() => setDismissedReminders((prev) => [...prev, activeMonitoringInc.id])}
                      className="bg-white hover:bg-amber-100 text-amber-800 text-xs font-medium px-3 py-1.5 rounded-xl border border-amber-200 transition-all cursor-pointer"
                    >
                      Vẫn đang theo dõi
                    </button>
                  </div>
                </div>
              );
            })()}

            {/* Quick Symptom Filter Chips */}
            <div className="flex flex-wrap items-center gap-1.5 pb-1">
              <span className="text-xs font-medium text-slate-400 mr-1">Lọc:</span>
              <button
                type="button"
                onClick={() => setSelectedSymptomFilter(null)}
                className={`text-xs font-medium px-2.5 py-1 rounded-xl border transition-all cursor-pointer ${selectedSymptomFilter === null
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
                  className={`text-xs font-medium px-2.5 py-1 rounded-xl border transition-all cursor-pointer ${selectedSymptomFilter === sym
                    ? "bg-primary text-white border-primary shadow-xs"
                    : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                    }`}
                >
                  {sym}
                </button>
              ))}
            </div>

            {/* Incident Records List */}
            {filteredIncidents.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-8">
                Chưa có sự cố sức khỏe nào được ghi nhận.
              </p>
            ) : (
              <div className="space-y-3 max-h-[560px] overflow-y-auto pr-1">
                {filteredIncidents.map((inc) => (
                  <div
                    key={inc.id}
                    className="bg-slate-50/80 hover:bg-slate-100/80 p-4 rounded-2xl border border-slate-100 space-y-2.5 transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-800">{inc.title}</span>
                        {inc.temp && (
                          <span
                            className={`text-xs font-semibold px-2 py-0.5 rounded-md ${inc.temp >= 38.5
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
                        className={`text-xs font-semibold px-3 py-1 rounded-xl border transition-all cursor-pointer flex items-center gap-1.5 ${inc.status === "Confirmed"
                          ? "bg-amber-50 hover:bg-emerald-50 text-amber-800 hover:text-emerald-800 border-amber-200 hover:border-emerald-300"
                          : "bg-emerald-100 text-emerald-800 border-emerald-200 shadow-2xs"
                          }`}
                      >
                        {inc.status === "Confirmed" ? (
                          <>
                            <Clock className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                            <span>Đang theo dõi</span>
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                            <span>Đã khỏi bệnh ✓</span>
                          </>
                        )}
                      </button>
                    </div>

                    <div className="flex flex-wrap items-center gap-1.5">
                      {inc.symptoms.map((symptom, idx) => (
                        <span
                          key={idx}
                          className="text-xs font-medium bg-white text-slate-700 px-2.5 py-0.5 rounded-lg border border-slate-200"
                        >
                          {symptom}
                        </span>
                      ))}
                    </div>

                    <p className="text-xs text-slate-600 font-normal leading-relaxed bg-white/70 p-3 rounded-xl border border-slate-100">
                      <span className="font-semibold text-slate-700">Phác đồ xử lý:</span> {inc.treatment}
                    </p>

                    <div className="flex items-center justify-between text-xs text-slate-400 font-normal pt-0.5">
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

          {/* Medication Allergies & Clinical Drug Warnings Card */}
          <div className="bg-white border border-slate-100 rounded-3xl p-5 shadow-xs space-y-3">
            <h3 className="text-xs font-bold text-rose-600 uppercase tracking-wider flex items-center gap-1.5">
              <AlertCircle className="w-4 h-4 text-rose-500" />
              Lưu ý Dị ứng Thuốc & Kháng sinh
            </h3>
            <div className="p-3.5 bg-rose-50/70 border border-rose-100 rounded-2xl space-y-2">
              <div className="flex flex-wrap gap-1.5">
                {(() => {
                  const medAllergies = activeBaby.medicationAllergies && activeBaby.medicationAllergies.length > 0
                    ? activeBaby.medicationAllergies
                    : (activeBaby.allergies ? activeBaby.allergies.filter((a) => a.toLowerCase().includes("cillin") || a.toLowerCase().includes("thuốc") || a.toLowerCase().includes("kháng sinh")) : []);

                  return medAllergies.length > 0 ? (
                    medAllergies.map((alg, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-rose-100 border border-rose-200 text-rose-800 font-semibold rounded-xl text-xs flex items-center gap-1"
                      >
                        🚨 {alg}
                      </span>
                    ))
                  ) : (
                    <span className="px-3 py-1 bg-emerald-50 border border-emerald-200 text-emerald-700 font-semibold rounded-xl text-xs">
                      🌿 Chưa ghi nhận dị ứng thuốc / kháng sinh
                    </span>
                  );
                })()}
              </div>
              <p className="text-xs text-slate-600 leading-relaxed font-normal pt-1">
                {(() => {
                  const medAllergies = activeBaby.medicationAllergies && activeBaby.medicationAllergies.length > 0
                    ? activeBaby.medicationAllergies
                    : (activeBaby.allergies ? activeBaby.allergies.filter((a) => a.toLowerCase().includes("cillin") || a.toLowerCase().includes("thuốc") || a.toLowerCase().includes("kháng sinh")) : []);

                  return medAllergies.length > 0
                    ? `Cảnh báo lâm sàng: Tuyệt đối kiểm tra hoạt chất và tá dược của thuốc trước khi kê toa hoặc cho bé ${activeBaby.name} uống.`
                    : `Hiện tại bé ${activeBaby.name} chưa có tiền sử dị ứng thuốc nào. Bạn có thể cập nhật trong mục Hồ sơ.`;
                })()}
              </p>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: MEDICATION MANAGEMENT HUB (7 / 12) */}
        <div className="lg:col-span-7 space-y-6">
          {/* 3-TAB MEDICATION MANAGEMENT CARD */}
          <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Pill className="w-5 h-5 text-primary" />
                <h3 className="text-sm font-bold text-slate-800">
                  Quản lý đơn thuốc & Lịch uống
                </h3>
              </div>

              <div className="flex items-center bg-slate-100 p-1 rounded-xl">
                {(["today", "cabinet", "history"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setMedTab(tab)}
                    className={`text-xs px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${medTab === tab ? "bg-white text-primary shadow-xs" : "text-slate-600 hover:text-slate-900"}`}
                  >
                    {tab === "today" ? `Hôm nay (${todayDoses.length})` : tab === "cabinet" ? `Tủ thuốc (${medPlans.length})` : "Lịch sử"}
                  </button>
                ))}
              </div>
            </div>

            {/* TAB 1: TODAY'S DOSES */}
            {medTab === "today" && (
              <div className="space-y-4">
                {/* Toast Notification */}
                {syncToast.visible && (
                  <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-2xl text-emerald-800 text-xs font-semibold flex items-center gap-2 shadow-sm animate-fade-in">
                    <CheckCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>{syncToast.message}</span>
                  </div>
                )}

                {todayDoses.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-8">Hôm nay bé chưa có cữ thuốc nào trong phác đồ.</p>
                ) : (
                  todayDoses.map((dose) => {
                    const mealInfo = MEAL_TIMING_MAP[dose.meal_timing] || MEAL_TIMING_MAP.after_food;
                    const isTaken = dose.status === "taken";
                    const isSkipped = dose.status === "skipped";
                    const isSnoozed = dose.status === "snoozed";

                    const timeFormatted = dose.taken_at
                      ? new Date(dose.taken_at).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })
                      : "";

                    return (
                      <div
                        key={dose.dose_id}
                        className={`p-4.5 rounded-2xl border space-y-3 transition-all ${
                          isTaken
                            ? "bg-emerald-50/70 border-emerald-200"
                            : isSkipped
                            ? "bg-slate-50/90 border-dashed border-slate-300"
                            : isSnoozed
                            ? "bg-purple-50/70 border-purple-200"
                            : "bg-white border-slate-200/90 hover:border-primary/40 shadow-xs"
                        }`}
                      >
                        {/* Dose Header & Info */}
                        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                          <div className="space-y-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-xs font-bold text-slate-900">{dose.medication_name}</span>
                              <span className="text-xs font-bold bg-primary/10 text-primary px-2.5 py-0.5 rounded-md">
                                {dose.dose_display}
                              </span>
                              <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-md border ${mealInfo.bg} ${mealInfo.text}`}>
                                {mealInfo.label}
                              </span>
                              <span className="text-xs text-slate-500 font-medium">
                                • {dose.route}
                              </span>
                            </div>
                            {dose.instructions && (
                              <p className="text-[11px] text-slate-500 font-normal">
                                💡 Lời dặn: {dose.instructions}
                              </p>
                            )}
                          </div>

                          {/* Status Badge */}
                          <div>
                            {isTaken ? (
                              <div className="text-right">
                                <span className="text-xs font-bold text-emerald-800 bg-emerald-100/90 border border-emerald-200 px-3 py-1 rounded-xl inline-flex items-center gap-1.5 shadow-2xs">
                                  <CheckCheck className="w-3.5 h-3.5 text-emerald-600" />
                                  <span>Đã cho uống lúc {timeFormatted || dose.scheduled_time}</span>
                                </span>
                                <p className="text-[11px] text-emerald-700 font-medium mt-1">
                                  Ghi nhận bởi: <strong className="font-semibold">{dose.administered_by || "Phụ huynh"}</strong>
                                </p>
                              </div>
                            ) : isSkipped ? (
                              <div className="text-right">
                                <span className="text-xs font-semibold text-slate-600 bg-slate-200/80 px-2.5 py-1 rounded-xl inline-block">
                                  ✕ Đã bỏ qua cữ này
                                </span>
                                <p className="text-[11px] text-slate-500 font-medium mt-1">
                                  Bởi: {dose.administered_by || "Phụ huynh"}
                                </p>
                              </div>
                            ) : isSnoozed ? (
                              <div className="text-right">
                                <span className="text-xs font-semibold text-purple-800 bg-purple-100 border border-purple-200 px-2.5 py-1 rounded-xl inline-block">
                                  ⏰ Đang hoãn nhắc lại (+15p)
                                </span>
                                <p className="text-[11px] text-purple-700 font-medium mt-1">
                                  Bởi: {dose.administered_by || "Phụ huynh"}
                                </p>
                              </div>
                            ) : (
                              <div className="text-right">
                                <span className="text-xs font-bold text-amber-800 bg-amber-100/90 border border-amber-200 px-2.5 py-1 rounded-xl inline-flex items-center gap-1">
                                  <Clock className="w-3.5 h-3.5 text-amber-600" />
                                  <span>Lịch: {dose.scheduled_time}</span>
                                </span>
                                <p className="text-[10px] text-amber-700 font-semibold mt-0.5">
                                  Chờ người chăm sóc xác nhận
                                </p>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Action Buttons Controller */}
                        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100">
                          <span className="text-[11px] text-slate-400 font-normal">
                            {isTaken
                              ? "🌿 Đã đồng bộ với toàn bộ người chăm sóc • Tránh uống lặp lại"
                              : "Yêu cầu xác nhận chủ động từ phụ huynh"}
                          </span>

                          <div className="flex items-center gap-2">
                            {isTaken ? (
                              <button
                                type="button"
                                onClick={() => handleLogDoseAction(dose, "skipped")}
                                className="text-[11px] text-slate-400 hover:text-slate-600 underline cursor-pointer"
                              >
                                Đổi thành bỏ qua
                              </button>
                            ) : (
                              <>
                                <button
                                  type="button"
                                  onClick={() => handleLogDoseAction(dose, "taken")}
                                  className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-xl transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
                                >
                                  <CheckCheck className="w-3.5 h-3.5" />
                                  ✓ Đã cho uống
                                </button>

                                <button
                                  type="button"
                                  onClick={() => handleLogDoseAction(dose, "snoozed")}
                                  className="bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 text-xs font-semibold px-3 py-2 rounded-xl transition-all cursor-pointer"
                                >
                                  ⏰ Nhắc lại 15p
                                </button>

                                <button
                                  type="button"
                                  onClick={() => handleLogDoseAction(dose, "skipped")}
                                  className="bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-medium px-3 py-2 rounded-xl transition-all cursor-pointer"
                                >
                                  ✕ Bỏ qua
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}

            {/* TAB 2: ACTIVE CABINET */}
            {medTab === "cabinet" && (
              <div className="space-y-3">
                {medPlans.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-8">Tủ thuốc của bé đang trống.</p>
                ) : (
                  medPlans.map((plan) => (
                    <div key={plan.id} className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-900">{plan.name}</span>
                          <span className="text-xs font-semibold bg-primary/10 text-primary px-2 py-0.5 rounded-md">
                            {plan.dose} {plan.unit}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => handleUpdatePlanStatus(plan.id, plan.status === "active" ? "completed" : "active")}
                            className="text-xs font-semibold bg-white border border-slate-200 px-2.5 py-1 rounded-lg cursor-pointer"
                          >
                            {plan.status === "active" ? "Hoàn thành" : "Dùng lại"}
                          </button>
                          <button
                            onClick={() => handleDeletePlan(plan.id)}
                            className="p-1 text-slate-400 hover:text-rose-500 cursor-pointer"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                      <p className="text-xs text-slate-600">
                        {plan.frequency} • Giờ: {plan.schedule_times?.join(", ")} • Từ {plan.start_date} ({plan.duration_days} ngày)
                      </p>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* TAB 3: AUDIT HISTORY */}
            {medTab === "history" && (
              <div className="space-y-2.5 max-h-[420px] overflow-y-auto pr-1">
                {doseHistory.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-8">Chưa có lịch sử cữ uống nào được ghi nhận.</p>
                ) : (
                  doseHistory.map((log, idx) => (
                    <div
                      key={log.id || idx}
                      className="bg-slate-50 hover:bg-slate-100/80 p-3.5 rounded-2xl border border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2 transition-all"
                    >
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-800">{log.medication_name}</span>
                          <span className="text-xs font-semibold bg-primary/10 text-primary px-2 py-0.2 rounded-md">
                            {log.dose_taken}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 font-normal">
                          {log.scheduled_date} lúc {log.scheduled_time} • Người cho uống: <strong className="font-semibold text-slate-700">{log.administered_by || "Phụ huynh"}</strong>
                        </p>
                        {log.notes && (
                          <p className="text-[11px] text-slate-400 italic font-normal">
                            Ghi chú: {log.notes}
                          </p>
                        )}
                      </div>

                      <div>
                        {log.status === "taken" ? (
                          <span className="text-xs font-bold text-emerald-800 bg-emerald-100 border border-emerald-200 px-2.5 py-1 rounded-xl inline-flex items-center gap-1">
                            <CheckCheck className="w-3.5 h-3.5 text-emerald-600" /> Đã uống
                          </span>
                        ) : log.status === "snoozed" ? (
                          <span className="text-xs font-semibold text-purple-800 bg-purple-100 border border-purple-200 px-2.5 py-1 rounded-xl inline-flex items-center gap-1">
                            ⏰ Đã hoãn
                          </span>
                        ) : (
                          <span className="text-xs font-semibold text-slate-600 bg-slate-200 px-2.5 py-1 rounded-xl inline-flex items-center gap-1">
                            ✕ Đã bỏ qua
                          </span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* SMART ADD MEDICATION PLAN MODAL */}
      <AnimatePresence>
        {showAddPlanModal && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <Pill className="w-4 h-4 text-primary" />
                  Tạo đơn thuốc cho bé (Chuẩn Y Khoa)
                </h3>
                <button onClick={() => setShowAddPlanModal(false)} className="text-xs font-semibold text-slate-400 cursor-pointer">
                  Hủy
                </button>
              </div>

              {/* Presets */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700">Mẫu thuốc thông dụng:</label>
                <div className="flex flex-wrap gap-1.5">
                  {PRESET_PLANS.map((preset, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSelectPresetPlan(preset)}
                      className="text-xs font-medium bg-slate-100 hover:bg-primary/10 text-slate-700 px-3 py-1 rounded-xl cursor-pointer"
                    >
                      {preset.name} ({preset.dose} {preset.unit})
                    </button>
                  ))}
                </div>
              </div>

              <form onSubmit={handleCreatePlanSubmit} className="space-y-3">
                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-700">Tên thuốc</label>
                  <input
                    type="text"
                    required
                    value={planName}
                    onChange={(e) => setPlanName(e.target.value)}
                    placeholder="VD: Amoxicillin, Hapacol..."
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs"
                  />
                  {/* Allergen clash warning */}
                  {(() => {
                    const medAllergies = activeBaby.medicationAllergies && activeBaby.medicationAllergies.length > 0
                      ? activeBaby.medicationAllergies
                      : (activeBaby.allergies ? activeBaby.allergies.filter((a) => a.toLowerCase().includes("cillin") || a.toLowerCase().includes("thuốc") || a.toLowerCase().includes("kháng sinh")) : []);

                    const match = medAllergies.find((alg) =>
                      planName.toLowerCase().includes(alg.toLowerCase()) || alg.toLowerCase().includes(planName.toLowerCase())
                    );

                    if (match && planName.trim().length > 2) {
                      return (
                        <div className="p-2 bg-rose-50 border border-rose-300 rounded-xl text-rose-800 text-xs flex items-center gap-1.5 font-bold animate-pulse">
                          <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                          <span>CẢNH BÁO: Thuốc này trùng với tiền sử dị ứng "{match}" của bé {activeBaby.name}!</span>
                        </div>
                      );
                    }
                    return null;
                  })()}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="block text-xs font-semibold text-slate-700">Liều mỗi lần</label>
                    <input
                      type="text"
                      required
                      value={planDose}
                      onChange={(e) => setPlanDose(e.target.value)}
                      placeholder="VD: 5, 2.5, 1..."
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="block text-xs font-semibold text-slate-700">Đơn vị</label>
                    <select
                      value={planUnit}
                      onChange={(e) => setPlanUnit(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs"
                    >
                      <option value="mL">mL</option>
                      <option value="gói">gói</option>
                      <option value="giọt">giọt</option>
                      <option value="viên">viên</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="block text-xs font-semibold text-slate-700">Đường dùng</label>
                    <select
                      value={planRoute}
                      onChange={(e) => setPlanRoute(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs"
                    >
                      <option value="Oral (Đường uống)">Uống</option>
                      <option value="Nasal Spray (Xịt mũi)">Xịt mũi</option>
                      <option value="Eye/Ear Drops (Nhỏ mắt/tai)">Nhỏ mắt/tai</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="block text-xs font-semibold text-slate-700">Thời điểm ăn</label>
                    <select
                      value={planMealTiming}
                      onChange={(e) => setPlanMealTiming(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs"
                    >
                      <option value="after_food">Sau ăn 30p</option>
                      <option value="before_food">Trước ăn 30p</option>
                      <option value="with_food">Cùng bữa ăn</option>
                      <option value="when_fever">Khi sốt</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-700">Số ngày dùng</label>
                  <input
                    type="number"
                    value={planDurationDays}
                    onChange={(e) => setPlanDurationDays(Number(e.target.value))}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full bg-primary text-white py-2.5 rounded-xl font-bold text-xs cursor-pointer"
                >
                  Lưu vào tủ thuốc
                </button>
              </form>
            </motion.div>
          </div>
        )}

        {/* SMART ADD INCIDENT MODAL WITH TEMPERATURE PICKER & PRESETS */}
        {showAddIncident && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary" />
                  <h3 className="text-sm font-bold text-slate-800">
                    Ghi Chép Triệu Chứng & Sức Khỏe
                  </h3>
                </div>
                <button onClick={() => setShowAddIncident(false)} className="text-xs font-semibold text-slate-400 cursor-pointer">
                  Hủy
                </button>
              </div>

              {/* ⚡ PRESET ILLNESSES */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700">
                  ⚡ Mẫu tình trạng sức khỏe thông dụng:
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {PRESET_ILLNESSES.map((preset, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSelectPresetIllness(preset)}
                      className="text-xs font-medium bg-slate-100 hover:bg-primary/10 hover:text-primary text-slate-700 px-3 py-1.5 rounded-xl border border-slate-200 transition-all cursor-pointer"
                    >
                      {preset.name}
                    </button>
                  ))}
                </div>
              </div>

              <form onSubmit={handleAddIncidentSubmit} className="space-y-4">
                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-700">Triệu chứng / Tình trạng sức khỏe</label>
                  <input
                    type="text"
                    required
                    value={incidentTitle}
                    onChange={(e) => setIncidentTitle(e.target.value)}
                    placeholder="Ví dụ: Sốt mọc răng, Cảm lạnh sổ mũi..."
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs font-medium text-slate-800 focus:outline-hidden focus:border-primary focus:bg-white transition-all"
                  />
                </div>

                {/* 🌡️ Interactive Temperature Selector */}
                <div className="bg-slate-50 border border-slate-200 p-4 rounded-2xl space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                      <Thermometer className="w-4 h-4 text-primary" />
                      Thân nhiệt đo được (°C):
                    </label>
                    <span
                      className={`text-xs font-bold px-3 py-1 rounded-xl ${incidentTemp >= 38.5
                        ? "bg-rose-100 text-rose-800 border border-rose-300 animate-pulse"
                        : incidentTemp >= 37.5
                          ? "bg-amber-100 text-amber-800 border border-amber-200"
                          : "bg-emerald-100 text-emerald-800 border border-emerald-200"
                        }`}
                    >
                      {incidentTemp}°C - {incidentTemp >= 38.5 ? "SỐT CAO ⚠️" : incidentTemp >= 37.5 ? "Sốt nhẹ" : "Bình thường ✓"}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {[37.0, 37.5, 38.0, 38.5, 39.0, 39.5].map((tempVal) => (
                      <button
                        key={tempVal}
                        type="button"
                        onClick={() => setIncidentTemp(tempVal)}
                        className={`flex-1 py-1.5 text-xs font-semibold rounded-xl border transition-all cursor-pointer ${incidentTemp === tempVal
                          ? "bg-primary text-white border-primary shadow-xs"
                          : "bg-white text-slate-700 border-slate-200 hover:bg-slate-100"
                          }`}
                      >
                        {tempVal}°C
                      </button>
                    ))}
                  </div>
                </div>

                {/* Symptom Chips */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-700">Triệu chứng của bé:</label>
                  <div className="flex flex-wrap gap-1.5">
                    {QUICK_SYMPTOMS.map((sym) => {
                      const isSelected = selectedSymptomChips.includes(sym);
                      return (
                        <button
                          key={sym}
                          type="button"
                          onClick={() => toggleSymptomChip(sym)}
                          className={`text-xs font-medium px-3 py-1.5 rounded-xl border transition-all cursor-pointer ${isSelected
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
                  className="w-full bg-primary hover:bg-primary/95 text-white py-2.5 rounded-xl font-bold text-xs transition-all shadow-xs cursor-pointer"
                >
                  Lưu ghi chép sức khỏe
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
