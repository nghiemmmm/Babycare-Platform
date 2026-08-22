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
  Mic,
  Calendar,
  Send,
  Trash2,
  RefreshCw,
  ShieldCheck,
  Coffee,
  Pill,
  Moon,
  Activity,
  Zap,
  BarChart3,
  Users,
  ArrowRightLeft
} from "lucide-react";
import { apiFetch } from "../lib/authClient";
import { BabyProfile } from "../types";

interface HandoverNote {
  id: string;
  baby_id: string;
  date: string;
  author_name: string;
  content: string;
  created_at: string;
}

interface CareTask {
  id: string;
  baby_id: string;
  task_type: string;
  title: string;
  scheduled_time: string;
  assigned_name?: string;
  backup_assigned_name?: string;
  instructions?: string;
  target_value?: { amount?: number; unit?: string; [key: string]: any };
  status: "pending" | "due" | "completed" | "skipped" | "overdue" | "escalated";
  priority: string;
  actual_value?: { amount?: number; unit?: string; [key: string]: any };
  completion_notes?: string;
  completed_at?: string;
  escalated_at?: string;
  escalation_reason?: string;
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
}

export default function CareCoordinationView({ activeBaby, userName }: CareCoordinationViewProps) {
  const [roleMode, setRoleMode] = useState<"parent" | "caregiver">("parent");
  const [isLoading, setIsLoading] = useState(false);

  // Data states
  const [handoverNote, setHandoverNote] = useState<HandoverNote | null>(null);
  const [handoverInput, setHandoverInput] = useState("");
  const [isSavingHandover, setIsSavingHandover] = useState(false);

  const [tasks, setTasks] = useState<CareTask[]>([]);
  const [events, setEvents] = useState<CareEvent[]>([]);
  const [aiSummary, setAiSummary] = useState<string>("");
  const [workloadStats, setWorkloadStats] = useState<WorkloadStats | null>(null);

  // New task modal
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskType, setNewTaskType] = useState("feeding");
  const [newTaskTime, setNewTaskTime] = useState("14:30");
  const [newTaskAssignee, setNewTaskAssignee] = useState("Bà nội");
  const [newTaskBackupAssignee, setNewTaskBackupAssignee] = useState("Bố");
  const [newTaskAmount, setNewTaskAmount] = useState<number>(150);
  const [newTaskUnit, setNewTaskUnit] = useState("ml");
  const [newTaskInstructions, setNewTaskInstructions] = useState("");

  // Load summary & data
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
        setTasks(data.tasks || []);
        setEvents(data.recent_events || []);
        setAiSummary(data.ai_summary_text || "");
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
          content: handoverInput.trim()
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

  // Create Task
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim() || !activeBaby?.id) return;

    try {
      const res = await apiFetch("/api/v1/care-coordination/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          baby_id: activeBaby.id,
          task_type: newTaskType,
          title: newTaskTitle.trim(),
          scheduled_time: newTaskTime,
          assigned_name: newTaskAssignee,
          backup_assigned_name: newTaskBackupAssignee,
          instructions: newTaskInstructions.trim(),
          target_value: { amount: newTaskAmount, unit: newTaskUnit },
          priority: "normal"
        })
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

  // 1-Tap Complete Task
  const handleCompleteTask = async (taskId: string, actualAmount?: number, actualUnit?: string, notes?: string) => {
    try {
      const res = await apiFetch(`/api/v1/care-coordination/tasks/${taskId}/complete`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          actual_value: actualAmount ? { amount: actualAmount, unit: actualUnit || "ml" } : undefined,
          notes: notes || "Bé ngoan, hoàn thành tốt",
          completed_by_name: roleMode === "caregiver" ? "Bà / Người chăm sóc" : (userName || "Phụ huynh")
        })
      });
      if (res.ok) {
        fetchData();
      }
    } catch (err) {
      console.error("Error completing task:", err);
    }
  };

  // Dynamic Escalation
  const handleEscalateTask = async (taskId: string, backupName?: string) => {
    try {
      const res = await apiFetch(`/api/v1/care-coordination/tasks/${taskId}/escalate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          new_assignee_name: backupName || "Bố/Mẹ (Dự phòng)",
          reason: "Tự động chuyển giao do quá hạn thực hiện"
        })
      });
      if (res.ok) {
        fetchData();
      }
    } catch (err) {
      console.error("Error escalating task:", err);
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
      case "feeding":
        return <Coffee className="w-5 h-5 text-amber-500" />;
      case "medication":
        return <Pill className="w-5 h-5 text-rose-500" />;
      case "sleep":
        return <Moon className="w-5 h-5 text-indigo-500" />;
      default:
        return <Activity className="w-5 h-5 text-teal-500" />;
    }
  };

  const completedCount = tasks.filter((t) => t.status === "completed").length;
  const totalCount = tasks.length;
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-16">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-teal-600 via-emerald-600 to-teal-700 rounded-3xl p-6 md:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 translate-x-8 -translate-y-8 w-64 h-64 bg-white/10 rounded-full blur-2xl pointer-events-none" />
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/20 backdrop-blur-md rounded-full text-xs font-semibold uppercase tracking-wider">
              <ClipboardList className="w-4 h-4" /> Sổ Bàn Giao & Điều Phối Chăm Sóc
            </div>
            <h1 className="text-2xl md:text-3xl font-bold">
              Lịch Trình Chăm Sóc Cho Bé {activeBaby?.name || "Bé"}
            </h1>
            <p className="text-teal-100 text-sm md:text-base max-w-2xl">
              Kết nối hai chiều giữa Bố/Mẹ và Người chăm sóc ở nhà. Giao việc cụ thể, tick 1-chạm và tự động cập nhật nhật ký dinh dưỡng & sức khỏe.
            </p>
          </div>

          {/* Role Switcher Pill */}
          <div className="bg-black/20 p-1.5 rounded-2xl backdrop-blur-md flex items-center border border-white/20 self-start md:self-auto">
            <button
              onClick={() => setRoleMode("parent")}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
                roleMode === "parent"
                  ? "bg-white text-teal-800 shadow-md font-bold"
                  : "text-white/80 hover:text-white"
              }`}
            >
              <User className="w-4 h-4" /> Góc Bố/Mẹ
            </button>
            <button
              onClick={() => setRoleMode("caregiver")}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
                roleMode === "caregiver"
                  ? "bg-amber-400 text-amber-950 shadow-md font-bold"
                  : "text-white/80 hover:text-white"
              }`}
            >
              <Heart className="w-4 h-4" /> Góc Người Chăm Sóc (1-Chạm)
            </button>
          </div>
        </div>
      </div>

      {/* Progress & AI Summary Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center font-bold text-xl">
            {completedCount}/{totalCount}
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium">Tiến độ hôm nay</div>
            <div className="text-lg font-bold text-slate-800">
              {progressPercent}% Hoàn thành
            </div>
          </div>
        </div>

        <div className="md:col-span-2 bg-gradient-to-br from-amber-50 to-orange-50/50 rounded-2xl p-5 border border-amber-100/80 shadow-sm flex items-start gap-3.5">
          <div className="p-2 rounded-xl bg-amber-100 text-amber-700 mt-0.5">
            <Sparkles className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <div className="text-xs font-bold uppercase tracking-wider text-amber-800">
              AI Trợ Lý Điều Phối & Quản Lý Ngoại Lệ
            </div>
            <p className="text-sm text-amber-900/90 leading-relaxed font-medium">
              {aiSummary || "Hôm nay bé đang có lịch trình chăm sóc ổn định. Bố mẹ yên tâm làm việc nhé!"}
            </p>
          </div>
        </div>
      </div>

      {/* ─── GÓC BỐ / MẸ: HANDOVER NOTE, TASK TIMELINE & WORKLOAD ANALYTICS ───── */}
      {roleMode === "parent" ? (
        <div className="space-y-6">
          {/* Lời dặn buổi sáng (Handover Note) */}
          <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-teal-50 rounded-xl text-teal-600">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-800">
                    Lời Dặn Bàn Giao Buổi Sáng Cho Người Ở Nhà
                  </h2>
                  <p className="text-xs text-slate-500">
                    Dặn dò bà hoặc bảo mẫu những điểm đặc biệt cần lưu ý trong ngày
                  </p>
                </div>
              </div>
              <button
                onClick={handleSaveHandover}
                disabled={isSavingHandover}
                className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-sm transition-all"
              >
                {isSavingHandover ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Lưu lời dặn
              </button>
            </div>

            <textarea
              value={handoverInput}
              onChange={(e) => setHandoverInput(e.target.value)}
              placeholder="Ví dụ: Hôm nay bé hơi nghẹt mũi, bà nhớ nhỏ nước muối sinh lý lúc 10h và 15h. Cữ trưa 11h30 cho bé ăn cháo cá hồi trong ngăn mát (hâm nóng 2 phút)..."
              rows={3}
              className="w-full p-4 bg-slate-50 border border-slate-200 rounded-2xl text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all resize-none"
            />
          </div>

          {/* Danh sách Task trong ngày */}
          <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-amber-50 rounded-xl text-amber-600">
                  <Clock className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-800">
                    Lịch Trình Chi Tiết Trong Ngày
                  </h2>
                  <p className="text-xs text-slate-500">
                    Các mốc giờ cụ thể được giao cho từng người chăm sóc
                  </p>
                </div>
              </div>

              <button
                onClick={() => setIsTaskModalOpen(true)}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-sm transition-all"
              >
                <Plus className="w-4 h-4" /> Thêm Cữ / Việc Cần Làm
              </button>
            </div>

            {/* Task List */}
            {tasks.length === 0 ? (
              <div className="p-8 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-200">
                <Baby className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                <div className="text-sm font-semibold text-slate-600">Chưa có lịch trình cho hôm nay</div>
                <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                  Hãy bấm "Thêm Cữ / Việc Cần Làm" để lên lịch cữ sữa, uống thuốc hoặc ăn dặm cho bé.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {tasks.map((task) => {
                  const isDone = task.status === "completed";
                  const isOverdue = task.status === "overdue";
                  const isEscalated = task.status === "escalated";

                  const timeFormatted = task.scheduled_time.includes("T")
                    ? task.scheduled_time.split("T")[1].substring(0, 5)
                    : task.scheduled_time;

                  return (
                    <motion.div
                      key={task.id}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`p-4 rounded-2xl border transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                        isDone
                          ? "bg-slate-50/60 border-slate-200/80 opacity-75"
                          : isOverdue
                          ? "bg-rose-50/80 border-rose-200 shadow-sm"
                          : isEscalated
                          ? "bg-purple-50/80 border-purple-200 shadow-sm"
                          : "bg-white border-slate-200 hover:shadow-md"
                      }`}
                    >
                      <div className="flex items-center gap-3.5">
                        <div className="p-3 rounded-2xl bg-slate-100">
                          {getTaskIcon(task.task_type)}
                        </div>
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-bold text-sm text-slate-800">
                              {task.title}
                            </span>
                            <span className="px-2 py-0.5 bg-slate-100 rounded-md text-[11px] font-semibold text-slate-600">
                              ⏰ {timeFormatted}
                            </span>
                            <span className="px-2 py-0.5 bg-teal-50 text-teal-700 rounded-md text-[11px] font-medium">
                              👤 {task.assigned_name || "Bà"}
                            </span>

                            {isOverdue && (
                              <span className="px-2 py-0.5 bg-rose-100 text-rose-700 font-bold rounded-md text-[11px] flex items-center gap-1">
                                <AlertTriangle className="w-3 h-3" /> Quá hạn
                              </span>
                            )}
                            {isEscalated && (
                              <span className="px-2 py-0.5 bg-purple-100 text-purple-800 font-bold rounded-md text-[11px] flex items-center gap-1">
                                <Zap className="w-3 h-3" /> Đã chuyển giao ({task.assigned_name})
                              </span>
                            )}
                          </div>

                          {task.instructions && (
                            <p className="text-xs text-slate-500 mt-1">
                              {task.instructions}
                            </p>
                          )}
                          {isDone && task.actual_value?.amount && (
                            <p className="text-xs text-emerald-700 font-semibold mt-1">
                              ✓ Thực tế đã thực hiện: {task.actual_value.amount} {task.actual_value.unit || "ml"}
                            </p>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 self-end md:self-auto">
                        {isOverdue && (
                          <button
                            onClick={() => handleEscalateTask(task.id, task.backup_assigned_name)}
                            className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all shadow-sm cursor-pointer"
                            title="Chuyển giao cho người dự phòng"
                          >
                            <ArrowRightLeft className="w-3.5 h-3.5" /> Chuyển giao dự phòng
                          </button>
                        )}

                        {isDone ? (
                          <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-600 px-3 py-1.5 bg-emerald-50 rounded-xl">
                            <CheckCircle2 className="w-4 h-4" /> Đã xong
                          </div>
                        ) : (
                          <button
                            onClick={() => handleCompleteTask(task.id, task.target_value?.amount, task.target_value?.unit)}
                            className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all shadow-sm"
                          >
                            <CheckCircle2 className="w-4 h-4" /> Đánh dấu xong
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteTask(task.id)}
                          className="p-2 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-xl transition-all"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>

          {/* ─── WORKLOAD ANALYTICS (CÂN BẰNG KHỐI LƯỢNG CÔNG VIỆC) ───────────── */}
          {workloadStats && (
            <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm space-y-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-indigo-50 rounded-xl text-indigo-600">
                    <BarChart3 className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-800">
                      Phân Bổ Khối Lượng Công Việc Gia Đình (7 Ngày Qua)
                    </h2>
                    <p className="text-xs text-slate-500">
                      Minh bạch hóa nỗ lực chăm sóc của từng thành viên để cùng nhau chia sẻ
                    </p>
                  </div>
                </div>
                <div className="text-xs font-bold text-indigo-700 bg-indigo-50 px-3 py-1.5 rounded-xl">
                  Tổng: {workloadStats.total_tasks_completed}/{workloadStats.total_tasks_assigned} cữ
                </div>
              </div>

              {/* Caregivers Distribution Bars */}
              <div className="space-y-3">
                {workloadStats.caregivers_distribution.map((item, idx) => (
                  <div key={idx} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                      <span className="flex items-center gap-1.5">
                        <Users className="w-3.5 h-3.5 text-slate-400" />
                        {item.caregiver_name}
                      </span>
                      <span>
                        {item.completed_tasks_count}/{item.assigned_tasks_count} việc ({item.workload_percentage}%)
                      </span>
                    </div>
                    <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-teal-500 to-indigo-500 rounded-full transition-all duration-500"
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
            <div className="bg-amber-500 text-amber-950 p-6 rounded-3xl shadow-lg border-2 border-amber-400 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-900">
                <Heart className="w-4 h-4 fill-amber-900" /> Lời Dặn Của Mẹ Dành Cho Bà Hôm Nay:
              </div>
              <p className="text-base md:text-lg font-bold leading-relaxed">
                "{handoverNote.content}"
              </p>
            </div>
          )}

          {/* Checklist 1-Chạm Cực Lớn */}
          <div className="bg-white rounded-3xl p-6 md:p-8 border border-slate-200 shadow-md space-y-6">
            <div>
              <h2 className="text-xl md:text-2xl font-black text-slate-900">
                Danh Sách Việc Cần Làm Cho Bé
              </h2>
              <p className="text-sm text-slate-500">
                Bà chỉ cần bấm nút xanh khi đã cho bé ăn, uống thuốc hoặc ngủ xong
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {tasks.map((task) => {
                const isDone = task.status === "completed";
                const timeFormatted = task.scheduled_time.includes("T")
                  ? task.scheduled_time.split("T")[1].substring(0, 5)
                  : task.scheduled_time;

                const defaultAmount = task.target_value?.amount || 150;
                const defaultUnit = task.target_value?.unit || "ml";

                return (
                  <div
                    key={task.id}
                    className={`p-6 rounded-3xl border-2 transition-all ${
                      isDone
                        ? "bg-slate-50 border-slate-200 opacity-60"
                        : "bg-gradient-to-br from-white to-teal-50/30 border-teal-200 shadow-md"
                    }`}
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center gap-3">
                          <span className="px-3 py-1 bg-teal-700 text-white rounded-xl font-black text-base">
                            ⏰ {timeFormatted}
                          </span>
                          <span className="text-lg md:text-xl font-black text-slate-900">
                            {task.title}
                          </span>
                        </div>
                        {task.instructions && (
                          <p className="text-sm text-slate-600 font-medium">
                            📝 {task.instructions}
                          </p>
                        )}
                        {task.target_value?.amount && (
                          <div className="text-sm font-bold text-amber-700 bg-amber-100/70 inline-block px-3 py-1 rounded-lg">
                            Khẩu phần dặn: {task.target_value.amount} {task.target_value.unit || "ml"}
                          </div>
                        )}
                      </div>

                      {/* 1-Tap Big Action Button */}
                      <div>
                        {isDone ? (
                          <div className="px-6 py-4 bg-emerald-100 text-emerald-800 rounded-2xl font-black text-lg flex items-center justify-center gap-2">
                            <CheckCircle2 className="w-6 h-6" /> ĐÃ XONG
                          </div>
                        ) : (
                          <button
                            onClick={() => handleCompleteTask(task.id, defaultAmount, defaultUnit)}
                            className="w-full md:w-auto px-8 py-5 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white rounded-2xl font-black text-lg md:text-xl flex items-center justify-center gap-3 shadow-lg shadow-emerald-600/30 transition-all cursor-pointer"
                          >
                            <CheckCircle2 className="w-7 h-7" /> ✓ ĐÃ HOÀN THÀNH
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

      {/* ─── MODAL TẠO TASK MỚI ──────────────────────────────────────────────── */}
      <AnimatePresence>
        {isTaskModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-lg w-full p-6 space-y-5 shadow-2xl border border-slate-100"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-lg font-bold text-slate-800">Thêm Việc Chăm Sóc Cho Bé</h3>
                <button
                  onClick={() => setIsTaskModalOpen(false)}
                  className="text-slate-400 hover:text-slate-600 text-sm font-bold"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleCreateTask} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Loại công việc</label>
                  <select
                    value={newTaskType}
                    onChange={(e) => setNewTaskType(e.target.value)}
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium"
                  >
                    <option value="feeding">🍼 Cữ bú sữa / Ăn dặm</option>
                    <option value="medication">💊 Uống thuốc / Vitamin</option>
                    <option value="sleep">😴 Giấc ngủ trưa / tối</option>
                    <option value="hygiene">🛁 Tắm rửa / Vệ sinh</option>
                    <option value="custom">✨ Công việc khác</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Tên việc cần làm</label>
                  <input
                    type="text"
                    required
                    value={newTaskTitle}
                    onChange={(e) => setNewTaskTitle(e.target.value)}
                    placeholder="Ví dụ: Cữ sữa chiều, Uống Vitamin D3..."
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Mốc giờ</label>
                    <input
                      type="time"
                      required
                      value={newTaskTime}
                      onChange={(e) => setNewTaskTime(e.target.value)}
                      className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Người phụ trách chính</label>
                    <input
                      type="text"
                      value={newTaskAssignee}
                      onChange={(e) => setNewTaskAssignee(e.target.value)}
                      placeholder="Bà nội, Bảo mẫu..."
                      className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Lượng dự kiến</label>
                    <input
                      type="number"
                      value={newTaskAmount}
                      onChange={(e) => setNewTaskAmount(Number(e.target.value))}
                      className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Người dự phòng (Escalation)</label>
                    <input
                      type="text"
                      value={newTaskBackupAssignee}
                      onChange={(e) => setNewTaskBackupAssignee(e.target.value)}
                      placeholder="Bố, Mẹ..."
                      className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Hướng dẫn chi tiết</label>
                  <textarea
                    value={newTaskInstructions}
                    onChange={(e) => setNewTaskInstructions(e.target.value)}
                    placeholder="Ví dụ: Sữa mẹ rã đông hâm 40 độ C, cho bé ợ hơi sau khi bú..."
                    rows={2}
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium resize-none"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsTaskModalOpen(false)}
                    className="px-4 py-2 text-slate-500 hover:bg-slate-100 rounded-xl text-sm font-bold"
                  >
                    Hủy
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-sm font-bold shadow-md"
                  >
                    Tạo việc cần làm
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
