import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { useNavigate } from "react-router-dom";
import {
  Heart,
  LayoutDashboard,
  Activity,
  Sparkles,
  User,
  Coffee,
  CloudLightning,
  AlertCircle,
  Plus,
  RefreshCw,
  Bell,
  Menu,
  X,
  Shield,
  LogOut,
  ClipboardList
} from "lucide-react";

import {
  BabyProfile,
  Gender,
  Measurement,
  MedicationLog,
  Guardian,
  FeedLog,
  IngredientLog,
  ChatMessage,
  SmartExtraction,
  NutritionRecommendation,
  WeeklyMealPlan,
  NutritionSafety,
  SafetyHandbook
} from "./types";

import { useAuth } from "./auth/AuthContext";
import { apiFetch } from "./lib/authClient";

import DashboardView from "./components/DashboardView";
import GrowthView from "./components/GrowthView";
import AiHubView from "./components/AiHubView";
import ProfileView from "./components/ProfileView";
import NutritionView from "./components/NutritionView";
import LogsView from "./components/LogsView";
import HealthView from "./components/HealthView";

export default function App() {
  const { email, name, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  // Core persistent states backed by Backend APIs
  const [babies, setBabies] = useState<BabyProfile[]>([]);
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [medications, setMedications] = useState<MedicationLog[]>([]);
  const [guardians, setGuardians] = useState<Guardian[]>([]);
  const [feeds, setFeeds] = useState<FeedLog[]>([]);
  const [ingredients, setIngredients] = useState<IngredientLog[]>([]);
  const [chats, setChats] = useState<ChatMessage[]>([]);
  const [nutritionRecommendation, setNutritionRecommendation] = useState<NutritionRecommendation | null>(null);
  const [isGeneratingRecommendation, setIsGeneratingRecommendation] = useState(false);
  const [weeklyMealPlan, setWeeklyMealPlan] = useState<WeeklyMealPlan | null>(null);
  const [isGeneratingWeeklyPlan, setIsGeneratingWeeklyPlan] = useState(false);
  const [isAcceptingWeeklyPlan, setIsAcceptingWeeklyPlan] = useState(false);
  const [threads, setThreads] = useState<Array<{ id: string; title: string }>>([]);
  const [activeThreadId, setActiveThreadId] = useState<string>("thread_default");
  const threadCacheRef = useRef<Record<string, ChatMessage[]>>({});
  const [nutritionSafety, setNutritionSafety] = useState<NutritionSafety | null>(null);
  const [safetyHandbook, setSafetyHandbook] = useState<SafetyHandbook | null>(null);
  const [isLoadingSafetyHandbook, setIsLoadingSafetyHandbook] = useState(false);

  // App UI state
  const [activeTab, setActiveTab] = useState<"dashboard" | "growth" | "ai" | "profile" | "nutrition" | "health" | "log">("dashboard");
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  // Nap timer states (Cohesive global stopwatch)
  const [isNapTimerRunning, setIsNapTimerRunning] = useState(false);
  const [napElapsedTime, setNapElapsedTime] = useState(0);
  const napTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Sync state helpers


  // Active Baby helper
  const activeBaby = babies.find((b) => b.isActive) || babies[0];
  const hasBaby = Boolean(activeBaby);

  // Onboarding: tài khoản vừa đăng ký chưa có hồ sơ bé nào - đưa thẳng vào tab "Hồ sơ bé" để
  // nhập thông tin, vì mọi tab khác (Dashboard, Tăng trưởng, AI, Dinh dưỡng, Sức khỏe) đều đọc
  // activeBaby.* không có kiểm tra null nên sẽ crash nếu chưa có bé nào. Chỉ tự chuyển tab một
  // lần lúc mới bootstrap xong với 0 bé - không ảnh hưởng người dùng cũ chủ động vào tab Hồ sơ.
  const [isOnboarding, setIsOnboarding] = useState(false);

  // Helper mappers
  const mapBackendGender = (g: string): Gender => {
    if (!g) return Gender.Unknown;
    const gl = g.toLowerCase();
    if (gl === "boy") return Gender.Boy;
    if (gl === "girl") return Gender.Girl;
    return Gender.Unknown;
  };

  const mapBackendReaction = (r: string): any => {
    if (!r) return "Neutral";
    const rl = r.toLowerCase();
    if (rl.includes("love") || rl === "liked" || rl === "loved it") return "Loved it";
    if (rl.includes("allergic") || rl.includes("allergy") || rl === "allergic reaction") return "Allergic Reaction";
    if (rl.includes("spat") || rl.includes("dislike") || rl === "spat out") return "Spat out";
    return "Neutral";
  };

  const mapNutritionRecommendation = (r: any): NutritionRecommendation => ({
    id: r.id,
    babyId: r.baby_id,
    generatedAt: r.generated_at,
    recommendedFoods: (r.recommended_foods || []).map((f: any) => ({ foodName: f.food_name, reason: f.reason })),
    foodsToAvoid: (r.foods_to_avoid || []).map((f: any) => ({ foodName: f.food_name, reason: f.reason, linkedTo: f.linked_to })),
    summary: r.summary,
    basedOnAllergies: r.based_on_allergies || [],
    basedOnConditions: r.based_on_conditions || []
  });

  const mapNutritionSafety = (s: any): NutritionSafety => ({
    foodsToAvoid: (s.foods_to_avoid || []).map((f: any) => ({
      name: f.name,
      reason: f.reason,
      category: f.category,
      minAgeMonths: f.min_age_months
    })),
    allergenAlerts: {
      allergens: s.allergen_alerts?.allergens || [],
      warningMessage: s.allergen_alerts?.warning_message || "",
      hasAlert: Boolean(s.allergen_alerts?.has_alert)
    }
  });

  const mapWeeklyMealPlan = (p: any): WeeklyMealPlan => ({
    id: p.id,
    babyId: p.baby_id,
    generatedAt: p.generated_at,
    startDate: p.start_date,
    endDate: p.end_date,
    status: p.status,
    acceptedAt: p.accepted_at || undefined,
    days: (p.days || []).map((d: any) => ({
      date: d.date,
      meals: (d.meals || []).map((m: any) => ({ mealType: m.meal_type, foodName: m.food_name, note: m.note }))
    })),
    summary: p.summary,
    basedOnAllergies: p.based_on_allergies || [],
    basedOnConditions: p.based_on_conditions || []
  });

  // Fetch active baby's data
  const refreshActiveBabyData = async (babyId: string) => {
    if (!babyId) return;
    try {
      // 1. Fetch growth measurements
      const mRes = await apiFetch(`/api/v1/growth/measurements?baby_id=${babyId}`);
      if (mRes.ok) {
        const mData = await mRes.json();
        setMeasurements(mData.map((m: any) => ({
          id: m.id,
          babyId: babyId,
          date: m.date,
          ageInMonths: m.age_months,
          weight: m.weight,
          height: m.height,
          headCircumference: m.head_circumference,
          status: "Normal",
          notes: ""
        })));
      }

      // 2. Fetch feeds
      const fRes = await apiFetch(`/api/v1/nutrition/feeds?baby_id=${babyId}`);
      if (fRes.ok) {
        const fData = await fRes.json();
        setFeeds(fData.map((f: any) => ({
          id: f.id,
          babyId: babyId,
          type: f.type === "Breast" || f.type === "BreastMilk" ? "Breast" : f.type === "Solids" ? "Solids" : "Formula",
          details: f.details,
          amount: f.amount,
          time: f.time,
          date: f.date || ""
        })));
      }

      // 3. Fetch ingredients
      const iRes = await apiFetch(`/api/v1/nutrition/ingredients?baby_id=${babyId}`);
      if (iRes.ok) {
        const iData = await iRes.json();
        setIngredients(iData.map((i: any) => ({
          id: i.id,
          babyId: babyId,
          name: i.name,
          reaction: mapBackendReaction(i.reaction),
          date: i.date
        })));
      }

      // 4. Fetch guardians
      const gRes = await apiFetch(`/api/v1/guardians?baby_id=${babyId}`);
      if (gRes.ok) {
        const gData = await gRes.json();
        setGuardians(gData.map((g: any) => ({
          id: g.id,
          name: g.name,
          email: g.email,
          role: g.role,
          status: g.status === "Synced" ? "Synced" : g.status === "Pending" ? "Pending" : "Invited"
        })));
      }

      // 5. Fetch medications
      const medRes = await apiFetch(`/api/v1/babies/${babyId}/medication`);
      if (medRes.ok) {
        const medData = await medRes.json();
        setMedications(medData.map((m: any) => ({
          id: m.id,
          babyId: babyId,
          name: m.medication_name,
          dosage: m.dosage,
          time: m.logged_at.slice(11, 16),
          date: m.logged_at.slice(0, 10),
          prescribedBy: m.prescribed_by || "Doctor"
        })));
      }

      // 7. Fetch cached AI nutrition recommendation (null nếu chưa từng tạo, không phải lỗi)
      const recRes = await apiFetch(`/api/v1/nutrition/recommendation?baby_id=${babyId}`);
      if (recRes.ok) {
        const recData = await recRes.json();
        setNutritionRecommendation(recData ? mapNutritionRecommendation(recData) : null);
      }

      // 8. Fetch cached AI weekly meal plan (null nếu chưa từng tạo, không phải lỗi)
      const planRes = await apiFetch(`/api/v1/nutrition/meal-plan/weekly?baby_id=${babyId}`);
      if (planRes.ok) {
        const planData = await planRes.json();
        setWeeklyMealPlan(planData ? mapWeeklyMealPlan(planData) : null);
      }

      // 9. Fetch hướng dẫn an toàn dinh dưỡng - tính đúng theo tuổi thật của bé (server-side)
      const safetyRes = await apiFetch(`/api/v1/nutrition/safety-guidelines?baby_id=${babyId}`);
      if (safetyRes.ok) {
        const safetyData = await safetyRes.json();
        setNutritionSafety(mapNutritionSafety(safetyData));
      }
    } catch (e) {
      console.error("Error refreshing active baby data:", e);
    }
  };

  // Cẩm nang an toàn dinh dưỡng - nội dung tĩnh, chỉ tải khi người dùng thực sự mở ra xem
  const handleOpenSafetyHandbook = async () => {
    if (safetyHandbook) return;
    setIsLoadingSafetyHandbook(true);
    try {
      const res = await apiFetch("/api/v1/nutrition/safety-handbook");
      if (res.ok) {
        const data = await res.json();
        setSafetyHandbook({
          title: data.title,
          sections: (data.sections || []).map((s: any) => ({
            title: s.title,
            description: s.description,
            items: s.items,
            level: s.level
          }))
        });
      }
    } catch (e) {
      console.error("Error loading safety handbook:", e);
    } finally {
      setIsLoadingSafetyHandbook(false);
    }
  };

  // Fetch all chat threads for the user
  const loadThreads = async () => {
    try {
      const res = await apiFetch("/api/v1/ai/threads");
      if (res.ok) {
        const data = await res.json();
        setThreads(data.map((t: any) => ({
          id: t.id,
          title: t.title
        })));
        if (data.length > 0) {
          const threadIds = data.map((t: any) => t.id);
          if (!threadIds.includes(activeThreadId)) {
            setActiveThreadId(data[0].id);
          }
        }
      }
    } catch (e) {
      console.error("Failed to load chat threads:", e);
    }
  };

  // Fetch messages inside the selected thread
  const loadThreadMessages = async (threadId: string) => {
    // Instant UI update if thread messages are cached in memory
    if (threadCacheRef.current[threadId]) {
      setChats(threadCacheRef.current[threadId]);
    }

    try {
      const res = await apiFetch(`/api/v1/ai/threads/${threadId}/messages`);
      if (res.ok) {
        const data = await res.json();
        const mapped = data.map((c: any) => ({
          id: c.id,
          role: c.role,
          content: c.content,
          timestamp: c.timestamp.includes("T") ? c.timestamp.slice(11, 16) : c.timestamp
        }));
        threadCacheRef.current[threadId] = mapped;
        setChats(mapped);
      } else if (!threadCacheRef.current[threadId]) {
        setChats([]);
      }
    } catch (e) {
      console.error("Failed to load thread messages:", e);
      if (!threadCacheRef.current[threadId]) {
        setChats([]);
      }
    }
  };

  // Load babies list on mount
  useEffect(() => {
    const loadInitialBabies = async () => {
      try {
        const res = await apiFetch("/api/v1/babies");
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            // QUAN TRỌNG: chỉ dùng đúng is_active thật từ backend, KHÔNG được ép index===0
            // thành active - trước đây "isActive: b.is_active || (index===0)" luôn ép phần tử
            // đầu tiên thành active bất kể giá trị thật, nên dù backend đã lưu đúng bé nào đang
            // chọn (vd. "gấu"), bé đứng đầu mảng (vd. "Leo") vẫn bị đánh dấu active song song ->
            // babies.find(isActive) luôn vớ trúng bé đầu tiên thay vì bé người dùng thực sự chọn.
            const mapped = data.map((b: any) => ({
              id: b.id,
              name: b.name,
              birthDate: b.birth_date,
              gender: mapBackendGender(b.gender),
              avatarUrl: b.avatar_url || "/static/img/leo.png",
              isActive: Boolean(b.is_active),
              bloodType: b.blood_type,
              pediatricianName: b.pediatrician_name,
              allergies: b.allergies || []
            }));
            // Fallback phòng dữ liệu cũ/hỏng chưa có bé nào active - chỉ áp dụng khi THỰC SỰ
            // không có bé nào active, không phải mặc định luôn ép bé đầu tiên.
            if (!mapped.some((b) => b.isActive)) {
              mapped[0].isActive = true;
            }
            setBabies(mapped);
          }
        }
      } catch (err) {
        console.error("Error loading initial babies:", err);
      } finally {
        setIsBootstrapping(false);
      }
    };
    loadInitialBabies();
    loadThreads();
  }, []);

  // Automatically fetch thread messages whenever activeThreadId changes
  useEffect(() => {
    if (activeThreadId) {
      loadThreadMessages(activeThreadId);
    }
  }, [activeThreadId]);

  // Check URL query parameters for invitation acceptance link
  useEffect(() => {
    const handleAcceptInviteFromUrl = async () => {
      const searchParams = new URLSearchParams(window.location.search);
      const inviteId = searchParams.get("accept_invite");
      if (inviteId) {
        try {
          const res = await apiFetch(`/api/v1/guardians/accept/${inviteId}`, {
            method: "POST"
          });
          if (res.ok) {
            window.history.replaceState({}, document.title, window.location.pathname);
            const resBabies = await apiFetch("/api/v1/babies");
            if (resBabies.ok) {
              const dataBabies = await resBabies.json();
              if (Array.isArray(dataBabies) && dataBabies.length > 0) {
                setBabies(dataBabies.map((b: any) => ({
                  id: b.id,
                  name: b.name,
                  birthDate: b.birth_date,
                  gender: mapBackendGender(b.gender),
                  avatarUrl: b.avatar_url || "/static/img/leo.png",
                  isActive: Boolean(b.is_active),
                  bloodType: b.blood_type,
                  pediatricianName: b.pediatrician_name,
                  allergies: b.allergies || []
                })));
              }
            }
          }
        } catch (e) {
          console.error("Error accepting invitation from URL:", e);
        }
      }
    };
    handleAcceptInviteFromUrl();
  }, []);

  // Sync active baby details
  useEffect(() => {
    if (activeBaby?.id) {
      refreshActiveBabyData(activeBaby.id);
      loadThreads();
    }
  }, [activeBaby?.id]);

  // Sync active thread with messages list
  useEffect(() => {
    if (activeThreadId) {
      loadThreadMessages(activeThreadId);
    }
  }, [activeThreadId]);

  // Bootstrap xong mà chưa có bé nào -> mở onboarding, khoá vào tab Hồ sơ.
  // Ngay khi bé đầu tiên được tạo -> tắt onboarding, chuyển sang Dashboard.
  useEffect(() => {
    if (!isBootstrapping && babies.length === 0 && !isOnboarding) {
      setIsOnboarding(true);
      setActiveTab("profile");
    } else if (isOnboarding && babies.length > 0) {
      setIsOnboarding(false);
      setActiveTab("dashboard");
    }
  }, [isBootstrapping, babies.length, isOnboarding]);

  // Stop watch logic
  useEffect(() => {
    if (isNapTimerRunning) {
      napTimerRef.current = setInterval(() => {
        setNapElapsedTime((prev) => prev + 1);
      }, 1000);
    } else {
      if (napTimerRef.current) {
        clearInterval(napTimerRef.current);
      }
    }
    return () => {
      if (napTimerRef.current) clearInterval(napTimerRef.current);
    };
  }, [isNapTimerRunning]);

  const handleStartNapTimer = async () => {
    if (isNapTimerRunning) {
      // Save nap log to feeds
      const hrs = Math.floor(napElapsedTime / 3600);
      const mins = Math.floor((napElapsedTime % 3600) / 60);
      const durationStr = hrs > 0 ? `${hrs}h ${mins}m` : `${mins}m`;

      try {
        const res = await apiFetch("/api/v1/ai/sleep/timer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            baby_id: activeBaby.id,
            action: "stop"
          })
        });
        if (res.ok) {
          refreshActiveBabyData(activeBaby.id);
        }
      } catch (e) {
        console.error(e);
      }

      setIsNapTimerRunning(false);
      setNapElapsedTime(0);
    } else {
      try {
        const res = await apiFetch("/api/v1/ai/sleep/timer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            baby_id: activeBaby.id,
            action: "start"
          })
        });
        if (res.ok) {
          setIsNapTimerRunning(true);
        }
      } catch (e) {
        console.error(e);
      }
    }
  };

  // State handlers passed to child views
  const handleSelectBaby = (id: string) => {
    // Cập nhật lạc quan ngay trên UI trước, đồng thời lưu lựa chọn xuống backend - nếu chỉ đổi
    // state cục bộ mà không gọi API, is_active thật trong Firestore không đổi, nên lần fetch
    // lại babies tiếp theo (refreshActiveBabyData, tạo/sửa bé khác...) sẽ khiến bé đang chọn bị
    // trả về giá trị cũ trong DB thay vì bé người dùng vừa bấm chọn.
    setBabies((prev) =>
      prev.map((b) => ({
        ...b,
        isActive: b.id === id
      }))
    );
    apiFetch(`/api/v1/babies/${id}/set-active`, { method: "PATCH" }).catch((e) => console.error(e));
  };

  // Ném lỗi thay vì chỉ console.error khi thất bại - nếu nuốt lỗi âm thầm, UI (ProfileView)
  // không có cách nào biết để báo cho người dùng, nhìn như "bấm Lưu xong không có gì xảy ra"
  // (vd. token đăng nhập hết hạn sau 1 giờ, mất mạng, lỗi server).
  const handleUpdateBaby = async (updated: BabyProfile) => {
    let res: Response;
    try {
      res = await apiFetch(`/api/v1/babies/${updated.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: updated.name,
          birth_date: updated.birthDate,
          gender: updated.gender,
          avatar_url: updated.avatarUrl,
          is_active: updated.isActive,
          blood_type: updated.bloodType,
          pediatrician_name: updated.pediatricianName,
          allergies: updated.allergies
        })
      });
    } catch (e) {
      console.error(e);
      throw new Error("Không thể kết nối tới máy chủ, vui lòng kiểm tra mạng và thử lại.");
    }
    if (!res.ok) {
      throw new Error(res.status === 401 ? "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại." : "Lưu hồ sơ thất bại, vui lòng thử lại.");
    }
    setBabies((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
  };

  const handleAddBaby = async (newBaby: Omit<BabyProfile, "id">) => {
    let res: Response;
    try {
      res = await apiFetch("/api/v1/babies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newBaby.name,
          birth_date: newBaby.birthDate,
          gender: newBaby.gender,
          avatar_url: newBaby.avatarUrl,
          is_active: true,
          blood_type: newBaby.bloodType,
          pediatrician_name: newBaby.pediatricianName,
          allergies: newBaby.allergies
        })
      });
    } catch (e) {
      console.error(e);
      throw new Error("Không thể kết nối tới máy chủ, vui lòng kiểm tra mạng và thử lại.");
    }
    if (!res.ok) {
      throw new Error(res.status === 401 ? "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại." : "Tạo hồ sơ bé thất bại, vui lòng thử lại.");
    }
    const data = await res.json();
    const bRes = await apiFetch("/api/v1/babies");
    if (bRes.ok) {
      const bData = await bRes.json();
      const mapped = bData.map((b: any) => ({
        id: b.id,
        name: b.name,
        birthDate: b.birth_date,
        gender: mapBackendGender(b.gender),
        avatarUrl: b.avatar_url || "/static/img/leo.png",
        isActive: b.id === data.id,
        bloodType: b.blood_type,
        pediatricianName: b.pediatrician_name,
        allergies: b.allergies
      }));
      setBabies(mapped);
    }
  };

  const handleDeleteBaby = async (id: string) => {
    let res: Response;
    try {
      res = await apiFetch(`/api/v1/babies/${id}`, { method: "DELETE" });
    } catch (e) {
      console.error(e);
      throw new Error("Không thể kết nối tới máy chủ, vui lòng kiểm tra mạng và thử lại.");
    }
    if (!res.ok) {
      throw new Error(res.status === 401 ? "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại." : "Xoá hồ sơ thất bại, vui lòng thử lại.");
    }
    setBabies((prev) => {
      const remaining = prev.filter((b) => b.id !== id);
      // Nếu bé đang active bị xoá, gán active cho bé còn lại đầu tiên (nếu có) - nếu không
      // còn bé nào cả, remaining=[] sẽ tự kích hoạt lại luồng onboarding (xem useEffect
      // isOnboarding phía trên).
      if (remaining.length > 0 && !remaining.some((b) => b.isActive)) {
        remaining[0] = { ...remaining[0], isActive: true };
      }
      return remaining;
    });
  };

  // Upload ảnh đại diện độc lập với create/update baby, vì lúc tạo bé mới chưa có baby_id để
  // gắn ảnh vào - trả về URL tĩnh để ProfileView gán vào avatarUrl trước khi submit form.
  const handleUploadAvatar = async (file: File): Promise<string> => {
    const formData = new FormData();
    formData.append("file", file);
    let res: Response;
    try {
      res = await apiFetch("/api/v1/babies/upload-avatar", { method: "POST", body: formData });
    } catch (e) {
      console.error(e);
      throw new Error("Không thể kết nối tới máy chủ, vui lòng kiểm tra mạng và thử lại.");
    }
    if (!res.ok) {
      const detail = await res.json().then((d) => d.detail || d.message).catch(() => null);
      throw new Error(detail || (res.status === 401 ? "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại." : "Tải ảnh lên thất bại, vui lòng thử lại."));
    }
    const data = await res.json();
    return data.avatar_url as string;
  };

  const handleAddMeasurement = async (newM: Omit<Measurement, "id">) => {
    try {
      const res = await apiFetch("/api/v1/growth/measurements", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          baby_id: activeBaby.id,
          weight: newM.weight,
          height: newM.height,
          head_circumference: newM.headCircumference,
          date: newM.date
        })
      });
      if (res.ok) {
        refreshActiveBabyData(activeBaby.id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteMeasurement = async (id: string) => {
    try {
      const res = await apiFetch(`/api/v1/babies/${activeBaby.id}/growth/${id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        refreshActiveBabyData(activeBaby.id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddMedication = async (newMed: Omit<MedicationLog, "id">) => {
    try {
      const res = await apiFetch("/api/v1/health/medications/administer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          baby_id: activeBaby.id,
          medication_name: newMed.name,
          amount: newMed.dosage,
          administered_at: new Date().toISOString()
        })
      });
      if (res.ok) {
        refreshActiveBabyData(activeBaby.id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteMedication = async (id: string) => {
    try {
      const res = await apiFetch(`/api/v1/babies/${activeBaby.id}/medication/${id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        refreshActiveBabyData(activeBaby.id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddGuardian = async (newG: Omit<Guardian, "id">) => {
    try {
      const res = await apiFetch(`/api/v1/guardians/invite?baby_id=${activeBaby.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newG.name,
          email: newG.email,
          role: newG.role
        })
      });
      if (res.ok) {
        refreshActiveBabyData(activeBaby.id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteGuardian = async (id: string) => {
    try {
      const res = await apiFetch(`/api/v1/guardians/${id}?baby_id=${activeBaby.id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        refreshActiveBabyData(activeBaby.id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddFeed = async (newFeed: Omit<FeedLog, "id">) => {
    try {
      const res = await apiFetch("/api/v1/nutrition/feeds", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          baby_id: activeBaby.id,
          type: newFeed.type,
          details: newFeed.details,
          amount: newFeed.amount,
          time: newFeed.time
        })
      });
      if (res.ok) {
        refreshActiveBabyData(activeBaby.id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteFeed = async (id: string) => {
    try {
      const res = await apiFetch(`/api/v1/nutrition/feeds/${id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        refreshActiveBabyData(activeBaby.id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddIngredient = async (newIng: Omit<IngredientLog, "id">) => {
    try {
      const res = await apiFetch("/api/v1/nutrition/ingredients", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          baby_id: activeBaby.id,
          name: newIng.name,
          reaction: newIng.reaction
        })
      });
      if (res.ok) {
        refreshActiveBabyData(activeBaby.id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteIngredient = async (id: string) => {
    try {
      const res = await apiFetch(`/api/v1/nutrition/ingredients/${id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        refreshActiveBabyData(activeBaby.id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleGenerateNutritionRecommendation = async () => {
    if (!activeBaby) return;
    setIsGeneratingRecommendation(true);
    try {
      const res = await apiFetch("/api/v1/nutrition/recommendation/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ baby_id: activeBaby.id })
      });
      if (!res.ok) {
        throw new Error("Không thể tạo gợi ý dinh dưỡng lúc này, vui lòng thử lại sau.");
      }
      const data = await res.json();
      setNutritionRecommendation(mapNutritionRecommendation(data));
    } finally {
      setIsGeneratingRecommendation(false);
    }
  };

  const handleGenerateWeeklyMealPlan = async (feedback?: string) => {
    if (!activeBaby) return;
    setIsGeneratingWeeklyPlan(true);
    try {
      const res = await apiFetch("/api/v1/nutrition/meal-plan/weekly/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ baby_id: activeBaby.id, feedback: feedback || undefined })
      });
      if (!res.ok) {
        // Backend trả message tiếng Việt cụ thể (vd "còn X ngày" khi bị khoá 409) - ưu tiên đọc
        // thẳng từ response thay vì thông báo lỗi chung chung.
        let message = "Không thể tạo thực đơn 7 ngày lúc này, vui lòng thử lại sau.";
        try {
          const errBody = await res.json();
          if (errBody?.message) message = errBody.message;
        } catch {
          // ignore parse error, dùng message mặc định
        }
        throw new Error(message);
      }
      const data = await res.json();
      setWeeklyMealPlan(mapWeeklyMealPlan(data));
    } finally {
      setIsGeneratingWeeklyPlan(false);
    }
  };

  const handleAcceptWeeklyMealPlan = async () => {
    if (!activeBaby) return;
    setIsAcceptingWeeklyPlan(true);
    try {
      const res = await apiFetch("/api/v1/nutrition/meal-plan/weekly/accept", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ baby_id: activeBaby.id })
      });
      if (!res.ok) {
        throw new Error("Không thể chấp nhận thực đơn lúc này, vui lòng thử lại sau.");
      }
      const data = await res.json();
      setWeeklyMealPlan(mapWeeklyMealPlan(data));
    } finally {
      setIsAcceptingWeeklyPlan(false);
    }
  };

  // AI assistant messaging with direct API calls to FastAPI backend (thread-scoped)
  const handleSendMessage = async (text: string) => {
    const userMsg: ChatMessage = {
      id: `u_${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setChats((prev) => [...prev, userMsg]);
    setIsAiLoading(true);

    try {
      const response = await apiFetch(`/api/v1/ai/threads/${activeThreadId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: userMsg.content,
          type: "text",
          baby_id: activeBaby?.id
        })
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();
      loadThreads(); // Refresh thread list to fetch any updated titles

      // Convert from Backend format (MessageCreateResponse) to App.tsx format
      const aiContent = data.ai_response?.content || "Tôi đã ghi nhận thông tin đó!";
      const citations = data.ai_response?.citations || [];
      const extractedLogs = data.extracted_logs || [];

      // Convert first extracted_log to extraction widget if present
      let extraction = null;
      if (extractedLogs.length > 0) {
        const log = extractedLogs[0];
        extraction = {
          type: log.type,
          title: log.title,
          detail: log.detail,
          value: log.value,
          time: log.time,
          pending: false,
        };
      }

      const aiMsgObj: ChatMessage = {
        id: `ai_${Date.now()}`,
        role: "assistant",
        content: aiContent,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        extraction,
        citations
      };

      setChats((prev) => {
        const next = [...prev, aiMsgObj];
        threadCacheRef.current[activeThreadId] = next;
        return next;
      });
    } catch (error) {
      console.error("Failed to message Gemini API:", error);
      // Fallback
      setChats((prev) => [
        ...prev,
        {
          id: `ai_${Date.now()}`,
          role: "assistant",
          content: "I ran into a connection glitch reaching the core servers, but rest assured, your logs are saved. Let me know if you want to track feeding volume, check paracetamol schedules, or solids advice!",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsAiLoading(false);
    }
  };

  const handleCreateThread = async () => {
    try {
      const res = await apiFetch("/api/v1/ai/threads", {
        method: "POST"
      });
      if (res.ok) {
        const data = await res.json();
        const newThreadId = data.thread_id;

        // Add new thread to the list and select it
        setThreads(prev => [{ id: newThreadId, title: data.title }, ...prev]);
        setActiveThreadId(newThreadId);
        setChats([]); // Clear messages locally immediately
      }
    } catch (e) {
      console.error("Failed to create new thread:", e);
    }
  };

  const handleSelectThread = (threadId: string) => {
    setActiveThreadId(threadId);
    if (threadCacheRef.current[threadId]) {
      setChats(threadCacheRef.current[threadId]);
    }
  };

  const handleConfirmExtraction = (ext: SmartExtraction) => {
    // Convert smart extraction to its actual logger counterpart
    if (ext.type === "feeding") {
      handleAddFeed({
        babyId: activeBaby.id,
        type: "Formula",
        details: ext.detail,
        amount: ext.value || 150,
        time: ext.time,
        date: "Today"
      });
    } else if (ext.type === "medication") {
      handleAddMedication({
        babyId: activeBaby.id,
        name: ext.detail,
        dosage: ext.value || "150mg",
        time: ext.time,
        date: "Today",
        prescribedBy: "Dr. Aris"
      });
    } else if (ext.type === "nutrition") {
      handleAddFeed({
        babyId: activeBaby.id,
        type: "Solids",
        details: ext.detail,
        amount: 1,
        time: ext.time,
        date: "Today"
      });
    } else if (ext.type === "sleep") {
      handleStartNapTimer();
    }

    // Clean up or mark the chat message's extraction as confirmed
    setChats((prev) =>
      prev.map((c) => {
        if (c.extraction?.title === ext.title) {
          return { ...c, extraction: null };
        }
        return c;
      })
    );
  };

  // Loading screen khi chờ bootstrap
  if (isBootstrapping) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg, #e0e7ff 0%, #f0fdf4 100%)" }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🌙</div>
        <div style={{ fontSize: 22, fontWeight: 700, color: "#4338ca", marginBottom: 8 }}>Lullaby AI</div>
        <div style={{ fontSize: 14, color: "#64748b" }}>Đang tải dữ liệu bé...</div>
        <div style={{ marginTop: 24, width: 40, height: 40, border: "4px solid #e0e7ff", borderTop: "4px solid #4338ca", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row font-sans text-slate-800" id="babycare-app">
      
      {/* Mobile Header Bar */}
      <div className="md:hidden bg-white border-b border-slate-100 p-4 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-indigo-600" />
          <span className="font-bold text-sm tracking-tight text-slate-900">Lullaby AI</span>
        </div>
        
        <div className="flex items-center gap-2">
          {isNapTimerRunning && (
            <span className="text-[10px] bg-indigo-50 text-indigo-700 font-bold px-2 py-0.5 rounded-full animate-pulse">
              Nap Ticking
            </span>
          )}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-1.5 hover:bg-slate-50 rounded-lg text-slate-600"
          >
            {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Sidebar Navigation */}
      <aside
        className={`w-64 bg-white/40 backdrop-blur-2xl border-r border-white/20 flex flex-col p-5 space-y-6 shrink-0 fixed md:sticky top-0 md:h-screen z-40 transition-transform md:translate-x-0 ${
          isMobileMenuOpen ? "translate-x-0 h-screen" : "-translate-x-full md:translate-x-0"
        }`}
      >
        {/* Logo and branding */}
        <div className="hidden md:flex items-center gap-3 px-1 py-2">
          <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center text-white shadow-md shadow-primary/20">
            <Shield className="w-5 h-5" />
          </div>
          <div className="space-y-0.5">
            <h2 className="font-bold text-sm tracking-tight text-primary leading-none">Lullaby AI</h2>
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Trợ lý đắc lực</p>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="space-y-1.5 flex-1 -mx-5">
          <button
            onClick={() => {
              setActiveTab("dashboard");
              setIsMobileMenuOpen(false);
            }}
            disabled={!hasBaby}
            title={!hasBaby ? "Hãy tạo hồ sơ bé trước" : undefined}
            className={`w-full flex items-center gap-3 px-5 py-2.5 text-xs font-semibold transition-all ${
              !hasBaby
                ? "text-slate-300 cursor-not-allowed"
                : activeTab === "dashboard"
                ? "text-primary font-bold border-r-4 border-primary bg-primary/10"
                : "text-slate-500 hover:text-primary hover:bg-primary/5"
            }`}
          >
            <LayoutDashboard className="w-4 h-4" />
            Tổng quan
          </button>

          <button
            onClick={() => {
              setActiveTab("profile");
              setIsMobileMenuOpen(false);
            }}
            className={`w-full flex items-center gap-3 px-5 py-2.5 text-xs font-semibold transition-all ${
              activeTab === "profile"
                ? "text-primary font-bold border-r-4 border-primary bg-primary/10"
                : "text-slate-500 hover:text-primary hover:bg-primary/5"
            }`}
          >
            <User className="w-4 h-4" />
            Hồ sơ bé
          </button>

          <button
            onClick={() => {
              setActiveTab("ai");
              setIsMobileMenuOpen(false);
            }}
            disabled={!hasBaby}
            title={!hasBaby ? "Hãy tạo hồ sơ bé trước" : undefined}
            className={`w-full flex items-center gap-3 px-5 py-2.5 text-xs font-semibold transition-all ${
              !hasBaby
                ? "text-slate-300 cursor-not-allowed"
                : activeTab === "ai"
                ? "text-primary font-bold border-r-4 border-primary bg-primary/10"
                : "text-slate-500 hover:text-primary hover:bg-primary/5"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            Phòng Chat AI
          </button>

          <button
            onClick={() => {
              setActiveTab("log");
              setIsMobileMenuOpen(false);
            }}
            disabled={!hasBaby}
            title={!hasBaby ? "Hãy tạo hồ sơ bé trước" : undefined}
            className={`w-full flex items-center gap-3 px-5 py-2.5 text-xs font-semibold transition-all ${
              !hasBaby
                ? "text-slate-300 cursor-not-allowed"
                : activeTab === "log"
                ? "text-primary font-bold border-r-4 border-primary bg-primary/10"
                : "text-slate-500 hover:text-primary hover:bg-primary/5"
            }`}
          >
            <ClipboardList className="w-4 h-4" />
            Nhật ký
          </button>

          <button
            onClick={() => {
              setActiveTab("health");
              setIsMobileMenuOpen(false);
            }}
            disabled={!hasBaby}
            title={!hasBaby ? "Hãy tạo hồ sơ bé trước" : undefined}
            className={`w-full flex items-center gap-3 px-5 py-2.5 text-xs font-semibold transition-all ${
              !hasBaby
                ? "text-slate-300 cursor-not-allowed"
                : activeTab === "health"
                ? "text-primary font-bold border-r-4 border-primary bg-primary/10"
                : "text-slate-500 hover:text-primary hover:bg-primary/5"
            }`}
          >
            <Activity className="w-4 h-4" />
            Sức khỏe
          </button>

          <button
            onClick={() => {
              setActiveTab("growth");
              setIsMobileMenuOpen(false);
            }}
            disabled={!hasBaby}
            title={!hasBaby ? "Hãy tạo hồ sơ bé trước" : undefined}
            className={`w-full flex items-center gap-3 px-5 py-2.5 text-xs font-semibold transition-all ${
              !hasBaby
                ? "text-slate-300 cursor-not-allowed"
                : activeTab === "growth"
                ? "text-primary font-bold border-r-4 border-primary bg-primary/10"
                : "text-slate-500 hover:text-primary hover:bg-primary/5"
            }`}
          >
            <Activity className="w-4 h-4" />
            Tăng trưởng
          </button>

          <button
            onClick={() => {
              setActiveTab("nutrition");
              setIsMobileMenuOpen(false);
            }}
            disabled={!hasBaby}
            title={!hasBaby ? "Hãy tạo hồ sơ bé trước" : undefined}
            className={`w-full flex items-center gap-3 px-5 py-2.5 text-xs font-semibold transition-all ${
              !hasBaby
                ? "text-slate-300 cursor-not-allowed"
                : activeTab === "nutrition"
                ? "text-primary font-bold border-r-4 border-primary bg-primary/10"
                : "text-slate-500 hover:text-primary hover:bg-primary/5"
            }`}
          >
            <Coffee className="w-4 h-4" />
            Dinh dưỡng
          </button>
        </nav>

        {/* Sidebar Footer Widget - Logged-in user + logout */}
        <div className="pt-4 border-t border-slate-200/60 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs shrink-0">
              {(name || email || "?").charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold text-slate-800 leading-tight truncate">{name || "Người giám hộ"}</p>
              <p className="text-[9px] text-slate-400 font-semibold truncate">{email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            title="Đăng xuất"
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-50 transition-colors cursor-pointer shrink-0"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </aside>

      {/* Main Canvas Area */}
      <main className="flex-1 flex flex-col min-w-0">
        
        {/* Top bar header */}
        <header className="hidden md:flex bg-white border-b border-slate-100 px-8 py-3.5 items-center justify-between sticky top-0 z-30">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-600 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-ping" />
              Family Server Online
            </span>
            {isNapTimerRunning && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-600 animate-pulse">
                Nap Active Ticking...
              </span>
            )}
          </div>

          <div className="flex items-center gap-4">
            <button className="p-1.5 hover:bg-slate-50 rounded-xl text-slate-400 hover:text-slate-600 transition-colors relative">
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-rose-500 rounded-full" />
            </button>
            
            <div className="h-5 w-px bg-slate-200" />
            
            {activeBaby && (
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-700">{activeBaby.name}</span>
                <img
                  src={activeBaby.avatarUrl}
                  alt={activeBaby.name}
                  className="w-7 h-7 rounded-full object-cover border border-slate-200"
                />
              </div>
            )}
          </div>
        </header>

        {/* Content canvas container */}
        <div className="flex-1 p-4 md:p-8 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab + "_" + (activeBaby?.id ?? "onboarding")}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: 0.15 }}
              className="h-full"
            >
              {/* Chưa có hồ sơ bé nào (mới đăng ký xong) - luôn hiện trang Hồ sơ để nhập
                  thông tin bé đầu tiên, bất kể activeTab là gì (nav các tab khác đã bị khoá). */}
              {!activeBaby ? (
                <ProfileView
                  babies={babies}
                  guardians={guardians}
                  onSelectBaby={handleSelectBaby}
                  onUpdateBaby={handleUpdateBaby}
                  onAddBaby={handleAddBaby}
                  onDeleteBaby={handleDeleteBaby}
                  onUploadAvatar={handleUploadAvatar}
                  onAddGuardian={handleAddGuardian}
                  onDeleteGuardian={handleDeleteGuardian}
                />
              ) : (
                <>
              {activeTab === "dashboard" && (
                <DashboardView
                  activeBaby={activeBaby}
                  babies={babies}
                  onSelectBaby={handleSelectBaby}
                  medications={medications.filter((m) => m.babyId === activeBaby.id)}
                  feeds={feeds.filter((f) => f.babyId === activeBaby.id)}
                  measurements={measurements.filter((m) => m.babyId === activeBaby.id)}
                  chats={chats}
                  isAiLoading={isAiLoading}
                  isNapTimerRunning={isNapTimerRunning}
                  napElapsedTime={napElapsedTime}
                  onSendMessage={handleSendMessage}
                  onConfirmExtraction={handleConfirmExtraction}
                  onStartNapTimer={handleStartNapTimer}
                  onAddMedication={handleAddMedication}
                  onDeleteMedication={handleDeleteMedication}
                  onAddFeed={handleAddFeed}
                  onDeleteFeed={handleDeleteFeed}
                  onAddMeasurement={handleAddMeasurement}
                  onDeleteMeasurement={handleDeleteMeasurement}
                  onNavigateTab={(tab) => setActiveTab(tab as any)}
                />
              )}

              {activeTab === "growth" && (
                <GrowthView
                  activeBaby={activeBaby}
                  measurements={measurements.filter((m) => m.babyId === activeBaby.id)}
                  onAddMeasurement={handleAddMeasurement}
                  onDeleteMeasurement={handleDeleteMeasurement}
                />
              )}

              {activeTab === "health" && (
                <HealthView
                  activeBaby={activeBaby}
                  medications={medications.filter((m) => m.babyId === activeBaby.id)}
                  onAddMedication={handleAddMedication}
                  onDeleteMedication={handleDeleteMedication}
                />
              )}

              {activeTab === "ai" && (
                <AiHubView
                  activeBaby={activeBaby}
                  babies={babies}
                  onSelectBaby={handleSelectBaby}
                  chats={chats}
                  onSendMessage={handleSendMessage}
                  onConfirmExtraction={handleConfirmExtraction}
                  isAiLoading={isAiLoading}
                  onStartNapTimer={handleStartNapTimer}
                  isNapTimerRunning={isNapTimerRunning}
                  napElapsedTime={napElapsedTime}
                  threads={threads}
                  activeThreadId={activeThreadId}
                  onSelectThread={handleSelectThread}
                  onCreateThread={handleCreateThread}
                />
              )}

              {activeTab === "profile" && (
                <ProfileView
                  babies={babies}
                  guardians={guardians}
                  onSelectBaby={handleSelectBaby}
                  onUpdateBaby={handleUpdateBaby}
                  onAddBaby={handleAddBaby}
                  onDeleteBaby={handleDeleteBaby}
                  onUploadAvatar={handleUploadAvatar}
                  onAddGuardian={handleAddGuardian}
                  onDeleteGuardian={handleDeleteGuardian}
                />
              )}

              {((activeTab as string) === "log" || (activeTab as string) === "logs") && (
                <LogsView
                  activeBaby={activeBaby}
                  feeds={feeds.filter((f) => f.babyId === activeBaby.id)}
                  medications={medications.filter((m) => m.babyId === activeBaby.id)}
                  measurements={measurements.filter((m) => m.babyId === activeBaby.id)}
                  onAddFeed={handleAddFeed}
                  onDeleteFeed={handleDeleteFeed}
                  onAddMedication={handleAddMedication}
                  onDeleteMedication={handleDeleteMedication}
                  onAddMeasurement={handleAddMeasurement}
                />
              )}

              {activeTab === "nutrition" && (
                <NutritionView
                  activeBaby={activeBaby}
                  feeds={feeds.filter((f) => f.babyId === activeBaby.id)}
                  ingredients={ingredients.filter((i) => i.babyId === activeBaby.id)}
                  onAddFeed={handleAddFeed}
                  onDeleteFeed={handleDeleteFeed}
                  onAddIngredient={handleAddIngredient}
                  onDeleteIngredient={handleDeleteIngredient}
                  recommendation={nutritionRecommendation}
                  isGeneratingRecommendation={isGeneratingRecommendation}
                  onGenerateRecommendation={handleGenerateNutritionRecommendation}
                  weeklyMealPlan={weeklyMealPlan}
                  isGeneratingWeeklyPlan={isGeneratingWeeklyPlan}
                  isAcceptingWeeklyPlan={isAcceptingWeeklyPlan}
                  onGenerateWeeklyMealPlan={handleGenerateWeeklyMealPlan}
                  onAcceptWeeklyMealPlan={handleAcceptWeeklyMealPlan}
                  nutritionSafety={nutritionSafety}
                  safetyHandbook={safetyHandbook}
                  isLoadingSafetyHandbook={isLoadingSafetyHandbook}
                  onOpenSafetyHandbook={handleOpenSafetyHandbook}
                />
              )}
                </>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

    </div>
  );
}
