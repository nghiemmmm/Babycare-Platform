import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
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
  Clock,
  BookOpen
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
  SmartExtraction
} from "./types";


import DashboardView from "./components/DashboardView";
import GrowthView from "./components/GrowthView";
import AiHubView from "./components/AiHubView";
import ProfileView from "./components/ProfileView";
import NutritionView from "./components/NutritionView";
import HealthView from "./components/HealthView";
import LogsView from "./components/LogsView";

const apiFetch = async (path: string, options: RequestInit = {}) => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || "";
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${baseUrl}${cleanPath}`;
  const headers = new Headers(options.headers);
  if (!headers.has("Authorization")) {
    headers.set("Authorization", "Bearer mock-token");
  }
  return fetch(url, {
    ...options,
    headers,
  });
};

export default function App() {
  // Core persistent states backed by Backend APIs
  const [babies, setBabies] = useState<BabyProfile[]>([]);
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [medications, setMedications] = useState<MedicationLog[]>([]);
  const [guardians, setGuardians] = useState<Guardian[]>([]);
  const [feeds, setFeeds] = useState<FeedLog[]>([]);
  const [ingredients, setIngredients] = useState<IngredientLog[]>([]);
  const [chats, setChats] = useState<ChatMessage[]>([]);
  const [threads, setThreads] = useState<Array<{ id: string; title: string }>>([]);
  const [activeThreadId, setActiveThreadId] = useState<string>("thread_default");

  // App UI state
  const [activeTab, setActiveTab] = useState<"dashboard" | "growth" | "ai" | "profile" | "nutrition" | "health" | "logs">("dashboard");
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
          date: "Today"
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

    } catch (e) {
      console.error("Error refreshing active baby data:", e);
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
    try {
      const res = await apiFetch(`/api/v1/ai/threads/${threadId}/messages`);
      if (res.ok) {
        const data = await res.json();
        const recentMessages = Array.isArray(data) ? data.slice(-6) : [];
        setChats(recentMessages.map((c: any) => ({
          id: c.id,
          role: c.role,
          content: c.content,
          timestamp: c.timestamp.includes("T") ? c.timestamp.slice(11, 16) : c.timestamp
        })));
      } else {
        setChats([]);
      }
    } catch (e) {
      console.error("Failed to load thread messages:", e);
      setChats([]);
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
            const mapped = data.map((b: any, index: number) => ({
              id: b.id,
              name: b.name,
              birthDate: b.birth_date,
              gender: mapBackendGender(b.gender),
              avatarUrl: b.avatar_url || "/static/img/leo.png",
              isActive: b.is_active || (index === 0)
            }));
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
  }, []);

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
                setBabies(dataBabies.map((b: any, index: number) => ({
                  id: b.id,
                  name: b.name,
                  birthDate: b.birth_date,
                  gender: mapBackendGender(b.gender),
                  avatarUrl: b.avatar_url || "/static/img/leo.png",
                  isActive: index === 0
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
    }
  }, [activeBaby?.id]);

  // Sync active baby with threads list
  useEffect(() => {
    if (activeBaby?.id) {
      loadThreads();
    }
  }, [activeBaby?.id]);

  // Sync active thread with messages list
  useEffect(() => {
    if (activeThreadId) {
      loadThreadMessages(activeThreadId);
    }
  }, [activeThreadId]);

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
    setBabies((prev) =>
      prev.map((b) => ({
        ...b,
        isActive: b.id === id
      }))
    );
  };

  const handleUpdateBaby = async (updated: BabyProfile) => {
    try {
      const res = await apiFetch(`/api/v1/babies/${updated.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: updated.name,
          birth_date: updated.birthDate,
          gender: updated.gender,
          avatar_url: updated.avatarUrl,
          is_active: updated.isActive
        })
      });
      if (res.ok) {
        setBabies((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddBaby = async (newBaby: Omit<BabyProfile, "id">) => {
    try {
      const res = await apiFetch("/api/v1/babies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newBaby.name,
          birth_date: newBaby.birthDate,
          gender: newBaby.gender,
          avatar_url: newBaby.avatarUrl,
          is_active: true
        })
      });
      if (res.ok) {
        const data = await res.json();
        // Reload all babies
        const bRes = await apiFetch("/api/v1/babies");
        if (bRes.ok) {
          const bData = await bRes.json();
          const mapped = bData.map((b: any) => ({
            id: b.id,
            name: b.name,
            birthDate: b.birth_date,
            gender: mapBackendGender(b.gender),
            avatarUrl: b.avatar_url || "/static/img/leo.png",
            isActive: b.id === data.id
          }));
          setBabies(mapped);
        }
      }
    } catch (e) {
      console.error(e);
    }
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

  // AI assistant messaging with direct API calls to FastAPI backend
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
          type: "text"
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

      setChats((prev) => [
        ...prev,
        {
          id: `ai_${Date.now()}`,
          role: "assistant",
          content: aiContent,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          extraction,
          citations
        }
      ]);
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
            className={`w-full flex items-center gap-3 px-5 py-2.5 text-xs font-semibold transition-all ${
              activeTab === "dashboard"
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
            className={`w-full flex items-center gap-3 px-5 py-2.5 text-xs font-semibold transition-all ${
              activeTab === "ai"
                ? "text-primary font-bold border-r-4 border-primary bg-primary/10"
                : "text-slate-500 hover:text-primary hover:bg-primary/5"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            Phòng Chat AI
          </button>

          <button
            onClick={() => {
              setActiveTab("logs");
              setIsMobileMenuOpen(false);
            }}
            className={`w-full flex items-center gap-3 px-5 py-2.5 text-xs font-semibold transition-all ${
              activeTab === "logs"
                ? "text-primary font-bold border-r-4 border-primary bg-primary/10"
                : "text-slate-500 hover:text-primary hover:bg-primary/5"
            }`}
          >
            <Clock className="w-4 h-4" />
            Nhật ký
          </button>

          <button
            onClick={() => {
              setActiveTab("nutrition");
              setIsMobileMenuOpen(false);
            }}
            className={`w-full flex items-center gap-3 px-5 py-2.5 text-xs font-semibold transition-all ${
              activeTab === "nutrition"
                ? "text-primary font-bold border-r-4 border-primary bg-primary/10"
                : "text-slate-500 hover:text-primary hover:bg-primary/5"
            }`}
          >
            <Coffee className="w-4 h-4" />
            Dinh dưỡng
          </button>

          <button
            onClick={() => {
              setActiveTab("health");
              setIsMobileMenuOpen(false);
            }}
            className={`w-full flex items-center gap-3 px-5 py-2.5 text-xs font-semibold transition-all ${
              activeTab === "health"
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
            className={`w-full flex items-center gap-3 px-5 py-2.5 text-xs font-semibold transition-all ${
              activeTab === "growth"
                ? "text-primary font-bold border-r-4 border-primary bg-primary/10"
                : "text-slate-500 hover:text-primary hover:bg-primary/5"
            }`}
          >
            <Activity className="w-4 h-4" />
            Tăng trưởng
          </button>
        </nav>

        {/* Sidebar Footer Widget - Selected Baby Quick View / User profile */}
        <div className="pt-4 border-t border-slate-200/60 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <img
              src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop&crop=face"
              alt="Sarah Jenkins"
              className="w-8 h-8 rounded-full object-cover border border-slate-200 shadow-xs"
            />
            <div>
              <p className="text-xs font-bold text-slate-800 leading-tight">Sarah Jenkins</p>
              <p className="text-[9px] text-indigo-600 font-semibold">Premium Member</p>
            </div>
          </div>
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
        </header>

        {/* Content canvas container */}
        <div className="flex-1 p-4 md:p-8 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab + "_" + activeBaby.id}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: 0.15 }}
              className="h-full"
            >
              {activeTab === "dashboard" && (
                <DashboardView
                  activeBaby={activeBaby}
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
                  onAddGuardian={handleAddGuardian}
                  onDeleteGuardian={handleDeleteGuardian}
                />
              )}

              {activeTab === "logs" && (
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
                />
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

    </div>
  );
}
