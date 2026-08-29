import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  ClipboardList,
  Plus,
  CheckCircle2,
  Clock,
  AlertTriangle,
  User,
  Heart,
  Baby,
  Sparkles,
  MessageSquare,
  Send,
  Trash2,
  RefreshCw,
  Coffee,
  Pill,
  Moon,
  Activity,
  Zap,
  BarChart3,
  Users,
  ArrowRightLeft,
  HandHeart,
  Timer,
  Sparkle
} from "lucide-react";
import { apiFetch } from "../lib/authClient";
import { BabyProfile, Guardian } from "../types";

interface HandoverNote {
  id: string;
  baby_id: string;
  date: string;
  author_name: string;
  recipient_name?: string;
  content: string;
  created_at: string;
}

interface CareTask {
  id: string;
  baby_id: string;
  task_type: string;
  title: string;
  scheduled_time?: string;
  time_mode?: "fixed" | "time_window" | "when_needed" | "flexible";
  time_window_start?: string;
  time_window_end?: string;
  estimated_duration_minutes?: number;
  assigned_name?: string;
  is_unassigned?: boolean;
  backup_assigned_name?: string;
  shift_name?: string;
  original_assigned_name?: string;
  is_temporary_handoff?: boolean;
  handoff_notes?: string;
  instructions?: string;
  target_value?: { amount?: number; unit?: string; [key: string]: any };
  status: "pending" | "due" | "completed" | "skipped" | "overdue" | "escalated";
  priority: string;
  actual_value?: { amount?: number; unit?: string; [key: string]: any };
  completion_notes?: string;
  completed_at?: string;
  completed_by?: string;
  escalated_at?: string;
  escalation_reason?: string;
  is_shift?: boolean;
  shift_activities?: string[];
  break_caregiver_name?: string;
  break_covering_name?: string;
}

interface CareEvent {
  id: string;
  task_id?: string;
  event_type: string;
  occurred_at: string;
  recorded_by_name: string;
  actual_value?: { amount?: number; unit?: string; [key: string]: any };
  notes?: string;
}

interface CaregiverWorkloadItem {
  caregiver_name: string;
  assigned_tasks_count: number;
  completed_tasks_count: number;
  workload_percentage: number;
  completion_rate: number;
}

interface WorkloadStats {
  baby_id: string;
  period_days: number;
  total_tasks_assigned: number;
  total_tasks_completed: number;
  caregivers_distribution: CaregiverWorkloadItem[];
  ai_rebalance_recommendation?: string;
}

interface CareCoordinationViewProps {
  activeBaby: BabyProfile;
  userName?: string;
  guardians?: Guardian[];
}

