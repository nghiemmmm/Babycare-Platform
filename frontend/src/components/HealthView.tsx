import React, { useState, useEffect, useMemo } from "react";
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
  Package,
  Wind,
  Smile,
  ChevronDown,
  Zap,
  Sparkle
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

// ─── HEALTH EPISODE & TIME-SERIES HEALTH EVENT INTERFACES ─────────────────────

export interface HealthEvent {
  id?: string;
  episode_id?: string;
  event_type: "measurement" | "symptom_check" | "medication" | "care_action" | "note";
  recorded_at?: string;
  recorded_by_name: string;
  metric_value?: number;
  count_value?: number;
  symptom_name?: string;
  severity?: "mild" | "moderate" | "severe" | "none";
  descriptor?: string;
  action_or_med_name?: string;
  notes?: string;
}

export interface HealthEpisode {
  id: string;
  baby_id?: string;
  category: "respiratory" | "digestive" | "dermatology" | "teething" | "fever" | "general";
  title: string;
  status: "active" | "resolved";
  progress_status: "improving" | "stable" | "worsening";
  started_at?: string;
  resolved_at?: string;
  initial_symptoms?: string[];
  diagnosis?: string;
  treatment?: string;
  doctor_name?: string;
  notes?: string;
  primary_metric_name?: string;
  events?: HealthEvent[];
  events_count?: number;
  latest_event?: HealthEvent;
  progress_summary?: string;
  created_at?: string;
  updated_at?: string;
}