export default function CareCoordinationView({ activeBaby, userName, guardians }: CareCoordinationViewProps) {
  const [roleMode, setRoleMode] = useState<"parent" | "caregiver">("parent");
  const [isLoading, setIsLoading] = useState(false);

  // Data states
  const [handoverNote, setHandoverNote] = useState<HandoverNote | null>(null);
  const [handoverInput, setHandoverInput] = useState("");
  const [handoverRecipient, setHandoverRecipient] = useState("Tất cả người chăm sóc");
  const [isSavingHandover, setIsSavingHandover] = useState(false);
  const [activeGuardians, setActiveGuardians] = useState<Guardian[]>(guardians || []);

  const [tasks, setTasks] = useState<CareTask[]>([]);
  const [events, setEvents] = useState<CareEvent[]>([]);
  const [aiSummary, setAiSummary] = useState<string>("");
  const [workloadStats, setWorkloadStats] = useState<WorkloadStats | null>(null);

  // Shift & Handoff filter / state
  const [selectedShift, setSelectedShift] = useState<"all" | "Ca Sáng" | "Ca Chiều" | "Ca Đêm">("all");
  const [handoffModalTask, setHandoffModalTask] = useState<CareTask | null>(null);
  const [handoffTargetName, setHandoffTargetName] = useState<string>("");
  const [handoffIsTemporary, setHandoffIsTemporary] = useState<boolean>(true);
  const [handoffReason, setHandoffReason] = useState<string>("");
  const [isHandoffSubmitting, setIsHandoffSubmitting] = useState<boolean>(false);

  // ─── REFACTORED FLEXIBLE MODAL STATES ──────────────────────────────────────────
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [newTaskType, setNewTaskType] = useState<string>("feeding");
  const [newTaskTitle, setNewTaskTitle] = useState<string>("");
  
  // Time flexibility
  const [newTaskTimeMode, setNewTaskTimeMode] = useState<"fixed" | "time_window" | "when_needed" | "flexible">("fixed");
  const [newTaskTime, setNewTaskTime] = useState<string>("14:30");
  const [newTaskWindowStart, setNewTaskWindowStart] = useState<string>("14:00");
  const [newTaskWindowEnd, setNewTaskWindowEnd] = useState<string>("16:00");
  const [newTaskDuration, setNewTaskDuration] = useState<number>(20);

  // Assignment flexibility
  const [newTaskAssigneeMode, setNewTaskAssigneeMode] = useState<"specific" | "unassigned">("specific");
  const [newTaskAssignee, setNewTaskAssignee] = useState<string>("Mẹ");
  const [hasBackup, setHasBackup] = useState<boolean>(false);
  const [newTaskBackupAssignee, setNewTaskBackupAssignee] = useState<string>("Bố");

  // Dynamic values
  const [newTaskAmount, setNewTaskAmount] = useState<number>(150);
  const [newTaskUnit, setNewTaskUnit] = useState<string>("ml");
  const [newTaskMedName, setNewTaskMedName] = useState<string>("");
  const [newTaskDosage, setNewTaskDosage] = useState<string>("1 liều");
  const [newTaskInstructions, setNewTaskInstructions] = useState<string>("");

  // Care Shift specific states
  const [shiftActivities, setShiftActivities] = useState<string[]>([
    "Chăm sóc bé",
    "Cho bú sữa",
    "Thay bỉm",
    "Ru ngủ",
    "Tắm bé"
  ]);
  const [shiftCoveringName, setShiftCoveringName] = useState<string>("Mẹ nghỉ ngơi");

  // Caregiver Break specific states
  const [breakCaregiver, setBreakCaregiver] = useState<string>("Mẹ");
  const [breakCovering, setBreakCovering] = useState<string>("Bố");

  const babyName = activeBaby?.name || "bé";

  // ─── LOAD DATA ─────────────────────────────────────────────────────────────
  const fetchData = async () => {
    if (!activeBaby?.id) return;
    setIsLoading(true);
    try {
      const res = await apiFetch(`/api/v1/care-coordination/summary/daily?baby_id=${activeBaby.id}`);
      if (res.ok) {
        const data = await res.json();
        setHandoverNote(data.handover_note);
        if (data.handover_note?.content) {
          setHandoverInput(data.handover_note.content);
        }
        if (data.handover_note?.recipient_name) {
          setHandoverRecipient(data.handover_note.recipient_name);
        }
        setTasks(data.tasks || []);
        setEvents(data.recent_events || []);
        setAiSummary(data.ai_summary_text || "");
      }

      // Fetch guardians
      const gRes = await apiFetch(`/api/v1/guardians?baby_id=${activeBaby.id}`);
      if (gRes.ok) {
        const gData = await gRes.json();
        if (Array.isArray(gData)) {
          const mappedGuardians = gData.map((g: any) => ({
            id: g.id,
            babyId: activeBaby.id,
            name: g.name || g.relationship || "Người chăm sóc",
            role: g.role || "caregiver",
            relationship: g.relationship || g.role,
            isPrimary: Boolean(g.is_primary),
            email: g.email || "",
            status: g.status || "active"
          }));
          setActiveGuardians(mappedGuardians);
          if (mappedGuardians.length > 0) {
            setNewTaskAssignee(mappedGuardians[0].name);
            setNewTaskBackupAssignee(mappedGuardians[1]?.name || mappedGuardians[0].name);
            setBreakCaregiver(mappedGuardians[0].name);
            setBreakCovering(mappedGuardians[1]?.name || mappedGuardians[0].name);
          }
        }
      }

      // Fetch Workload Analytics
      const wlRes = await apiFetch(`/api/v1/care-coordination/workload-analytics?baby_id=${activeBaby.id}&days=7`);
      if (wlRes.ok) {
        const wlData = await wlRes.json();
        setWorkloadStats(wlData);
      }
    } catch (err) {
      console.error("Error fetching care coordination data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeBaby?.id]);

  // Save Handover Note
  const handleSaveHandover = async () => {
    if (!handoverInput.trim() || !activeBaby?.id) return;
    setIsSavingHandover(true);
    try {
      const res = await apiFetch("/api/v1/care-coordination/handover", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          baby_id: activeBaby.id,
          content: handoverInput.trim(),
          recipient_name: handoverRecipient
        })
      });
      if (res.ok) {
        const saved = await res.json();
        setHandoverNote(saved);
      }
    } catch (err) {
      console.error("Error saving handover note:", err);
    } finally {
      setIsSavingHandover(false);
    }
  };

  // ─── 12 QUICK PRESETS HANDLER ──────────────────────────────────────────────
  const applyPreset = (preset: {
    type: string;
    title: string;
    timeMode?: "fixed" | "time_window" | "when_needed" | "flexible";
    duration?: number;
    amount?: number;
    unit?: string;
    note?: string;
    isShift?: boolean;
  }) => {
    setNewTaskType(preset.type);
    setNewTaskTitle(preset.title);
    setNewTaskTimeMode(preset.timeMode || "fixed");
    setNewTaskDuration(preset.duration || 20);
    if (preset.amount !== undefined) setNewTaskAmount(preset.amount);
    if (preset.unit !== undefined) setNewTaskUnit(preset.unit);
    if (preset.note !== undefined) setNewTaskInstructions(preset.note);
    if (preset.type === "medication") {
      setNewTaskMedName("Vitamin D3 K2");
      setNewTaskDosage("2 giọt");
    }
  };

  // ─── CREATE TASK (SUBMIT) ──────────────────────────────────────────────────
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeBaby?.id) return;

    let finalTitle = newTaskTitle.trim();
    if (!finalTitle) {
      if (newTaskType === "feeding") finalTitle = `Cho bé ${babyName} bú sữa`;
      else if (newTaskType === "diaper") finalTitle = `Thay bỉm cho bé ${babyName}`;
      else if (newTaskType === "sleep") finalTitle = `Ru bé ${babyName} ngủ`;
      else if (newTaskType === "break") finalTitle = `Khoảng nghỉ của ${breakCaregiver}`;
      else if (newTaskType === "shift") finalTitle = `Ca chăm sóc (${newTaskTime})`;
      else finalTitle = `Chăm sóc bé ${babyName}`;
    }

    const isUnassigned = newTaskAssigneeMode === "unassigned";
    const assignedName = isUnassigned ? "Ai rảnh" : newTaskAssignee;

    let targetValue: any = {};
    if (newTaskType === "feeding") {
      targetValue = { amount: newTaskAmount, unit: newTaskUnit };
    } else if (newTaskType === "medication") {
      targetValue = { medication_name: newTaskMedName || "Thuốc", dosage: newTaskDosage || "1 liều" };
    }

    const payload = {
      baby_id: activeBaby.id,
      task_type: newTaskType,
      title: finalTitle,
      time_mode: newTaskTimeMode,
      scheduled_time: newTaskTimeMode === "fixed" ? newTaskTime : undefined,
      time_window_start: newTaskTimeMode === "time_window" ? newTaskWindowStart : undefined,
      time_window_end: newTaskTimeMode === "time_window" ? newTaskWindowEnd : undefined,
      estimated_duration_minutes: newTaskDuration,
      assigned_name: assignedName,
      is_unassigned: isUnassigned,
      backup_assigned_name: hasBackup ? newTaskBackupAssignee : undefined,
      instructions: newTaskInstructions.trim(),
      target_value: targetValue,
      priority: "normal",
      is_shift: newTaskType === "shift",
      shift_activities: newTaskType === "shift" ? shiftActivities : [],
      break_caregiver_name: newTaskType === "break" ? breakCaregiver : undefined,
      break_covering_name: newTaskType === "break" ? breakCovering : undefined
    };

    try {
      const res = await apiFetch("/api/v1/care-coordination/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setIsTaskModalOpen(false);
        setNewTaskTitle("");
        setNewTaskInstructions("");
        fetchData();
      }
    } catch (err) {
      console.error("Error creating task:", err);
    }
  };

  // ─── 1-TAP COMPLETE TASK ───────────────────────────────────────────────────
  const handleCompleteTask = async (taskId: string, actualAmount?: number, actualUnit?: string, notes?: string) => {
    try {
      const res = await apiFetch(`/api/v1/care-coordination/tasks/${taskId}/complete`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          actual_value: actualAmount ? { amount: actualAmount, unit: actualUnit || "ml" } : undefined,
          notes: notes || "Bé ngoan, hoàn thành tốt",
          completed_by_name: roleMode === "caregiver" ? "Người chăm sóc" : (userName || "Mẹ")
        })
      });
      if (res.ok) {
        fetchData();
      }
    } catch (err) {
      console.error("Error completing task:", err);
    }
  };

  // ─── CLAIM TASK ("TÔI SẼ LÀM") ─────────────────────────────────────────────
  const handleClaimTask = async (taskId: string) => {
    try {
      const myName = userName || (activeGuardians[0]?.name || "Bố/Mẹ");
      const res = await apiFetch(`/api/v1/care-coordination/tasks/${taskId}/claim`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ claimed_by_name: myName })
      });
      if (res.ok) {
        fetchData();
      }
    } catch (err) {
      console.error("Error claiming task:", err);
    }
  };

  // ─── HANDOFF / CHUYỂN CA ───────────────────────────────────────────────────
  const handleHandoffSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!handoffModalTask || !handoffTargetName) return;
    setIsHandoffSubmitting(true);
    try {
      const res = await apiFetch(`/api/v1/care-coordination/tasks/${handoffModalTask.id}/handoff`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          new_assignee_name: handoffTargetName,
          is_temporary: handoffIsTemporary,
          reason: handoffReason || (handoffIsTemporary ? "Nhờ chăm sóc hộ tạm thời cữ này" : "Đổi người phụ trách chính")
        })
      });
      if (res.ok) {
        setHandoffModalTask(null);
        setHandoffReason("");
        fetchData();
      }
    } catch (err) {
      console.error("Error handing off task:", err);
    } finally {
      setIsHandoffSubmitting(false);
    }
  };

  // Delete Task
  const handleDeleteTask = async (taskId: string) => {
    try {
      const res = await apiFetch(`/api/v1/care-coordination/tasks/${taskId}`, {
        method: "DELETE"
      });
      if (res.ok) {
        fetchData();
      }
    } catch (err) {
      console.error("Error deleting task:", err);
    }
  };

  // Helper icons
  const getTaskIcon = (type: string) => {
    switch (type) {
      case "break":
        return <Coffee className="w-5 h-5 text-amber-600" />;
      case "feeding":
        return <Baby className="w-5 h-5 text-sky-600" />;
      case "diaper":
        return <Sparkle className="w-5 h-5 text-teal-600" />;
      case "medication":
        return <Pill className="w-5 h-5 text-purple-600" />;
      case "sleep":
        return <Moon className="w-5 h-5 text-indigo-600" />;
      case "hygiene":
        return <Activity className="w-5 h-5 text-teal-600" />;
      case "shift":
        return <Moon className="w-5 h-5 text-purple-600" />;
      default:
        return <Clock className="w-5 h-5 text-slate-500" />;
    }
  };

  const completedCount = tasks.filter((t) => t.status === "completed").length;
  const totalCount = tasks.length;
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <div className="space-y-6 pb-16">
      {/* Header Banner */}
      <div className="bg-white border border-slate-100 rounded-3xl p-6 sm:p-8 shadow-xs flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        <div className="flex items-center gap-3.5">
          <div className="p-3.5 rounded-2xl bg-primary/10 text-primary shrink-0">
            <ClipboardList className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
              Lịch trình chăm sóc bé {babyName}
            </h1>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              Phối hợp chăm sóc linh hoạt, chia sẻ ca trực và bàn giao giữa bố mẹ & người ở nhà
            </p>
          </div>
        </div>

        {/* Role Switcher Pill */}
        <div className="bg-slate-100/80 p-1 rounded-2xl border border-slate-200/60 flex items-center self-start lg:self-auto shadow-2xs">
          <button
            onClick={() => setRoleMode("parent")}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${
              roleMode === "parent"
                ? "bg-primary text-white shadow-xs"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <User className="w-3.5 h-3.5" /> Góc bố mẹ
          </button>
          <button
            onClick={() => setRoleMode("caregiver")}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${
              roleMode === "caregiver"
                ? "bg-amber-500 text-white shadow-xs"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <Heart className="w-3.5 h-3.5" /> Góc người chăm sóc
          </button>
        </div>
      </div>

      {/* Progress & AI Summary Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-5 flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center font-black text-lg shrink-0">
            {completedCount}/{totalCount}
          </div>
          <div className="space-y-0.5">
            <span className="text-xs text-slate-500 font-bold">Tiến độ hôm nay</span>
            <div className="text-xl font-black text-slate-900">
              {progressPercent}% hoàn thành
            </div>
          </div>
        </div>

        <div className="md:col-span-2 bg-amber-50/80 backdrop-blur-xl border border-amber-200/70 shadow-[0_8px_32px_rgba(0,0,0,0.03)] rounded-[32px] p-5 flex items-start gap-3.5">
          <div className="p-2.5 rounded-2xl bg-amber-100 text-amber-700 shrink-0">
            <Sparkles className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h4 className="text-xs font-black uppercase tracking-wider text-amber-900">
              AI trợ lý điều phối chăm sóc
            </h4>
            <p className="text-xs font-medium text-amber-900/90 leading-relaxed">
              {aiSummary || "Hôm nay bé đang có lịch trình chăm sóc ổn định. Bố mẹ hãy linh hoạt san sẻ để ai cũng có thời gian nghỉ ngơi nhé!"}
            </p>
          </div>
        </div>
      </div>

      {/* ─── GÓC BỐ / MẸ: HANDOVER NOTE, TASK TIMELINE & WORKLOAD ANALYTICS ───── */}
      {roleMode === "parent" ? (
        <div className="space-y-6">
          {/* Lời dặn buổi sáng (Handover Note) */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-primary/10 rounded-xl text-primary">
                  <MessageSquare className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-sm font-black text-slate-800">
                    Lời dặn bàn giao buổi sáng cho người ở nhà
                  </h2>
                  <p className="text-xs text-slate-400 font-medium">
                    Dặn dò bà hoặc bảo mẫu những điểm đặc biệt cần lưu ý trong ngày
                  </p>
                </div>
              </div>
              <button
                onClick={handleSaveHandover}
                disabled={isSavingHandover}
                className="inline-flex items-center gap-1.5 bg-primary hover:bg-primary/95 text-white text-xs font-bold px-4 py-2.5 rounded-2xl transition-all shadow-xs cursor-pointer disabled:opacity-50"
              >
                {isSavingHandover ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                Lưu lời dặn
              </button>
            </div>

            <div className="space-y-3">
              <textarea
                value={handoverInput}
                onChange={(e) => setHandoverInput(e.target.value)}
                placeholder="Ví dụ: Hôm nay bé hơi hắt hơi nhẹ, cô nhớ cho bé uống nhiều nước ấm và đo nhiệt độ lúc 10h nhé..."
                rows={3}
                className="w-full p-4 bg-slate-50 border border-slate-200 rounded-2xl text-xs font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all resize-none"
              />
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-slate-500 font-bold">Gửi tới:</span>
                  <select
                    value={handoverRecipient}
                    onChange={(e) => setHandoverRecipient(e.target.value)}
                    className="p-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-700"
                  >
                    <option value="Tất cả người chăm sóc">Tất cả người chăm sóc</option>
                    {activeGuardians.map((g) => (
                      <option key={g.id} value={g.name}>{g.name} ({g.relationship || g.role})</option>
                    ))}
                  </select>
                </div>
                {handoverNote && (
                  <span className="text-[11px] text-emerald-600 font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Đã cập nhật lúc {handoverNote.created_at?.substring(11, 16) || "hôm nay"}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* ─── BẢNG ĐIỀU PHỐI LỊCH TRÌNH LINH HOẠT ────────────────────────── */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-sky-50 rounded-xl text-sky-600">
                  <Clock className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-sm font-black text-slate-800">
                    Lịch trình chăm sóc & Phân chia trách nhiệm
                  </h2>
                  <p className="text-xs text-slate-400 font-medium">
                    Biết rõ ai đang phụ trách bé, linh hoạt nhận việc và bàn giao ca
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    applyPreset({
                      type: "break",
                      title: `Mẹ nghỉ ngơi & Phục hồi`,
                      timeMode: "fixed",
                      duration: 60,
                      note: "Bố hoặc người ở nhà hỗ trợ trông bé trong khung giờ này"
                    });
                    setIsTaskModalOpen(true);
                  }}
                  className="inline-flex items-center gap-1.5 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200/80 text-xs font-bold px-3.5 py-2.5 rounded-2xl transition-all shadow-2xs cursor-pointer"
                  title="Đặt khoảng nghỉ cho người chăm sóc"
                >
                  <Coffee className="w-3.5 h-3.5 text-amber-600" />
                  + Giờ Mẹ nghỉ ngơi
                </button>

                <button
                  onClick={() => {
                    applyPreset({
                      type: "feeding",
                      title: `Cho bé ${babyName} bú sữa`,
                      timeMode: "fixed",
                      duration: 20,
                      amount: 150,
                      unit: "ml",
                      note: "Sữa ấm 40 độ C, vỗ ợ hơi sau khi bú"
                    });
                    setIsTaskModalOpen(true);
                  }}
                  className="inline-flex items-center gap-1.5 bg-primary hover:bg-primary/95 text-white text-xs font-bold px-4 py-2.5 rounded-2xl transition-all shadow-xs cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" /> Thêm việc chăm bé
                </button>
              </div>
            </div>

            {/* Shift Filter Pills */}
            <div className="flex flex-wrap items-center gap-1.5">
              {[
                { label: "🌐 Tất cả", value: "all" },
                { label: "🌅 Ca Sáng (06:00 - 12:00)", value: "Ca Sáng" },
                { label: "☀️ Ca Chiều (12:00 - 18:00)", value: "Ca Chiều" },
                { label: "🌙 Ca Đêm (18:00 - 06:00)", value: "Ca Đêm" }
              ].map((pill) => (
                <button
                  key={pill.value}
                  onClick={() => setSelectedShift(pill.value as any)}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer border ${
                    selectedShift === pill.value
                      ? "bg-slate-900 text-white border-slate-900 shadow-2xs"
                      : "bg-slate-50 hover:bg-slate-100 text-slate-600 border-slate-200"
                  }`}
                >
                  {pill.label}
                </button>
              ))}
            </div>

            {/* Task List */}
            {tasks.length === 0 ? (
              <div className="p-8 text-center bg-slate-50/50 rounded-2xl border border-dashed border-slate-200">
                <Baby className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <div className="text-xs font-bold text-slate-600">Chưa có lịch trình cho hôm nay</div>
                <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto font-medium">
                  Bấm "Thêm việc chăm bé" hoặc chọn một mẫu việc nhanh để bắt đầu theo dõi cùng gia đình.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {(() => {
                  const filteredTasks = tasks.filter((t) => {
                    if (selectedShift === "all") return true;
                    const shift = t.shift_name || "Ca Sáng";
                    return shift === selectedShift;
                  });

                  if (filteredTasks.length === 0) {
                    return (
                      <div className="p-6 text-center bg-slate-50/50 rounded-2xl border border-dashed border-slate-200 text-xs text-slate-400 font-medium">
                        Không có việc nào trong ca này.
                      </div>
                    );
                  }

                  return filteredTasks.map((task) => {
                    const isDone = task.status === "completed";
                    const isOverdue = task.status === "overdue";
                    const isEscalated = task.status === "escalated";
                    const isBreak = task.task_type === "break";
                    const isShift = task.task_type === "shift" || task.is_shift;
                    const isUnassigned = task.is_unassigned || task.assigned_name === "Ai rảnh";

                    // Time display logic
                    let timeLabel = "";
                    if (task.time_mode === "time_window" && task.time_window_start && task.time_window_end) {
                      timeLabel = `⏳ ${task.time_window_start} – ${task.time_window_end}`;
                    } else if (task.time_mode === "when_needed") {
                      timeLabel = "⚡ Khi bé cần";
                    } else if (task.time_mode === "flexible") {
                      timeLabel = "🍃 Linh hoạt";
                    } else {
                      const timeFormatted = task.scheduled_time?.includes("T")
                        ? task.scheduled_time.split("T")[1].substring(0, 5)
                        : task.scheduled_time || "12:00";
                      timeLabel = `⏰ ${timeFormatted}`;
                    }

                    // ─── RENDERING CARE SHIFT CARD ────────────────────────────────
                    if (isShift) {
                      return (
                        <motion.div
                          key={task.id}
                          initial={{ opacity: 0, y: 5 }}
                          animate={{ opacity: 1, y: 0 }}
                          className={`p-5 rounded-3xl border transition-all ${
                            isDone
                              ? "bg-slate-50/70 border-slate-200 opacity-75"
                              : "bg-purple-50/50 border-purple-200/80 shadow-xs hover:shadow-md"
                          }`}
                        >
                          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="space-y-2">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="px-3 py-1 bg-purple-600 text-white rounded-xl text-xs font-black tracking-wide">
                                  🌙 CA CHĂM SÓC
                                </span>
                                <span className="px-2.5 py-1 bg-purple-100 text-purple-900 rounded-xl text-xs font-bold">
                                  {timeLabel}
                                </span>
                                <span className="px-2.5 py-1 bg-white border border-purple-200 text-purple-900 rounded-xl text-xs font-bold">
                                  👤 Người trực: <strong className="text-purple-700">{task.assigned_name || "Bố"}</strong>
                                </span>
                                {task.break_covering_name && (
                                  <span className="px-2.5 py-1 bg-rose-50 text-rose-700 border border-rose-100 rounded-xl text-xs font-bold">
                                    ❤️ {task.break_covering_name}
                                  </span>
                                )}
                              </div>

                              <h3 className="text-sm font-black text-slate-800">{task.title}</h3>

                              {/* Checklist activities inside shift */}
                              {task.shift_activities && task.shift_activities.length > 0 && (
                                <div className="flex flex-wrap gap-1.5 pt-1">
                                  {task.shift_activities.map((act, i) => (
                                    <span key={i} className="px-2.5 py-0.5 bg-white/80 border border-purple-100 rounded-lg text-[11px] font-bold text-slate-600 flex items-center gap-1">
                                      <CheckCircle2 className="w-3 h-3 text-purple-500" /> {act}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>

                            <div className="flex items-center gap-2 self-end md:self-auto shrink-0">
                              {isDone ? (
                                <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-700 px-3 py-2 bg-emerald-50 rounded-xl">
                                  <CheckCircle2 className="w-4 h-4" /> Đã hoàn thành ca
                                </div>
                              ) : (
                                <button
                                  onClick={() => handleCompleteTask(task.id, undefined, undefined, "Đã xong ca trực chu đáo")}
                                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all shadow-xs cursor-pointer"
                                >
                                  <CheckCircle2 className="w-4 h-4" /> Đánh dấu xong ca
                                </button>
                              )}
                              <button
                                onClick={() => handleDeleteTask(task.id)}
                                className="p-2 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-xl transition-all cursor-pointer"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        </motion.div>
                      );
                    }

                    // ─── RENDERING STANDARD & BREAK TASKS ─────────────────────────
                    return (
                      <motion.div
                        key={task.id}
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`p-4 rounded-2xl border transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                          isDone
                            ? "bg-slate-50/60 border-slate-200/80 opacity-75"
                            : isBreak
                            ? "bg-amber-50/70 border-amber-200/80 shadow-2xs"
                            : isOverdue
                            ? "bg-rose-50/80 border-rose-200 shadow-xs"
                            : isEscalated
                            ? "bg-purple-50/80 border-purple-200 shadow-xs"
                            : isUnassigned
                            ? "bg-sky-50/60 border-sky-200 shadow-2xs"
                            : "bg-white/80 border-slate-100 hover:shadow-xs"
                        }`}
                      >
                        <div className="flex items-center gap-3.5">
                          <div className={`p-3 rounded-2xl shrink-0 ${isBreak ? "bg-amber-100" : isUnassigned ? "bg-sky-100" : "bg-slate-100"}`}>
                            {getTaskIcon(task.task_type)}
                          </div>
                          <div>
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="font-bold text-xs text-slate-800">
                                {task.title}
                              </span>

                              {/* Time badge */}
                              <span className="px-2 py-0.5 bg-slate-100 rounded-md text-[10px] font-bold text-slate-600">
                                {timeLabel}
                              </span>

                              {/* Estimated Duration */}
                              {task.estimated_duration_minutes && (
                                <span className="px-2 py-0.5 bg-slate-100 rounded-md text-[10px] font-bold text-slate-500 flex items-center gap-1">
                                  <Timer className="w-3 h-3" /> {task.estimated_duration_minutes}p
                                </span>
                              )}

                              {/* Assignee Badge & Claim Button */}
                              {isUnassigned ? (
                                <span className="px-2.5 py-0.5 bg-sky-100 text-sky-800 border border-sky-200 rounded-md text-[10px] font-extrabold flex items-center gap-1">
                                  <Users className="w-3 h-3" /> Ai rảnh
                                </span>
                              ) : task.is_temporary_handoff && task.original_assigned_name ? (
                                <span className="px-2 py-0.5 bg-purple-100 text-purple-900 border border-purple-200 rounded-md text-[10px] font-bold flex items-center gap-1">
                                  <span>👤 {task.original_assigned_name}</span>
                                  <span>➔</span>
                                  <span className="text-purple-700 font-extrabold">🔄 {task.assigned_name} nhận hộ</span>
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 bg-primary/10 text-primary rounded-md text-[10px] font-bold">
                                  👤 {task.assigned_name || "Người chăm sóc"}
                                </span>
                              )}

                              {isOverdue && (
                                <span className="px-2 py-0.5 bg-rose-100 text-rose-700 font-bold rounded-md text-[10px] flex items-center gap-1">
                                  <AlertTriangle className="w-3 h-3" /> Quá hạn
                                </span>
                              )}
                              {isEscalated && (
                                <span className="px-2 py-0.5 bg-purple-100 text-purple-800 font-bold rounded-md text-[10px] flex items-center gap-1">
                                  <Zap className="w-3 h-3" /> Đã chuyển giao
                                </span>
                              )}
                            </div>

                            {task.instructions && (
                              <p className="text-xs text-slate-500 font-medium mt-1">
                                📝 {task.instructions}
                              </p>
                            )}
                            {task.handoff_notes && task.is_temporary_handoff && (
                              <p className="text-[11px] text-purple-700 font-medium mt-0.5 italic">
                                💬 Lời dặn bàn giao: "{task.handoff_notes}"
                              </p>
                            )}
                            {isDone && task.actual_value?.amount && (
                              <p className="text-xs text-emerald-700 font-bold mt-1">
                                ✓ Thực tế đã thực hiện: {task.actual_value.amount} {task.actual_value.unit || "ml"}
                              </p>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 self-end md:self-auto shrink-0">
                          {/* Nút Claim Task nếu là "Ai rảnh" */}
                          {!isDone && isUnassigned && (
                            <button
                              onClick={() => handleClaimTask(task.id)}
                              className="px-3 py-1.5 bg-sky-500 hover:bg-sky-600 text-white rounded-xl text-xs font-extrabold flex items-center gap-1.5 transition-all shadow-xs cursor-pointer"
                              title="Nhận phụ trách việc này"
                            >
                              <HandHeart className="w-3.5 h-3.5" />
                              <span>Tôi sẽ làm</span>
                            </button>
                          )}

                          {/* Nút Nhờ Trông Hộ / Chuyển Ca */}
                          {!isDone && !isUnassigned && (
                            <button
                              onClick={() => {
                                setHandoffModalTask(task);
                                setHandoffTargetName(task.backup_assigned_name || (activeGuardians[1]?.name || activeGuardians[0]?.name || "Bố"));
                                setHandoffIsTemporary(true);
                                setHandoffReason("");
                              }}
                              className="px-3 py-1.5 bg-purple-50 hover:bg-purple-100 text-purple-800 border border-purple-200/80 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all shadow-2xs cursor-pointer"
                              title="Chuyển giao hoặc nhờ người khác làm hộ cữ này"
                            >
                              <ArrowRightLeft className="w-3.5 h-3.5 text-purple-600" />
                              <span>Nhờ làm hộ</span>
                            </button>
                          )}

                          {isDone ? (
                            <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-700 px-3 py-1.5 bg-emerald-50 rounded-xl">
                              <CheckCircle2 className="w-4 h-4" /> Đã xong
                            </div>
                          ) : (
                            <button
                              onClick={() => handleCompleteTask(task.id, task.target_value?.amount, task.target_value?.unit)}
                              className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all shadow-xs cursor-pointer"
                            >
                              <CheckCircle2 className="w-4 h-4" /> Đánh dấu xong
                            </button>
                          )}
                          <button
                            onClick={() => handleDeleteTask(task.id)}
                            className="p-2 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-xl transition-all cursor-pointer"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </motion.div>
                    );
                  });
                })()}
              </div>
            )}
          </div>

          {/* ─── WORKLOAD ANALYTICS ────────────────────────────────────────────── */}
          {workloadStats && (
            <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-indigo-50 rounded-xl text-indigo-600">
                    <BarChart3 className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="text-sm font-black text-slate-800">
                      Phân bổ khối lượng chăm sóc gia đình (7 ngày qua)
                    </h2>
                    <p className="text-xs text-slate-400 font-medium">
                      Minh bạch hóa nỗ lực chăm sóc của từng thành viên để cùng nhau chia sẻ
                    </p>
                  </div>
                </div>
                <div className="text-xs font-bold text-primary bg-primary/10 px-3 py-1.5 rounded-xl">
                  Tổng: {workloadStats.total_tasks_completed}/{workloadStats.total_tasks_assigned} cữ
                </div>
              </div>

              {/* Caregivers Distribution Bars */}
              <div className="space-y-3">
                {workloadStats.caregivers_distribution.map((item, idx) => (
                  <div key={idx} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                      <span className="flex items-center gap-1.5">
                        <Users className="w-3.5 h-3.5 text-slate-400" />
                        {item.caregiver_name}
                      </span>
                      <span>
                        {item.completed_tasks_count}/{item.assigned_tasks_count} việc ({item.workload_percentage}%)
                      </span>
                    </div>
                    <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-primary to-sky-400 rounded-full transition-all duration-500"
                        style={{ width: `${item.workload_percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* AI Workload Recommendation */}
              {workloadStats.ai_rebalance_recommendation && (
                <div className="p-4 bg-indigo-50/70 border border-indigo-100 rounded-2xl flex items-start gap-3">
                  <Sparkles className="w-4 h-4 text-indigo-600 mt-0.5 shrink-0" />
                  <p className="text-xs font-medium text-indigo-950 leading-relaxed">
                    {workloadStats.ai_rebalance_recommendation}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        /* ─── GÓC NGƯỜI CHĂM SÓC (ÔNG / BÀ / BẢO MẪU): 1-TAP EXECUTION ────────── */
        <div className="space-y-6">
          {/* Lời dặn to rõ của Bố/Mẹ */}
          {handoverNote && handoverNote.content && (
            <div className="bg-amber-50/90 border border-amber-200 p-6 rounded-[32px] space-y-2 shadow-2xs">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-900">
                <Heart className="w-4 h-4 fill-amber-700 text-amber-700" /> Lời dặn của mẹ dành cho người ở nhà hôm nay:
              </div>
              <p className="text-sm sm:text-base font-bold text-amber-950 leading-relaxed">
                "{handoverNote.content}"
              </p>
            </div>
          )}

          {/* Checklist Cực Lớn & Rõ Ràng */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 md:p-8 space-y-6">
            <div>
              <h2 className="text-lg sm:text-xl font-black text-slate-900">
                Danh sách việc cần làm cho bé {babyName}
              </h2>
              <p className="text-xs text-slate-500 font-medium mt-0.5">
                Chỉ cần bấm nút khi đã cho bé ăn, uống thuốc hoặc ngủ xong
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {tasks.map((task) => {
                const isDone = task.status === "completed";
                const isShift = task.task_type === "shift" || task.is_shift;
                const isUnassigned = task.is_unassigned || task.assigned_name === "Ai rảnh";

                let timeDisplay = "";
                if (task.time_mode === "time_window" && task.time_window_start) {
                  timeDisplay = `${task.time_window_start} – ${task.time_window_end}`;
                } else if (task.time_mode === "when_needed") {
                  timeDisplay = "Khi bé cần";
                } else if (task.time_mode === "flexible") {
                  timeDisplay = "Linh hoạt";
                } else {
                  timeDisplay = task.scheduled_time?.includes("T")
                    ? task.scheduled_time.split("T")[1].substring(0, 5)
                    : task.scheduled_time || "12:00";
                }

                return (
                  <div
                    key={task.id}
                    className={`p-6 rounded-3xl border transition-all ${
                      isDone
                        ? "bg-slate-50/70 border-slate-200/80 opacity-60"
                        : isShift
                        ? "bg-purple-50/80 border-purple-200 shadow-xs"
                        : "bg-white/90 border-slate-200 shadow-xs hover:border-primary/40"
                    }`}
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center gap-3">
                          <span className="px-3 py-1 bg-primary text-white rounded-xl font-black text-sm">
                            ⏰ {timeDisplay}
                          </span>
                          <span className="text-base font-black text-slate-900">
                            {task.title}
                          </span>
                        </div>
                        {task.instructions && (
                          <p className="text-xs text-slate-600 font-medium">
                            📝 {task.instructions}
                          </p>
                        )}
                        {task.handoff_notes && (
                          <p className="text-xs text-purple-700 font-medium italic">
                            💬 Lời dặn bàn giao: "{task.handoff_notes}"
                          </p>
                        )}
                        {isUnassigned && (
                          <span className="inline-flex items-center gap-1 text-xs font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded-md">
                            👥 Ai rảnh làm hộ
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        {isDone ? (
                          <div className="px-5 py-3 bg-emerald-100 text-emerald-800 rounded-2xl font-black text-xs flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4" /> ĐÃ XONG
                          </div>
                        ) : (
                          <button
                            onClick={() => handleCompleteTask(task.id, task.target_value?.amount, task.target_value?.unit)}
                            className="px-6 py-3.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl font-black text-sm flex items-center gap-2 transition-all shadow-md active:scale-95 cursor-pointer"
                          >
                            <CheckCircle2 className="w-5 h-5" /> BẤM KHI XONG
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ─── REFACTORED FLEXIBLE ADD CARE TASK MODAL ───────────────────────── */}
      <AnimatePresence>
        {isTaskModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-lg w-full p-6 space-y-5 shadow-2xl border border-slate-100 my-8 max-h-[90vh] overflow-y-auto"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h3 className="text-sm font-black text-slate-800">Thêm việc chăm sóc cho bé</h3>
                  <p className="text-[11px] text-slate-400 font-medium">Bé {babyName}</p>
                </div>
                <button
                  onClick={() => setIsTaskModalOpen(false)}
                  className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg cursor-pointer"
                >
                  ✕
                </button>
              </div>

              {/* ─── 12 QUICK PRESETS (PRIMARY INTERACTION) ───────────────── */}
              <div className="space-y-1.5">
                <label className="text-[11px] font-bold text-slate-500 block">
                  ⚡ Chọn nhanh mẫu công việc (1-Chạm tự điền):
                </label>
                <div className="grid grid-cols-3 sm:grid-cols-4 gap-1.5">
                  {[
                    { label: "🍼 Cho bú", type: "feeding", title: `Cho bé ${babyName} bú sữa`, duration: 20, amount: 150, unit: "ml", note: "Sữa ấm 40 độ C, vỗ ợ hơi sau khi bú" },
                    { label: "🧷 Thay bỉm", type: "diaper", title: `Thay bỉm cho bé ${babyName}`, duration: 10, timeMode: "when_needed" as const, note: "Thoa kem chống hăm sau khi vệ sinh" },
                    { label: "😴 Ru ngủ", type: "sleep", title: `Ru bé ${babyName} ngủ`, duration: 30, timeMode: "time_window" as const, note: "Bật tiếng ồn trắng và hạ đèn phòng" },
                    { label: "🛁 Tắm bé", type: "hygiene", title: `Tắm bé & massage ấm`, duration: 30, timeMode: "time_window" as const, note: "Pha nước ấm 37 độ C, thoa dầu tràm giữ ấm" },
                    { label: "🥣 Cho ăn dặm", type: "feeding", title: `Cho bé ${babyName} ăn dặm`, duration: 30, amount: 1, unit: "bát", note: "Cháo ấm mịn, cho bé ngồi ghế ăn" },
                    { label: "💊 Thuốc / Vitamin", type: "medication", title: "Uống thuốc / Vitamin D3", duration: 10, note: "Cho bé uống đúng liều bác sĩ kê" },
                    { label: "🍼 Rửa bình", type: "custom", title: "Rửa & tiệt trùng bình sữa", duration: 15, timeMode: "flexible" as const, note: "Tiệt trùng hơi nước 15 phút" },
                    { label: "🧸 Chơi với bé", type: "activity", title: `Tương tác & chơi cùng bé ${babyName}`, duration: 30, timeMode: "flexible" as const, note: "Đọc sách tranh hoặc tập lẫy/tummy time" },
                    { label: "🚶 Đi dạo", type: "activity", title: `Đẩy xe cho bé ${babyName} dạo mát`, duration: 30, timeMode: "time_window" as const, note: "Đội mũ che nắng nhẹ" },
                    { label: "❤️ Mẹ nghỉ ngơi", type: "break", title: `Mẹ nghỉ ngơi & Phục hồi`, duration: 60, timeMode: "fixed" as const, note: "Bố hoặc người ở nhà hỗ trợ trông bé trong khung giờ này" },
                    { label: "🌙 Ca chăm sóc", type: "shift", title: `Ca chăm sóc (${newTaskTime})`, duration: 300, timeMode: "time_window" as const, isShift: true },
                    { label: "✨ Khác", type: "custom", title: "", duration: 20, timeMode: "flexible" as const }
                  ].map((preset) => (
                    <button
                      key={preset.label}
                      type="button"
                      onClick={() => applyPreset(preset)}
                      className={`px-2 py-2 rounded-xl text-[11px] font-bold border transition-all text-center flex flex-col items-center justify-center gap-0.5 cursor-pointer ${
                        newTaskType === preset.type && newTaskTitle === preset.title
                          ? "bg-primary text-white border-primary shadow-xs"
                          : "border-slate-200 bg-slate-50 hover:bg-primary/10 hover:text-primary hover:border-primary/30"
                      }`}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>

              <form onSubmit={handleCreateTask} className="space-y-4">
                {/* ─── SPECIAL LAYOUT: CARE SHIFT (CA CHĂM SÓC) ─────────────── */}
                {newTaskType === "shift" ? (
                  <div className="p-4 bg-purple-50/70 border border-purple-200 rounded-2xl space-y-3">
                    <div className="flex items-center gap-2 text-purple-900 font-extrabold text-xs">
                      <Moon className="w-4 h-4 text-purple-600" />
                      Thiết lập Ca chăm sóc chuyên biệt
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <label className="block text-slate-700 font-bold mb-1">Khung giờ bắt đầu</label>
                        <input
                          type="time"
                          value={newTaskWindowStart}
                          onChange={(e) => setNewTaskWindowStart(e.target.value)}
                          className="w-full p-2.5 bg-white border border-purple-200 rounded-xl font-bold text-slate-800"
                        />
                      </div>
                      <div>
                        <label className="block text-slate-700 font-bold mb-1">Khung giờ kết thúc</label>
                        <input
                          type="time"
                          value={newTaskWindowEnd}
                          onChange={(e) => setNewTaskWindowEnd(e.target.value)}
                          className="w-full p-2.5 bg-white border border-purple-200 rounded-xl font-bold text-slate-800"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-slate-700 font-bold mb-1 text-xs">Người phụ trách chính ca này:</label>
                      <select
                        value={newTaskAssignee}
                        onChange={(e) => setNewTaskAssignee(e.target.value)}
                        className="w-full p-2.5 bg-white border border-purple-200 rounded-xl text-xs font-bold text-slate-800"
                      >
                        {activeGuardians.map((g) => (
                          <option key={g.id} value={g.name}>{g.name} ({g.relationship || g.role})</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-slate-700 font-bold mb-1 text-xs">Hoạt động bao gồm trong ca:</label>
                      <div className="grid grid-cols-2 gap-1.5">
                        {["Chăm sóc bé", "Cho bú sữa", "Thay bỉm", "Ru ngủ", "Tắm bé", "Chơi với bé"].map((act) => (
                          <label key={act} className="flex items-center gap-2 p-2 bg-white rounded-xl border border-purple-100 text-xs font-medium text-slate-700 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={shiftActivities.includes(act)}
                              onChange={(e) => {
                                if (e.target.checked) setShiftActivities([...shiftActivities, act]);
                                else setShiftActivities(shiftActivities.filter((a) => a !== act));
                              }}
                              className="rounded text-purple-600"
                            />
                            {act}
                          </label>
                        ))}
                      </div>
                    </div>

                    <div>
                      <label className="block text-slate-700 font-bold mb-1 text-xs">Thành viên còn lại:</label>
                      <input
                        type="text"
                        value={shiftCoveringName}
                        onChange={(e) => setShiftCoveringName(e.target.value)}
                        placeholder="Mẹ nghỉ ngơi / Việc cá nhân"
                        className="w-full p-2.5 bg-white border border-purple-200 rounded-xl text-xs font-medium"
                      />
                    </div>
                  </div>
                ) : newTaskType === "break" ? (
                  /* ─── SPECIAL LAYOUT: CAREGIVER BREAK (MẸ NGHỈ NGƠI) ───────── */
                  <div className="p-4 bg-amber-50/70 border border-amber-200 rounded-2xl space-y-3">
                    <div className="flex items-center gap-2 text-amber-900 font-extrabold text-xs">
                      <Coffee className="w-4 h-4 text-amber-600" />
                      Khoảng nghỉ ngơi & Phục hồi năng lượng
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <label className="block text-slate-700 font-bold mb-1">Người được nghỉ ngơi</label>
                        <select
                          value={breakCaregiver}
                          onChange={(e) => setBreakCaregiver(e.target.value)}
                          className="w-full p-2.5 bg-white border border-amber-200 rounded-xl font-bold text-slate-800"
                        >
                          {activeGuardians.map((g) => (
                            <option key={g.id} value={g.name}>{g.name} ({g.relationship || g.role})</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-slate-700 font-bold mb-1">Người chăm bé thay thế</label>
                        <select
                          value={breakCovering}
                          onChange={(e) => setBreakCovering(e.target.value)}
                          className="w-full p-2.5 bg-white border border-amber-200 rounded-xl font-bold text-slate-800"
                        >
                          {activeGuardians.map((g) => (
                            <option key={g.id} value={g.name}>{g.name} ({g.relationship || g.role})</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <label className="block text-slate-700 font-bold mb-1">Bắt đầu lúc</label>
                        <input
                          type="time"
                          value={newTaskTime}
                          onChange={(e) => setNewTaskTime(e.target.value)}
                          className="w-full p-2.5 bg-white border border-amber-200 rounded-xl font-medium"
                        />
                      </div>
                      <div>
                        <label className="block text-slate-700 font-bold mb-1">Thời lượng nghỉ</label>
                        <select
                          value={newTaskDuration}
                          onChange={(e) => setNewTaskDuration(Number(e.target.value))}
                          className="w-full p-2.5 bg-white border border-amber-200 rounded-xl font-medium"
                        >
                          <option value={30}>30 phút</option>
                          <option value={60}>1 tiếng (Khuyến nghị)</option>
                          <option value={90}>1 tiếng 30 phút</option>
                          <option value={120}>2 tiếng</option>
                        </select>
                      </div>
                    </div>
                  </div>
                ) : (
                  /* ─── STANDARD PROGRESSIVE DISCLOSURE FORM ─────────────────── */
                  <>
                    {/* Tên việc cần làm */}
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">Tên việc cần làm</label>
                      <input
                        type="text"
                        required
                        value={newTaskTitle}
                        onChange={(e) => setNewTaskTitle(e.target.value)}
                        placeholder={`Ví dụ: Cho bé ${babyName} bú sữa...`}
                        className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:bg-white"
                      />
                    </div>

                    {/* ─── TIME FLEXIBILITY SECTION ─────────────────────────── */}
                    <div className="space-y-2">
                      <label className="block text-xs font-bold text-slate-700">Thời gian thực hiện:</label>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
                        {[
                          { id: "fixed", label: "⏰ Theo lịch" },
                          { id: "time_window", label: "⏳ Trong khoảng" },
                          { id: "when_needed", label: "⚡ Khi bé cần" },
                          { id: "flexible", label: "🍃 Linh hoạt" }
                        ].map((m) => (
                          <button
                            key={m.id}
                            type="button"
                            onClick={() => setNewTaskTimeMode(m.id as any)}
                            className={`p-2 rounded-xl text-[11px] font-bold border transition-all text-center cursor-pointer ${
                              newTaskTimeMode === m.id
                                ? "bg-slate-900 text-white border-slate-900 shadow-2xs"
                                : "bg-slate-50 hover:bg-slate-100 text-slate-600 border-slate-200"
                            }`}
                          >
                            {m.label}
                          </button>
                        ))}
                      </div>

                      {/* Time Details based on Mode */}
                      {newTaskTimeMode === "fixed" && (
                        <div className="pt-1">
                          <input
                            type="time"
                            value={newTaskTime}
                            onChange={(e) => setNewTaskTime(e.target.value)}
                            className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium"
                          />
                        </div>
                      )}

                      {newTaskTimeMode === "time_window" && (
                        <div className="grid grid-cols-2 gap-2 pt-1">
                          <div>
                            <span className="text-[10px] text-slate-500 font-bold block mb-0.5">Từ mốc giờ:</span>
                            <input
                              type="time"
                              value={newTaskWindowStart}
                              onChange={(e) => setNewTaskWindowStart(e.target.value)}
                              className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium"
                            />
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-500 font-bold block mb-0.5">Đến mốc giờ:</span>
                            <input
                              type="time"
                              value={newTaskWindowEnd}
                              onChange={(e) => setNewTaskWindowEnd(e.target.value)}
                              className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium"
                            />
                          </div>
                        </div>
                      )}

                      {(newTaskTimeMode === "when_needed" || newTaskTimeMode === "flexible") && (
                        <p className="text-[11px] text-slate-500 font-medium italic bg-slate-50 p-2 rounded-xl border border-slate-200/60">
                          💡 Việc này không bắt buộc giờ cố định. Bất kỳ ai rảnh hoặc khi bé có nhu cầu đều có thể thực hiện và bấm hoàn thành.
                        </p>
                      )}
                    </div>

                    {/* ─── ASSIGNMENT FLEXIBILITY SECTION ───────────────────── */}
                    <div className="space-y-2">
                      <label className="block text-xs font-bold text-slate-700">Ai phụ trách?</label>
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          type="button"
                          onClick={() => setNewTaskAssigneeMode("specific")}
                          className={`p-2.5 rounded-xl text-xs font-bold border transition-all text-center cursor-pointer ${
                            newTaskAssigneeMode === "specific"
                              ? "bg-primary text-white border-primary shadow-xs"
                              : "bg-slate-50 text-slate-600 border-slate-200"
                          }`}
                        >
                          👤 Người cụ thể
                        </button>
                        <button
                          type="button"
                          onClick={() => setNewTaskAssigneeMode("unassigned")}
                          className={`p-2.5 rounded-xl text-xs font-bold border transition-all text-center cursor-pointer ${
                            newTaskAssigneeMode === "unassigned"
                              ? "bg-sky-600 text-white border-sky-600 shadow-xs"
                              : "bg-slate-50 text-slate-600 border-slate-200"
                          }`}
                        >
                          👥 Ai rảnh làm hộ
                        </button>
                      </div>

                      {newTaskAssigneeMode === "specific" && (
                        <select
                          value={newTaskAssignee}
                          onChange={(e) => setNewTaskAssignee(e.target.value)}
                          className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium"
                        >
                          {activeGuardians.map((g) => (
                            <option key={g.id} value={g.name}>{g.name} ({g.relationship || g.role})</option>
                          ))}
                        </select>
                      )}
                    </div>

                    {/* ─── DYNAMIC FIELDS (FEEDING / MEDICATION / DURATION) ─── */}
                    {newTaskType === "feeding" && (
                      <div>
                        <label className="block text-xs font-bold text-slate-700 mb-1">Khẩu phần ăn / bú</label>
                        <div className="flex gap-2">
                          <input
                            type="number"
                            value={newTaskAmount}
                            onChange={(e) => setNewTaskAmount(Number(e.target.value))}
                            placeholder="150"
                            className="w-2/3 p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium"
                          />
                          <input
                            type="text"
                            value={newTaskUnit}
                            onChange={(e) => setNewTaskUnit(e.target.value)}
                            placeholder="ml"
                            className="w-1/3 p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-center"
                          />
                        </div>
                      </div>
                    )}

                    {newTaskType === "medication" && (
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-xs font-bold text-slate-700 mb-1">Tên thuốc / Vitamin</label>
                          <input
                            type="text"
                            value={newTaskMedName}
                            onChange={(e) => setNewTaskMedName(e.target.value)}
                            placeholder="Vitamin D3 K2"
                            className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-bold text-slate-700 mb-1">Liều lượng</label>
                          <input
                            type="text"
                            value={newTaskDosage}
                            onChange={(e) => setNewTaskDosage(e.target.value)}
                            placeholder="2 giọt / 1 gói"
                            className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium"
                          />
                        </div>
                      </div>
                    )}

                    {/* Thời gian dự kiến (Duration) */}
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">⏱️ Thời gian thực hiện dự kiến:</label>
                      <div className="flex items-center gap-2">
                        {[10, 20, 30, 45, 60].map((d) => (
                          <button
                            key={d}
                            type="button"
                            onClick={() => setNewTaskDuration(d)}
                            className={`px-3 py-1.5 rounded-xl text-xs font-bold border transition-all cursor-pointer ${
                              newTaskDuration === d
                                ? "bg-slate-800 text-white border-slate-800"
                                : "bg-slate-50 text-slate-600 border-slate-200"
                            }`}
                          >
                            {d}p
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* ─── OPTIONAL BACKUP TOGGLE ───────────────────────────── */}
                    <div className="pt-1 border-t border-slate-100">
                      <label className="flex items-center gap-2 text-xs font-bold text-slate-700 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={hasBackup}
                          onChange={(e) => setHasBackup(e.target.checked)}
                          className="rounded text-primary"
                        />
                        <span>Có người hỗ trợ khi cần (Hỗ trợ dự phòng)</span>
                      </label>

                      {hasBackup && (
                        <div className="mt-2 pl-5">
                          <select
                            value={newTaskBackupAssignee}
                            onChange={(e) => setNewTaskBackupAssignee(e.target.value)}
                            className="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium"
                          >
                            {activeGuardians.map((g) => (
                              <option key={g.id} value={g.name}>{g.name} ({g.relationship || g.role})</option>
                            ))}
                          </select>
                        </div>
                      )}
                    </div>

                    {/* Hướng dẫn chi tiết */}
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">Hướng dẫn chi tiết (Ghi chú)</label>
                      <textarea
                        value={newTaskInstructions}
                        onChange={(e) => setNewTaskInstructions(e.target.value)}
                        placeholder="Ví dụ: Sữa ấm 40 độ, cho bé ợ hơi sau bú..."
                        rows={2}
                        className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium resize-none"
                      />
                    </div>
                  </>
                )}

                {/* Submit & Cancel Buttons */}
                <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setIsTaskModalOpen(false)}
                    className="px-4 py-2.5 text-slate-500 hover:bg-slate-100 rounded-2xl text-xs font-bold cursor-pointer"
                  >
                    Hủy
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2.5 bg-primary hover:bg-primary/95 text-white rounded-2xl text-xs font-bold shadow-xs cursor-pointer"
                  >
                    {newTaskType === "shift" ? "Tạo Ca chăm sóc" : newTaskType === "break" ? "Thiết lập Giờ nghỉ" : "Tạo việc chăm sóc"}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ─── MODAL CHUYỂN GIAO / NHỜ LÀM HỘ TẠM THỜI (HANDOFF MODAL) ─────────── */}
      <AnimatePresence>
        {handoffModalTask && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl border border-slate-100"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-purple-100 text-purple-700 rounded-xl">
                    <ArrowRightLeft className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-black text-slate-800">Nhờ làm hộ / Chuyển ca</h3>
                    <p className="text-[11px] text-slate-400 font-medium">{handoffModalTask.title}</p>
                  </div>
                </div>
                <button
                  onClick={() => setHandoffModalTask(null)}
                  className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg cursor-pointer"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleHandoffSubmit} className="space-y-4 text-xs font-bold text-slate-700">
                <div className="space-y-1.5">
                  <label className="block">Chuyển giao cho ai:</label>
                  <select
                    value={handoffTargetName}
                    onChange={(e) => setHandoffTargetName(e.target.value)}
                    className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-800"
                  >
                    {activeGuardians.map((g) => (
                      <option key={g.id} value={g.name}>{g.name} ({g.relationship || g.role})</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="block">Hình thức chuyển giao:</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setHandoffIsTemporary(true)}
                      className={`p-2.5 rounded-xl border transition-all text-center cursor-pointer ${
                        handoffIsTemporary
                          ? "bg-purple-600 text-white border-purple-600 shadow-xs"
                          : "bg-slate-50 text-slate-600 border-slate-200"
                      }`}
                    >
                      🔄 Nhờ làm hộ cữ này
                    </button>
                    <button
                      type="button"
                      onClick={() => setHandoffIsTemporary(false)}
                      className={`p-2.5 rounded-xl border transition-all text-center cursor-pointer ${
                        !handoffIsTemporary
                          ? "bg-purple-600 text-white border-purple-600 shadow-xs"
                          : "bg-slate-50 text-slate-600 border-slate-200"
                      }`}
                    >
                      👤 Đổi người phụ trách
                    </button>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="block">Lời nhắn dặn dò thêm:</label>
                  <input
                    type="text"
                    value={handoffReason}
                    onChange={(e) => setHandoffReason(e.target.value)}
                    placeholder="Ví dụ: Mẹ đang bận một chút, nhờ Bố cho bé bú cữ này nhé..."
                    className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl font-medium"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setHandoffModalTask(null)}
                    className="px-4 py-2 text-slate-500 hover:bg-slate-100 rounded-xl cursor-pointer"
                  >
                    Hủy
                  </button>
                  <button
                    type="submit"
                    disabled={isHandoffSubmitting}
                    className="px-5 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl shadow-xs cursor-pointer disabled:opacity-50"
                  >
                    {isHandoffSubmitting ? "Đang chuyển..." : "Xác nhận chuyển giao"}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