const PRESET_ILLNESSES = [
  {
    category: "fever" as const,
    name: "🌡️ Sốt sau tiêm / Sốt cao",
    defaultTemp: 38.5,
    symptoms: ["🌡️ Sốt cao (>38.5°C)", "😴 Quấy khóc mệt mỏi"],
    treatment: "Uống Paracetamol liều 10-15mg/kg khi sốt >= 38.5°C, chườm ấm trán nách bẹn, cho bé bú nhiều cữ nhỏ."
  },
  {
    category: "respiratory" as const,
    name: "🌬️ Viêm họng / Cảm cúm",
    defaultTemp: 37.8,
    symptoms: ["🌬️ Ho khan", "👃 Sổ mũi", "🥵 Đau họng"],
    treatment: "Dùng siro ho thảo dược, rửa mũi bằng nước muối sinh lý 0.9% ngày 2-3 lần, uống nhiều nước ấm và giữ ấm cổ."
  },
  {
    category: "teething" as const,
    name: "🦷 Mọc răng sưng nướu",
    defaultTemp: 37.4,
    symptoms: ["🦷 Chảy dãi mọc răng", "😴 Quấy khóc mệt mỏi"],
    treatment: "Cho ngậm nướu lạnh sạch, mát-xa nướu nhẹ nhàng, giữ vệ sinh khoang miệng và vỗ về bé."
  },
  {
    category: "digestive" as const,
    name: "💩 Rối loạn tiêu hóa",
    defaultTemp: 37.0,
    symptoms: ["🤮 Nôn mửa", "💩 Tiêu chảy"],
    treatment: "Uống Oresol bù điện giải rải rác từng thìa nhỏ, bổ sung men vi sinh, cho ăn cháo loãng dễ tiêu."
  },
  {
    category: "dermatology" as const,
    name: "🔴 Nổi mẩn / Dị ứng",
    defaultTemp: 37.0,
    symptoms: ["🔴 Nổi mẩn đỏ"],
    treatment: "Giữ da bé sạch thoáng, thoa kem dưỡng ẩm dịu da, tắm nước ấm dịu nhẹ, tránh tiếp xúc chất gây kích ứng."
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
  // ─── HEALTH EPISODES & TIMELINE STATES (CỘT TRÁI) ───────────────────────────
  const [activeEpisode, setActiveEpisode] = useState<HealthEpisode | null>(null);
  const [resolvedEpisodes, setResolvedEpisodes] = useState<HealthEpisode[]>([]);
  const [isLoadingEpisodes, setIsLoadingEpisodes] = useState(false);
  const [showResolvedHistory, setShowResolvedHistory] = useState(false);

  // Form states for creating new episode
  const [showAddIncident, setShowAddIncident] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<"respiratory" | "digestive" | "dermatology" | "teething" | "fever" | "general">("respiratory");
  const [incidentTitle, setIncidentTitle] = useState("");
  const [incidentTemp, setIncidentTemp] = useState<number>(37.5);
  const [selectedSymptomChips, setSelectedSymptomChips] = useState<string[]>([]);
  const [incidentDoctor, setIncidentDoctor] = useState("Bác sĩ nhi khoa");

  // Quick event input state
  const [customEventNote, setCustomEventNote] = useState("");
  const [isSubmittingEvent, setIsSubmittingEvent] = useState(false);

  // ─── MEDICATION MANAGEMENT STATES (CỘT PHẢI) ────────────────────────────────
  const [medTab, setMedTab] = useState<"today" | "cabinet" | "history">("today");
  const [todayDoses, setTodayDoses] = useState<TodayDoseItem[]>([]);
  const [medPlans, setMedPlans] = useState<MedicationPlan[]>([]);
  const [doseHistory, setDoseHistory] = useState<MedicationDoseLog[]>([]);
  const [isLoadingMeds, setIsLoadingMeds] = useState(false);

  // Sắp xếp cữ thuốc hôm nay: Bản ghi sắp đến lịch đẩy lên trên, bản ghi đã uống đẩy xuống dưới
  const sortedTodayDoses = useMemo(() => {
    return [...todayDoses].sort((a, b) => {
      const isCompletedA = a.status === "taken" || a.status === "skipped" ? 1 : 0;
      const isCompletedB = b.status === "taken" || b.status === "skipped" ? 1 : 0;
      if (isCompletedA !== isCompletedB) {
        return isCompletedA - isCompletedB;
      }
      return (a.scheduled_time || "").localeCompare(b.scheduled_time || "");
    });
  }, [todayDoses]);

  const pendingDoses = useMemo(
    () => sortedTodayDoses.filter((d) => d.status !== "taken" && d.status !== "skipped"),
    [sortedTodayDoses]
  );
  const completedDoses = useMemo(
    () => sortedTodayDoses.filter((d) => d.status === "taken" || d.status === "skipped"),
    [sortedTodayDoses]
  );

  // Form states for adding medication plan (GIỮ NGUYÊN 100%)
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

  // Toast Notification for Real-time sync across devices
  const [syncToast, setSyncToast] = useState<{ message: string; visible: boolean }>({ message: "", visible: false });

  const showSyncNotification = (msg: string) => {
    setSyncToast({ message: msg, visible: true });
    setTimeout(() => {
      setSyncToast((prev) => ({ ...prev, visible: false }));
    }, 4500);
  };

  // ─── 1. FETCH HEALTH EPISODES & TIMELINE ───────────────────────────────────

  const fetchHealthEpisodes = async () => {
    if (!activeBaby?.id) return;
    setIsLoadingEpisodes(true);
    try {
      // 1. Fetch active episode with full events timeline
      const activeRes = await apiFetch(`/api/v1/babies/${activeBaby.id}/health-episodes/active`);
      if (activeRes.ok) {
        const data = await activeRes.json();
        setActiveEpisode(data);
      } else {
        setActiveEpisode(null);
      }

      // 2. Fetch resolved episodes list
      const resResolved = await apiFetch(`/api/v1/babies/${activeBaby.id}/health-episodes?status_filter=resolved`);
      if (resResolved.ok) {
        const resData = await resResolved.json();
        setResolvedEpisodes(Array.isArray(resData) ? resData : []);
      }
    } catch (err) {
      console.error("Failed to fetch health episodes:", err);
    } finally {
      setIsLoadingEpisodes(false);
    }
  };

  // ─── 2. FETCH MEDICATION DATA (CỘT PHẢI - GIỮ NGUYÊN) ───────────────────────

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
    fetchHealthEpisodes();
    fetchMedicationData();
  }, [activeBaby?.id]);

  useEffect(() => {
    const handleSync = () => {
      fetchHealthEpisodes();
      fetchMedicationData();
    };
    window.addEventListener("baby-data-updated", handleSync);
    return () => window.removeEventListener("baby-data-updated", handleSync);
  }, [activeBaby?.id]);

  // ─── 3. AI TREATMENT GENERATOR (GIỮ NGUYÊN) ─────────────────────────────────

  const generateAITreatment = (title: string, temp: number, symptoms: string[], category: string = "general") => {
    const parts: string[] = [];

    if (temp >= 39.5) {
      parts.push("⚠️ Sốt nguy hiểm: Chườm ấm toàn thân liên tục và đưa bé đến Bệnh viện Nhi ngay.");
    } else if (temp >= 38.5) {
      parts.push("Cho bé uống Paracetamol liều 10-15mg/kg theo chỉ dẫn và chườm ấm trán, nách, bẹn.");
    } else if (temp >= 37.5) {
      parts.push("Chườm ấm trán nách, giữ phòng thoáng mát và theo dõi thân nhiệt mỗi 30-60 phút.");
    }

    const symText = (title + " " + symptoms.join(" ") + " " + category).toLowerCase();
    if (symText.includes("ho") || symText.includes("họng") || symText.includes("cảm") || category === "respiratory") {
      parts.push("Dùng siro ho thảo dược, nhỏ mũi bằng nước muối sinh lý 0.9% ngày 2-3 lần và cho uống nước ấm.");
    }
    if (symText.includes("sổ mũi") || symText.includes("ngạt")) {
      parts.push("Làm sạch dịch mũi và duy trì độ ẩm phòng 55-60%.");
    }
    if (symText.includes("nôn") || symText.includes("tiêu chảy") || symText.includes("tiêu hóa") || category === "digestive") {
      parts.push("Cho uống Oresol bù điện giải rải rác từng thìa nhỏ trong ngày và ăn thức ăn lỏng dễ tiêu.");
    }
    if (symText.includes("mọc răng") || symText.includes("nướu") || symText.includes("dãi") || category === "teething") {
      parts.push("Cho ngậm nướu lạnh sạch và mát-xa nướu nhẹ nhàng cho bé.");
    }
    if (symText.includes("mẩn") || symText.includes("dị ứng") || symText.includes("chàm") || category === "dermatology") {
      parts.push("Giữ da bé sạch thoáng, thoa kem dưỡng ẩm dịu da và lau người bằng nước ấm dịu nhẹ.");
    }

    if (parts.length === 0) {
      parts.push(`Cho bé ${activeBaby.name} nghỉ ngơi, theo dõi sinh hoạt và cho bú/uống nước đầy đủ.`);
    }

    return parts.join(" ");
  };

  const handleSelectPresetIllness = (preset: typeof PRESET_ILLNESSES[0]) => {
    setSelectedCategory(preset.category);
    setIncidentTitle(preset.name);
    setIncidentTemp(preset.defaultTemp);
    setSelectedSymptomChips(preset.symptoms);
  };

  const toggleSymptomChip = (sym: string) => {
    setSelectedSymptomChips((prev) =>
      prev.includes(sym) ? prev.filter((s) => s !== sym) : [...prev, sym]
    );
  };

  // ─── 4. CREATE NEW HEALTH EPISODE ──────────────────────────────────────────

  const handleCreateEpisodeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!incidentTitle.trim() || !activeBaby?.id) return;

    const symptomsToSave = selectedSymptomChips.length > 0 ? selectedSymptomChips : ["Sức khỏe mệt nhẹ"];
    const aiTreatment = generateAITreatment(incidentTitle, incidentTemp, symptomsToSave, selectedCategory);

    const payload = {
      category: selectedCategory,
      title: incidentTitle.trim(),
      initial_symptoms: symptomsToSave,
      initial_temp: incidentTemp,
      initial_severity: incidentTemp >= 38.5 ? "severe" : "mild",
      initial_descriptor: `Ghi nhận khởi phát: ${symptomsToSave.join(", ")}`,
      treatment: aiTreatment,
      doctor_name: incidentDoctor || "AI Y Khoa Gợi Ý"
    };

    try {
      const res = await apiFetch(`/api/v1/babies/${activeBaby.id}/health-episodes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setShowAddIncident(false);
        setIncidentTitle("");
        setSelectedSymptomChips([]);
        fetchHealthEpisodes();
        window.dispatchEvent(new CustomEvent("baby-data-updated", { detail: { babyId: activeBaby.id } }));
      }
    } catch (err) {
      console.error("Failed to create health episode:", err);
    }
  };

  // ─── 5. QUICK LOG EVENT TO ACTIVE EPISODE ──────────────────────────────────

  const handleLogQuickEvent = async (eventData: Partial<HealthEvent>) => {
    if (!activeEpisode?.id || !activeBaby?.id) return;
    setIsSubmittingEvent(true);
    const actor = authStorage.name || "Phụ huynh";

    try {
      const res = await apiFetch(`/api/v1/babies/${activeBaby.id}/health-episodes/${activeEpisode.id}/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...eventData,
          recorded_by_name: actor,
          recorded_at: new Date().toISOString()
        })
      });
      if (res.ok) {
        fetchHealthEpisodes();
        setCustomEventNote("");
        showSyncNotification(`✓ Đã ghi nhận diễn biến mới cho đợt theo dõi của bé.`);
      }
    } catch (err) {
      console.error("Failed to log quick event:", err);
    } finally {
      setIsSubmittingEvent(false);
    }
  };

  // ─── 6. RESOLVE HEALTH EPISODE (BÉ ĐÃ KHỎI BỆNH) ───────────────────────────

  const handleResolveEpisode = async () => {
    if (!activeEpisode?.id || !activeBaby?.id) return;
    try {
      const res = await apiFetch(`/api/v1/babies/${activeBaby.id}/health-episodes/${activeEpisode.id}/resolve`, {
        method: "PATCH"
      });
      if (res.ok) {
        fetchHealthEpisodes();
        showSyncNotification(`🎉 Tuyệt vời! Bé ${activeBaby.name} đã khỏi bệnh và đợt theo dõi được lưu vào lịch sử.`);
        window.dispatchEvent(new CustomEvent("baby-data-updated", { detail: { babyId: activeBaby.id } }));
      }
    } catch (err) {
      console.error("Failed to resolve episode:", err);
    }
  };

  // ─── 7. LOG DOSE ACTION (CỘT PHẢI - GIỮ NGUYÊN 100%) ───────────────────────

  const handleLogDoseAction = async (
    dose: TodayDoseItem,
    actionStatus: "taken" | "skipped" | "snoozed",
    customNote?: string
  ) => {
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
          `✓ ${actor} đã cho bé uống ${dose.medication_name} (${dose.dose_display}) lúc ${timeStr}. Đã đồng bộ với toàn bộ gia đình!`
        );
      } else if (actionStatus === "snoozed") {
        showSyncNotification(`⏰ ${actor} đã hoãn nhắc nhở cữ thuốc ${dose.medication_name} thêm 15 phút.`);
      } else {
        showSyncNotification(`✕ ${actor} đã ghi nhận bỏ qua cữ ${dose.medication_name}.`);
      }

      fetchMedicationData();
      fetchHealthEpisodes(); // Tự động đồng bộ mốc cữ thuốc sang Timeline đợt bệnh ở Cột Trái!
      window.dispatchEvent(new CustomEvent("baby-data-updated", { detail: { babyId: activeBaby.id } }));
    } catch (err) {
      console.error("Failed to log dose action:", err);
    }
  };

  // Action: Submit Medication Plan (GIỮ NGUYÊN 100%)
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

  // Helper icons for episode category
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "respiratory":
        return <Wind className="w-4 h-4 text-sky-600" />;
      case "digestive":
        return <Droplet className="w-4 h-4 text-amber-600" />;
      case "dermatology":
        return <Heart className="w-4 h-4 text-rose-600" />;
      case "teething":
        return <Sparkle className="w-4 h-4 text-teal-600" />;
      case "fever":
        return <Thermometer className="w-4 h-4 text-red-600" />;
      default:
        return <Activity className="w-4 h-4 text-primary" />;
    }
  };

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case "respiratory": return "Hô hấp / Ho sổ mũi";
      case "digestive": return "Tiêu hóa / Đi ngoài";
      case "dermatology": return "Da liễu / Dị ứng";
      case "teething": return "Mọc răng / Nướu";
      case "fever": return "Sốt / Sau tiêm";
      default: return "Sức khỏe chung";
    }
  };

  // Helper for progress status badge
  const renderProgressBadge = (status: "improving" | "stable" | "worsening") => {
    if (status === "improving") {
      return (
        <span className="px-2.5 py-1 bg-emerald-100 text-emerald-800 border border-emerald-200 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-2xs">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          🌿 Đang thuyên giảm
        </span>
      );
    }
    if (status === "worsening") {
      return (
        <span className="px-2.5 py-1 bg-rose-100 text-rose-800 border border-rose-200 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-2xs">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-bounce" />
          ⚠️ Cần theo dõi thêm
        </span>
      );
    }
    return (
      <span className="px-2.5 py-1 bg-sky-100 text-sky-800 border border-sky-200 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-2xs">
        <span className="w-2 h-2 rounded-full bg-sky-500" />
        ⚖️ Đang ổn định
      </span>
    );
  };

  // Helper render individual dose card
  const renderDoseItem = (dose: TodayDoseItem) => {
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
              ? "🌿 Đã đồng bộ với dòng thời gian theo dõi bệnh • Tránh uống lặp lại"
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
  };

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
              Theo dõi diễn tiến sức khỏe liên tục và quản lý tủ thuốc đúng giờ cho bé{" "}
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
            Theo dõi đợt ốm mới
          </button>
        </div>
      </div>

      {/* Main Grid Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* ═══════════════════════════════════════════════════════════════════ */}
        {/* CỘT TRÁI: HEALTH PROGRESS MONITORING (ĐA BỆNH LÝ & TIMELINE) (5/12) */}
        {/* ═══════════════════════════════════════════════════════════════════ */}
        <div className="lg:col-span-5 space-y-6">
          
          {/* 1. THẺ ĐỢT BỆNH ĐANG HOẠT ĐỘNG (ACTIVE HEALTH EPISODE HUB) */}
          <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-xs space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-primary/10 rounded-xl text-primary">
                  <Activity className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-800">
                    Diễn biến đợt theo dõi sức khỏe
                  </h3>
                  <p className="text-[11px] text-slate-400 font-medium">
                    Theo dõi liên tục và chia sẻ giữa các thành viên gia đình
                  </p>
                </div>
              </div>

              {activeEpisode && (
                renderProgressBadge(activeEpisode.progress_status)
              )}
            </div>

            {/* TRƯỜNG HỢP 1: CÓ ĐỢT BỆNH ĐANG ACTIVE */}
            {activeEpisode ? (
              <div className="space-y-4">
                {/* Header Thẻ Đợt Bệnh */}
                <div className="p-4 bg-gradient-to-br from-slate-50 to-primary/5 rounded-2xl border border-primary/20 space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2.5 py-0.5 bg-white border border-slate-200 rounded-lg text-xs font-bold text-slate-700 flex items-center gap-1.5">
                          {getCategoryIcon(activeEpisode.category)}
                          {getCategoryLabel(activeEpisode.category)}
                        </span>
                        <span className="text-[11px] text-slate-400 font-medium">
                          Bắt đầu: {activeEpisode.started_at ? new Date(activeEpisode.started_at).toLocaleDateString("vi-VN") : "Hôm nay"}
                        </span>
                      </div>
                      <h4 className="text-base font-extrabold text-slate-900 pt-0.5">
                        {activeEpisode.title}
                      </h4>
                    </div>

                    <button
                      type="button"
                      onClick={handleResolveEpisode}
                      className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all shadow-xs shrink-0 cursor-pointer"
                      title="Đánh dấu bé đã khỏi đợt bệnh này"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Bé đã khỏi bệnh</span>
                    </button>
                  </div>

                  {/* 💡 PHÁC ĐỒ XỬ LÝ & LỜI DẶN CHĂM SÓC (GIỮ NGUYÊN & NỔI BẬT) */}
                  {activeEpisode.treatment && (
                    <div className="p-3 bg-white/90 border border-primary/20 rounded-xl space-y-1 shadow-2xs">
                      <div className="text-[11px] font-bold text-primary flex items-center gap-1.5 uppercase tracking-wider">
                        <Sparkles className="w-3.5 h-3.5" /> Phác đồ chăm sóc & Lời dặn theo dõi:
                      </div>
                      <p className="text-xs font-medium text-slate-700 leading-relaxed">
                        {activeEpisode.treatment}
                      </p>
                    </div>
                  )}

                  {/* Tiến triển tóm tắt */}
                  {activeEpisode.progress_summary && (
                    <div className="text-xs text-slate-600 font-medium flex items-center gap-1.5 pt-0.5">
                      <span>💡 Tiến triển:</span>
                      <span className="font-semibold text-slate-800">{activeEpisode.progress_summary}</span>
                    </div>
                  )}
                </div>

                {/* ─── THANH GHI NHANH DIỄN BIẾN (QUICK LOG IN 3 SECONDS) ──── */}
                <div className="space-y-2 pt-1">
                  <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                    <span className="flex items-center gap-1.5">
                      <Zap className="w-3.5 h-3.5 text-amber-500" />
                      Ghi nhanh tiến triển sức khỏe:
                    </span>
                    <span className="text-[10px] text-slate-400 font-normal">Tự động xâu chuỗi vào timeline</span>
                  </div>

                  {/* Chips Ghi Nhanh Thích Ứng Theo Loại Bệnh */}
                  <div className="flex flex-wrap gap-1.5">
                    {activeEpisode.category === "respiratory" && (
                      <>
                        <button
                          type="button"
                          onClick={() => handleLogQuickEvent({ event_type: "symptom_check", symptom_name: "Ho", severity: "moderate", descriptor: "Bé ho có đờm sâu" })}
                          className="px-2.5 py-1.5 bg-slate-100 hover:bg-primary/10 text-slate-700 hover:text-primary rounded-xl text-xs font-medium border border-slate-200 transition-all cursor-pointer"
                        >
                          🌬️ Ho có đờm
                        </button>
                        <button
                          type="button"
                          onClick={() => handleLogQuickEvent({ event_type: "care_action", action_or_med_name: "Rửa mũi nước muối 0.9%", descriptor: "Vệ sinh mũi sạch thoáng" })}
                          className="px-2.5 py-1.5 bg-slate-100 hover:bg-primary/10 text-slate-700 hover:text-primary rounded-xl text-xs font-medium border border-slate-200 transition-all cursor-pointer"
                        >
                          👃 Rửa mũi nước muối
                        </button>
                        <button
                          type="button"
                          onClick={() => handleLogQuickEvent({ event_type: "symptom_check", symptom_name: "Thở", severity: "mild", descriptor: "Tiếng thở êm hơn, bớt khò khè" })}
                          className="px-2.5 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 rounded-xl text-xs font-bold border border-emerald-200 transition-all cursor-pointer"
                        >
                          🌿 Tiếng thở êm hơn
                        </button>
                      </>
                    )}

                    {activeEpisode.category === "digestive" && (
                      <>
                        <button
                          type="button"
                          onClick={() => handleLogQuickEvent({ event_type: "symptom_check", count_value: 1, descriptor: "Đi ngoài phân lỏng nhiều nước" })}
                          className="px-2.5 py-1.5 bg-slate-100 hover:bg-primary/10 text-slate-700 rounded-xl text-xs font-medium border border-slate-200 transition-all cursor-pointer"
                        >
                          💩 Phân lỏng (+1 lần)
                        </button>
                        <button
                          type="button"
                          onClick={() => handleLogQuickEvent({ event_type: "symptom_check", count_value: 1, severity: "mild", descriptor: "Phân sệt có khuôn hơn" })}
                          className="px-2.5 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 rounded-xl text-xs font-bold border border-emerald-200 transition-all cursor-pointer"
                        >
                          💩 Phân sệt cải thiện
                        </button>
                        <button
                          type="button"
                          onClick={() => handleLogQuickEvent({ event_type: "care_action", action_or_med_name: "Uống Oresol bù điện giải", descriptor: "Bù nước rải rác từng thìa nhỏ" })}
                          className="px-2.5 py-1.5 bg-sky-50 hover:bg-sky-100 text-sky-800 rounded-xl text-xs font-bold border border-sky-200 transition-all cursor-pointer"
                        >
                          💧 Bù Oresol
                        </button>
                      </>
                    )}

                    {activeEpisode.category === "dermatology" && (
                      <>
                        <button
                          type="button"
                          onClick={() => handleLogQuickEvent({ event_type: "care_action", action_or_med_name: "Thoa kem dưỡng ẩm dịu da", descriptor: "Thoa lớp mỏng cấp ẩm" })}
                          className="px-2.5 py-1.5 bg-slate-100 hover:bg-primary/10 text-slate-700 rounded-xl text-xs font-medium border border-slate-200 transition-all cursor-pointer"
                        >
                          🧴 Thoa kem ẩm
                        </button>
                        <button
                          type="button"
                          onClick={() => handleLogQuickEvent({ event_type: "symptom_check", severity: "mild", descriptor: "Vết mẩn dịu đỏ, bé bớt ngứa" })}
                          className="px-2.5 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 rounded-xl text-xs font-bold border border-emerald-200 transition-all cursor-pointer"
                        >
                          🌿 Mẩn dịu bớt
                        </button>
                      </>
                    )}

                    {/* Quick Temperature Selector cho mọi bệnh lý */}
                    <div className="flex items-center gap-1 w-full pt-1">
                      <span className="text-[11px] font-semibold text-slate-500 mr-1 flex items-center gap-1">
                        <Thermometer className="w-3.5 h-3.5 text-primary" /> Đo nhiệt:
                      </span>
                      {[37.0, 37.5, 38.0, 38.5, 39.0].map((t) => (
                        <button
                          key={t}
                          type="button"
                          onClick={() => handleLogQuickEvent({
                            event_type: "measurement",
                            metric_value: t,
                            descriptor: t >= 38.5 ? "Sốt cao" : t >= 37.5 ? "Sốt nhẹ" : "Thân nhiệt bình thường"
                          })}
                          className={`px-2 py-1 rounded-lg text-xs font-bold border transition-all cursor-pointer ${
                            t >= 38.5
                              ? "bg-rose-50 hover:bg-rose-100 text-rose-800 border-rose-200"
                              : t >= 37.5
                              ? "bg-amber-50 hover:bg-amber-100 text-amber-800 border-amber-200"
                              : "bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200"
                          }`}
                        >
                          {t}°C
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* ─── DÒNG THỜI GIAN DIỄN TIẾN (EPISODE TIMELINE) ────────── */}
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between text-xs font-bold text-slate-700 border-b border-slate-100 pb-2">
                    <span className="flex items-center gap-1.5">
                      <History className="w-4 h-4 text-primary" />
                      Dòng thời gian diễn tiến ({activeEpisode.events?.length || 0} sự kiện):
                    </span>
                    <span className="text-[10px] text-slate-400">Tự động cập nhật theo giờ</span>
                  </div>

                  {(!activeEpisode.events || activeEpisode.events.length === 0) ? (
                    <p className="text-xs text-slate-400 text-center py-4">Chưa có sự kiện nào trong đợt này.</p>
                  ) : (
                    <div className="space-y-2.5 max-h-[340px] overflow-y-auto pr-1">
                      {activeEpisode.events.map((ev, idx) => {
                        const evTime = ev.recorded_at
                          ? new Date(ev.recorded_at).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })
                          : "Vừa xong";
                        const isMed = ev.event_type === "medication";
                        const isTemp = ev.event_type === "measurement" && ev.metric_value;

                        return (
                          <div
                            key={ev.id || idx}
                            className={`p-3 rounded-2xl border transition-all flex items-start justify-between gap-2.5 ${
                              isMed
                                ? "bg-purple-50/80 border-purple-200/90"
                                : isTemp && ev.metric_value! >= 38.5
                                ? "bg-rose-50/80 border-rose-200"
                                : "bg-slate-50/80 border-slate-200/70"
                            }`}
                          >
                            <div className="space-y-1">
                              <div className="flex flex-wrap items-center gap-1.5">
                                <span className="px-2 py-0.5 bg-white border border-slate-200 rounded-md text-[10px] font-black text-slate-700">
                                  ⏰ {evTime}
                                </span>

                                {isTemp && (
                                  <span className={`px-2 py-0.5 rounded-md text-[10px] font-black ${
                                    ev.metric_value! >= 38.5
                                      ? "bg-rose-100 text-rose-800 border border-rose-300"
                                      : "bg-amber-100 text-amber-800 border border-amber-200"
                                  }`}>
                                    🌡️ {ev.metric_value}°C
                                  </span>
                                )}

                                {isMed && (
                                  <span className="px-2 py-0.5 bg-purple-100 text-purple-900 border border-purple-200 rounded-md text-[10px] font-black flex items-center gap-1">
                                    <Pill className="w-3 h-3 text-purple-600" />
                                    <span>{ev.action_or_med_name || "Uống thuốc"}</span>
                                  </span>
                                )}

                                {ev.count_value && (
                                  <span className="px-2 py-0.5 bg-amber-100 text-amber-900 rounded-md text-[10px] font-bold">
                                    Đi ngoài cữ {ev.count_value}
                                  </span>
                                )}

                                <span className="text-[10px] text-slate-400 font-medium">
                                  • {ev.recorded_by_name}
                                </span>
                              </div>

                              <p className="text-xs font-semibold text-slate-800">
                                {ev.descriptor || ev.notes || ev.symptom_name || "Ghi nhận diễn tiến"}
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* TRƯỜNG HỢP 2: BÉ ĐANG KHỎE MẠNH (KHÔNG CÓ ĐỢT BỆNH ACTIVE) */
              <div className="p-8 text-center bg-emerald-50/60 rounded-2xl border border-emerald-200/80 space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto shadow-2xs">
                  <Heart className="w-6 h-6 fill-emerald-600 text-emerald-600" />
                </div>
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-emerald-950">
                    Bé {activeBaby.name} hiện đang khỏe mạnh!
                  </h4>
                  <p className="text-xs text-emerald-800 font-medium max-w-sm mx-auto">
                    Chưa có đợt bệnh nào cần theo dõi. Khi bé có dấu hiệu sốt, ho, sổ mũi hay rối loạn tiêu hóa, phụ huynh hãy bấm nút bên dưới để bắt đầu theo dõi nhé.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowAddIncident(true)}
                  className="inline-flex items-center gap-1.5 bg-primary hover:bg-primary/95 text-white text-xs font-bold px-4 py-2.5 rounded-xl transition-all shadow-xs cursor-pointer"
                >
                  <Plus className="w-4 h-4" /> Bắt đầu theo dõi đợt ốm mới
                </button>
              </div>
            )}

            {/* ─── LỊCH SỬ CÁC ĐỢT BỆNH ĐÃ KHỎI (RESOLVED HISTORY ACCORDION) ─ */}
            {resolvedEpisodes.length > 0 && (
              <div className="border-t border-slate-100 pt-3 space-y-2">
                <button
                  type="button"
                  onClick={() => setShowResolvedHistory(!showResolvedHistory)}
                  className="w-full flex items-center justify-between text-xs font-bold text-slate-600 hover:text-slate-900 py-1 cursor-pointer"
                >
                  <span className="flex items-center gap-1.5">
                    <CheckCheck className="w-4 h-4 text-emerald-600" />
                    Lịch sử các đợt ốm đã khỏi ({resolvedEpisodes.length} đợt)
                  </span>
                  <ChevronDown className={`w-4 h-4 transition-transform ${showResolvedHistory ? "rotate-180" : ""}`} />
                </button>

                {showResolvedHistory && (
                  <div className="space-y-2 pt-1 max-h-[220px] overflow-y-auto pr-1">
                    {resolvedEpisodes.map((ep) => (
                      <div key={ep.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-800">{ep.title}</span>
                          <span className="text-emerald-700 font-bold text-[10px] bg-emerald-100 px-2 py-0.5 rounded-md">
                            Đã khỏi ✓
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 font-normal">
                          Từ {ep.started_at ? new Date(ep.started_at).toLocaleDateString("vi-VN") : "Gần đây"} • {ep.events_count || 1} mốc theo dõi
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 2. THẺ LƯU Ý DỊ ỨNG THUỐC & KHÁNG SINH (GIỮ NGUYÊN) */}
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

        {/* ═══════════════════════════════════════════════════════════════════ */}
        {/* CỘT PHẢI: TRUNG TÂM QUẢN LÝ THUỐC (GIỮ NGUYÊN HOÀN TOÀN 100%) (7/12) */}
        {/* ═══════════════════════════════════════════════════════════════════ */}
        <div className="lg:col-span-7 space-y-6">
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
                  <div className="space-y-4">
                    {/* NHÓM 1: CÁC CỮ THUỐC SẮP ĐẾN LỊCH UỐNG (ĐẨY LÊN TRÊN CÙNG) */}
                    {pendingDoses.length > 0 && (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                          <span className="flex items-center gap-1.5 text-amber-800">
                            <Clock className="w-3.5 h-3.5 text-amber-600" />
                            Cữ thuốc sắp tới ({pendingDoses.length})
                          </span>
                          <span className="text-[11px] text-slate-400 font-normal">Sắp xếp theo giờ dùng gần nhất</span>
                        </div>
                        {pendingDoses.map((dose) => renderDoseItem(dose))}
                      </div>
                    )}

                    {/* THÔNG BÁO HOÀN THÀNH TẤT CẢ CÁC CỮ TRONG NGÀY */}
                    {pendingDoses.length === 0 && completedDoses.length > 0 && (
                      <div className="p-3.5 bg-emerald-50/90 border border-emerald-200 rounded-2xl flex items-center gap-2 text-emerald-800 text-xs font-semibold">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>Bé đã hoàn thành tất cả các cữ thuốc trong ngày hôm nay! Gia đình tiếp tục theo dõi diễn biến sức khỏe nhé.</span>
                      </div>
                    )}

                    {/* NHÓM 2: CÁC CỮ THUỐC ĐÃ UỐNG / ĐÃ HOÀN THÀNH (ĐẨY XUỐNG DƯỚI) */}
                    {completedDoses.length > 0 && (
                      <div className="space-y-3 pt-2">
                        <div className="flex items-center justify-between text-xs font-bold text-slate-700 border-t border-slate-100 pt-3">
                          <span className="flex items-center gap-1.5 text-emerald-800">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            Đã hoàn thành trong ngày ({completedDoses.length})
                          </span>
                          <span className="text-[11px] text-slate-400 font-normal">Đã xác nhận an toàn</span>
                        </div>
                        {completedDoses.map((dose) => renderDoseItem(dose))}
                      </div>
                    )}
                  </div>
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

      {/* ─── MODAL TẠO ĐƠN THUỐC MỚI (CỘT PHẢI - GIỮ NGUYÊN 100%) ────────────── */}
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
      </AnimatePresence>

      {/* ─── MODAL TẠO ĐỢT THEO DÕI SỨC KHỎE MỚI (CỘT TRÁI) ────────────────── */}
      <AnimatePresence>
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
                    Bắt đầu theo dõi đợt sức khỏe mới
                  </h3>
                </div>
                <button onClick={() => setShowAddIncident(false)} className="text-xs font-semibold text-slate-400 cursor-pointer">
                  Hủy
                </button>
              </div>

              {/* ⚡ PRESET ILLNESSES */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700">
                  ⚡ Chọn mẫu tình trạng sức khỏe thông dụng:
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

              <form onSubmit={handleCreateEpisodeSubmit} className="space-y-4">
                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-700">Tiêu đề đợt theo dõi</label>
                  <input
                    type="text"
                    required
                    value={incidentTitle}
                    onChange={(e) => setIncidentTitle(e.target.value)}
                    placeholder="Ví dụ: Cảm cúm ho sổ mũi, Sốt sau tiêm, Rối loạn tiêu hóa..."
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs font-medium text-slate-800 focus:outline-hidden focus:border-primary focus:bg-white transition-all"
                  />
                </div>

                {/* Nhóm Bệnh Lý */}
                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-700">Nhóm bệnh lý</label>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value as any)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs font-medium text-slate-800"
                  >
                    <option value="respiratory">🌬️ Hô hấp (Ho, Sổ mũi, Cảm cúm)</option>
                    <option value="digestive">💩 Tiêu hóa (Tiêu chảy, Nôn trớ)</option>
                    <option value="dermatology">🔴 Da liễu & Dị ứng (Chàm, Mẩn ngứa)</option>
                    <option value="teething">🦷 Mọc răng & Quấy khóc</option>
                    <option value="fever">🌡️ Sốt & Nhiễm khuẩn / Sau tiêm</option>
                    <option value="general">✨ Sức khỏe chung / Khác</option>
                  </select>
                </div>

                {/* Thân nhiệt ban đầu */}
                <div className="bg-slate-50 border border-slate-200 p-4 rounded-2xl space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                      <Thermometer className="w-4 h-4 text-primary" />
                      Thân nhiệt ban đầu (°C):
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
                  <label className="block text-xs font-semibold text-slate-700">Triệu chứng ban đầu của bé:</label>
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
                  Bắt đầu theo dõi đợt này
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
