import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Shield,
  Plus,
  Bell,
  Settings,
  Baby,
  Moon,
  Droplet,
  Pill,
  ChevronRight,
  TrendingUp,
  Activity,
  ArrowRight,
  Clock,
  Sparkles,
  MessageSquare,
  Mic,
  Send,
  Volume2,
  VolumeX,
  AlertCircle,
  Check,
  ChevronDown,
  Trash2,
  Scale,
  Ruler,
  Upload,
  RefreshCw,
  CheckCircle2
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from "recharts";
import { BabyProfile, MedicationLog, FeedLog, Measurement, ChatMessage, SmartExtraction, NotificationItem } from "../types";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";

interface DashboardViewProps {
  activeBaby: BabyProfile;
  babies?: BabyProfile[];
  onSelectBaby?: (id: string) => void;
  medications: MedicationLog[];
  feeds: FeedLog[];
  measurements: Measurement[];
  chats: ChatMessage[];
  isAiLoading: boolean;
  isNapTimerRunning: boolean;
  napElapsedTime: number;
  onSendMessage: (text: string) => Promise<void>;
  onConfirmExtraction: (ext: SmartExtraction) => void;
  onStartNapTimer: () => void;
  onAddMedication: (med: Omit<MedicationLog, "id">) => void;
  onDeleteMedication: (id: string) => void;
  onAddFeed: (feed: Omit<FeedLog, "id">) => void;
  onDeleteFeed: (id: string) => void;
  onAddMeasurement: (m: Omit<Measurement, "id">) => void;
  onDeleteMeasurement: (id: string) => void;
  onNavigateTab?: (tab: string) => void;
}

// Static WHO standard median reference data (0-12 months) for boys & girls
const WHO_BOY_WEIGHT_STANDARDS = [
  { month: 0, median: 3.3, percentile3: 2.4, percentile97: 4.3 },
  { month: 2, median: 5.6, percentile3: 4.3, percentile97: 7.1 },
  { month: 4, median: 7.0, percentile3: 5.6, percentile97: 8.7 },
  { month: 6, median: 7.9, percentile3: 6.4, percentile97: 9.8 },
  { month: 8, median: 8.6, percentile3: 7.0, percentile97: 10.7 },
  { month: 10, median: 9.2, percentile3: 7.5, percentile97: 11.4 },
  { month: 12, median: 9.6, percentile3: 7.8, percentile97: 12.0 }
];

const WHO_GIRL_WEIGHT_STANDARDS = [
  { month: 0, median: 3.2, percentile3: 2.4, percentile97: 4.2 },
  { month: 2, median: 5.1, percentile3: 3.9, percentile97: 6.6 },
  { month: 4, median: 6.4, percentile3: 5.0, percentile97: 8.2 },
  { month: 8, median: 8.0, percentile3: 6.3, percentile97: 10.2 },
  { month: 10, median: 8.5, percentile3: 6.7, percentile97: 10.9 },
  { month: 12, median: 8.9, percentile3: 7.0, percentile97: 11.5 }
];

const WHO_BOY_HEIGHT_STANDARDS = [
  { month: 0, median: 49.9, percentile3: 46.1, percentile97: 53.7 },
  { month: 2, median: 58.4, percentile3: 54.4, percentile97: 62.4 },
  { month: 4, median: 63.9, percentile3: 59.7, percentile97: 68.0 },
  { month: 6, median: 67.6, percentile3: 63.3, percentile97: 71.9 },
  { month: 8, median: 70.6, percentile3: 66.2, percentile97: 75.0 },
  { month: 10, median: 73.3, percentile3: 68.7, percentile97: 77.9 },
  { month: 12, median: 75.7, percentile3: 71.0, percentile97: 80.5 }
];

const WHO_GIRL_HEIGHT_STANDARDS = [
  { month: 0, median: 49.1, percentile3: 45.4, percentile97: 52.9 },
  { month: 2, median: 57.1, percentile3: 53.0, percentile97: 61.1 },
  { month: 4, median: 62.1, percentile3: 57.8, percentile97: 66.4 },
  { month: 6, median: 65.7, percentile3: 61.2, percentile97: 70.3 },
  { month: 8, median: 68.7, percentile3: 64.0, percentile97: 73.5 },
  { month: 10, median: 71.5, percentile3: 66.7, percentile97: 76.4 },
  { month: 12, median: 74.0, percentile3: 68.9, percentile97: 79.2 }
];

export default function DashboardView({
  activeBaby,
  babies = [],
  onSelectBaby,
  medications,
  feeds,
  measurements,
  chats,
  isAiLoading,
  isNapTimerRunning,
  napElapsedTime,
  onSendMessage,
  onConfirmExtraction,
  onStartNapTimer,
  onAddMedication,
  onDeleteMedication,
  onAddFeed,
  onDeleteFeed,
  onAddMeasurement,
  onDeleteMeasurement,
  onNavigateTab
}: DashboardViewProps) {
  // Modals visibility states
  const [activeModal, setActiveModal] = useState<"none" | "add-entry" | "feed" | "sleep" | "diaper" | "medication" | "growth">("none");
  const [showBabyDropdown, setShowBabyDropdown] = useState(false);

  // Growth Metric Toggle state (weight or height)
  const [growthMetric, setGrowthMetric] = useState<"weight" | "height">("weight");

  // Form states for Feed
  const [feedType, setFeedType] = useState<"Formula" | "Breast" | "Solids">("Formula");
  const [feedAmount, setFeedAmount] = useState(150);
  const [feedDetails, setFeedDetails] = useState("Formula Milk");
  
  // Form states for Diaper
  const [diaperType, setDiaperType] = useState<"Wet" | "Dirty" | "Both">("Wet");
  const [diaperStatus, setDiaperStatus] = useState("Normal");

  // Form states for Medication
  const [medName, setMedName] = useState("Vitamin D drops");
  const [medDosage, setMedDosage] = useState("2 drops");
  const [prescribedBy, setPrescribedBy] = useState("Dr. Aris");

  // Form states for Measurement
  const [growthWeight, setGrowthWeight] = useState(7.4);
  const [growthHeight, setGrowthHeight] = useState(67);
  const [growthAgeMonths, setGrowthAgeMonths] = useState(6);

  // Form states for Chat
  const [chatInput, setChatInput] = useState("");
  const [isRecording, setIsRecording] = useState(false);

  // Local state for tracking Diaper logs and Temperature
  const [diaperLogs, setDiaperLogs] = useState<Array<{ id: string; time: string; type: "Wet" | "Dirty" | "Both"; status: string }>>([
    { id: "d1", time: "10:45 AM", type: "Wet", status: "Normal" },
    { id: "d2", time: "07:30 AM", type: "Dirty", status: "Soft" },
    { id: "d3", time: "06:15 AM", type: "Wet", status: "Normal" }
  ]);
  const [temperatureLogs, setTemperatureLogs] = useState<Array<{ id: string; time: string; temp: number; status: string }>>([
    { id: "t1", time: "09:00 AM", temp: 36.8, status: "Optimal" }
  ]);

  // Notifications State & Fetching from Backend
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  // Quick Settings State
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isSoundEnabled, setIsSoundEnabled] = useState(true);
  const [unitSystem, setUnitSystem] = useState<"metric" | "imperial">("metric");

  // Voice Extraction Loading State
  const [isExtractingVoice, setIsExtractingVoice] = useState(false);

  // AI Cry Detection State & Handlers
  const [isAnalyzingCry, setIsAnalyzingCry] = useState(false);
  const [cryFeedback, setCryFeedback] = useState<"accurate" | "inaccurate" | null>(null);
  const [cryResult, setCryResult] = useState<{
    prediction: string;
    label: string;
    confidence: number;
    reasonScores?: Record<string, number>;
    soothingSound: string;
    advice: string;
    logId: string;
  } | null>(null);
  const cryFileInputRef = useRef<HTMLInputElement | null>(null);

  const getCryAdvice = (pred: string, name: string) => {
    switch (pred) {
      case "hungry":
        return `Bé ${name} có dấu hiệu đói bú. Vui lòng kiểm tra cữ ăn gần nhất và chuẩn bị cữ sữa ấm cho bé.`;
      case "tired":
        return `Bé ${name} đang mệt và gắt ngủ. Vui lòng hạ ánh sáng phòng, bật nhạc ru nhẹ nhàng và bế đung đưa bé.`;
      case "pain":
        return `Bé ${name} có thể đang bị đau bụng hoặc đầy hơi. Hãy vỗ lưng ợ hơi, chần ấm bụng và theo dõi thêm.`;
      case "burp":
        return `Bé ${name} cần ợ hơi sau cữ bú. Phụ huynh nên bế đứng ép bụng bé vào vai và vỗ lưng nhẹ nhàng.`;
      case "diaper":
        return `Tã của bé ${name} có thể đã ẩm ướt hoặc bẩn. Vui lòng kiểm tra và thay tã mới sạch sẽ cho bé.`;
      case "discomfort":
        return `Bé ${name} cảm thấy không thoải mái (nóng/lạnh hoặc quần áo chật). Vui lòng kiểm tra nhiệt độ phòng và trang phục.`;
      case "lonely":
        return `Bé ${name} đang cần sự chú ý và vỗ về từ cha mẹ. Hãy ôm bé vào lòng và nói chuyện nhẹ nhàng với bé.`;
      case "scared":
        return `Bé ${name} bị giật mình hoặc sợ hãi bởi tiếng động lạ. Hãy ôm chặt bé và bật tiếng ồn trắng để xoa dịu.`;
      default:
        return `Bé ${name} đang cảm thấy khó chịu. Phụ huynh nên kiểm tra nhiệt độ phòng, tã lót và vỗ về bé.`;
    }
  };

  const handleStartCryAnalysis = async (selectedFile?: File) => {
    setIsAnalyzingCry(true);
    setCryFeedback(null);
    try {
      const formData = new FormData();
      if (selectedFile) {
        formData.append("audio_file", selectedFile);
      } else {
        // Lấy tệp âm thanh WAV mẫu hợp lệ từ static server để chạy thử nghiệm
        try {
          const sampleRes = await fetch("/static/samples/cry_samples/sample_baby_cry.wav");
          if (sampleRes.ok) {
            const sampleBlob = await sampleRes.blob();
            formData.append("audio_file", sampleBlob, "sample_baby_cry.wav");
          } else {
            throw new Error("Cannot fetch sample audio file");
          }
        } catch (fetchErr) {
          const emptyAudioHeader = new Uint8Array([82, 73, 70, 70, 36, 0, 0, 0, 87, 65, 86, 69, 102, 109, 116, 32, 16, 0, 0, 0, 1, 0, 1, 0, 128, 62, 0, 0, 0, 125, 0, 0, 2, 0, 16, 0, 100, 97, 116, 97, 0, 0, 0, 0]);
          const sampleBlob = new Blob([emptyAudioHeader], { type: "audio/wav" });
          formData.append("audio_file", sampleBlob, "sample_baby_cry.wav");
        }
      }

      const baseUrl = import.meta.env.VITE_API_BASE_URL || "";
      const token = localStorage.getItem("token") || "mock-token";
      const res = await fetch(`${baseUrl}/api/v1/babies/${activeBaby.id}/cry-prediction`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        const pred = data.prediction || "hungry";
        const labels: Record<string, string> = {
          hungry: "Khóc do Đói 🍼",
          tired: "Khóc do Gắt ngủ 🥱",
          pain: "Khóc do Đau/Đầy hơi 😣",
          burp: "Khóc do Cần ợ hơi 💨",
          diaper: "Khóc do Bẩn tã 💩",
          discomfort: "Khóc do Khó chịu 🌡️",
          lonely: "Khóc do Cần bế/Cô đơn 🫂",
          scared: "Khóc do Giật mình/Sợ hãi 😨"
        };
        const soundPath = data.sound_played || "/static/sounds/lullabies/classic_lullaby.mp3";

        setCryResult({
          prediction: pred,
          label: labels[pred] || "Khóc do Khó chịu 🌡️",
          confidence: Math.round((data.confidence || 0.85) * 100),
          reasonScores: data.reason_scores || {},
          soothingSound: soundPath,
          advice: getCryAdvice(pred, activeBaby.name),
          logId: data.id || `cry_${Date.now()}`
        });
        showToast("success", "Phân tích hoàn tất", `AI chẩn đoán: ${labels[pred] || pred}`);
      } else {
        const errData = await res.json().catch(() => ({}));
        showToast("error", "Lỗi phân tích", errData.detail || "Không thể phân tích tệp âm thanh này.");
      }
    } catch (e) {
      console.error("Error analyzing cry:", e);
      showToast("error", "Lỗi kết nối", "Lỗi kết nối với máy chủ phân tích tiếng khóc.");
    } finally {
      setIsAnalyzingCry(false);
    }
  };

  const handleSendCryFeedback = async (accurate: boolean) => {
    setCryFeedback(accurate ? "accurate" : "inaccurate");
    if (cryResult?.logId) {
      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || "";
        const token = localStorage.getItem("token");
        await fetch(`${baseUrl}/api/v1/babies/${activeBaby.id}/cry-prediction/${cryResult.logId}/feedback?feedback_accurate=${accurate}`, {
          method: "PATCH",
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
      } catch (e) {
        console.error("Error submitting cry feedback:", e);
      }
    }
  };

  // Process voice transcript with FastAPI AI Agent Backend
  const handleProcessVoiceTranscript = useCallback(async (text: string) => {
    if (!text.trim()) return;
    setIsExtractingVoice(true);
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || "";
      const res = await fetch(`${baseUrl}/api/v1/ai/voice-extract`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer mock-token"
        },
        body: JSON.stringify({ transcript: text, baby_id: activeBaby.id }),
      });
      if (res.ok) {
        const data = await res.json();
        const { intent, extracted_data } = data;
        
        if (intent === "feeding") {
          if (extracted_data.type) setFeedType(extracted_data.type);
          if (extracted_data.amount) setFeedAmount(extracted_data.amount);
          if (extracted_data.details) setFeedDetails(extracted_data.details);
          setActiveModal("feed");
        } else if (intent === "medication") {
          if (extracted_data.medication_name) setMedName(extracted_data.medication_name);
          if (extracted_data.dosage) setMedDosage(extracted_data.dosage);
          setActiveModal("medication");
        } else if (intent === "growth") {
          if (extracted_data.weight) setGrowthWeight(extracted_data.weight);
          if (extracted_data.height) setGrowthHeight(extracted_data.height);
          setActiveModal("growth");
        } else if (intent === "diaper") {
          if (extracted_data.type) setDiaperType(extracted_data.type);
          setActiveModal("diaper");
        } else if (intent === "sleep") {
          setActiveModal("sleep");
        } else {
          setActiveModal("feed");
        }
      } else {
        showToast("error", "Lỗi kết nối", "Không thể kết nối máy chủ phân tích AI.");
      }
    } catch (err) {
      console.error("Error processing voice transcript with AI:", err);
      showToast("error", "Lỗi bóc tách", "Đã xảy ra lỗi khi xử lý giọng nói.");
    } finally {
      setIsExtractingVoice(false);
    }
  }, [activeBaby.id]);

  // Speech Recognition & Voice Extraction State with Auto-Silence Detection (1.5s)
  const { isListening, transcript, startListening, stopListening, resetTranscript } = useSpeechRecognition({
    silenceTimeoutMs: 1500,
    onSilence: (finalText) => {
      handleProcessVoiceTranscript(finalText);
    }
  });

  // Toast Notification System (Success & Failure)
  interface ToastNotification {
    type: "success" | "error";
    title: string;
    message: string;
  }
  const [toast, setToast] = useState<ToastNotification | null>(null);

  const showToast = (type: "success" | "error", title: string, message: string) => {
    setToast({ type, title, message });
    setTimeout(() => setToast(null), 3500);
  };

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const res = await fetch(`/api/v1/dashboard/notifications?baby_id=${activeBaby.id}`, {
          headers: { "Authorization": "Bearer mock-token" }
        });
        if (res.ok) {
          const data = await res.json();
          setNotifications(data);
        }
      } catch (err) {
        console.warn("Could not fetch notifications from backend:", err);
      }
    };
    fetchNotifications();
  }, [activeBaby.id]);

  const handleMarkAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    notifications.forEach(async (n) => {
      if (!n.read) {
        try {
          await fetch(`/api/v1/dashboard/notifications/${n.id}/read`, {
            method: "POST",
            headers: { "Authorization": "Bearer mock-token" }
          });
        } catch (e) {
          // silent fallback
        }
      }
    });
  };

  const chatContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chats, isAiLoading]);

  // Compute stats
  const lastFeed = feeds.filter(f => f.type === "Formula" || f.type === "Breast")[0];
  const lastFeedStr = lastFeed ? `${lastFeed.amount} ml` : "150 ml";
  const lastFeedDetail = lastFeed ? lastFeed.details : "Breastmilk";
  
  // Calculate diaper count today
  const diaperCountStr = `${diaperLogs.length} today`;

  // Calculate current temperature
  const currentTemp = temperatureLogs[0]?.temp || 36.8;

  // Calculate age of activeBaby
  const calculateAgeStr = (birthDateStr: string) => {
    const birth = new Date(birthDateStr);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - birth.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    const years = Math.floor(diffDays / 365);
    const remainingDays = diffDays % 365;
    const months = Math.floor(remainingDays / 30.4);
    if (years > 0) {
      return `${years} tuổi`;
    }
    if (months === 0) {
      return `${diffDays} ngày`;
    }
    return `${months} tháng`;
  };

  const getLatestWeight = () => {
    if (measurements.length > 0) {
      const sorted = [...measurements].sort((a, b) => b.ageInMonths - a.ageInMonths);
      return `${sorted[0].weight} kg`;
    }
    return "7.4 kg";
  };

  const getLatestHeight = () => {
    if (measurements.length > 0) {
      const sorted = [...measurements].sort((a, b) => b.ageInMonths - a.ageInMonths);
      return `${sorted[0].height} cm`;
    }
    return "67 cm";
  };

  // Compile Growth Trajectory Chart Data
  const isBoy = activeBaby.gender !== "Girl";
  const weightStandards = isBoy ? WHO_BOY_WEIGHT_STANDARDS : WHO_GIRL_WEIGHT_STANDARDS;
  const heightStandards = isBoy ? WHO_BOY_HEIGHT_STANDARDS : WHO_GIRL_HEIGHT_STANDARDS;
  const standards = growthMetric === "weight" ? weightStandards : heightStandards;
  
  const chartData = standards.map((std) => {
    const match = measurements.find(m => Math.abs(m.ageInMonths - std.month) <= 0.5);
    const val = match
      ? (growthMetric === "weight" ? match.weight : match.height)
      : (std.month === 6 ? parseFloat(growthMetric === "weight" ? getLatestWeight() : getLatestHeight()) : undefined);

    return {
      name: std.month === 0 ? "Birth" : `${std.month}M`,
      "WHO Median": std.median,
      "WHO 3rd": std.percentile3,
      "WHO 97th": std.percentile97,
      [activeBaby.name]: val
    };
  });

  // Handle Quick Chat Submit
  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isAiLoading) return;
    onSendMessage(chatInput);
    setChatInput("");
  };

  // Mic voice memo input toggle
  const handleToggleMic = () => {
    if (isListening) {
      stopListening();
      if (transcript) {
        setChatInput(transcript);
      }
    } else {
      startListening();
    }
  };

  // Handle modals submit
  const handleAddFeedSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const now = new Date();
      const timeStr = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      onAddFeed({
        babyId: activeBaby.id,
        type: feedType,
        details: feedType === "Solids" ? feedDetails : `${feedAmount}ml ${feedType === "Formula" ? "Formula" : "Breastmilk"}`,
        amount: feedType === "Solids" ? 1 : feedAmount,
        time: timeStr,
        date: "Today"
      });
      setActiveModal("none");
      showToast("success", "Thành công!", "Đã lưu nhật ký cữ bú thành công! 🍼");
    } catch (err) {
      showToast("error", "Thất bại!", "Không thể lưu nhật ký cữ bú. Vui lòng thử lại.");
    }
  };

  const handleAddDiaperSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const now = new Date();
      const timeStr = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      setDiaperLogs(prev => [
        { id: `diaper_${Date.now()}`, time: timeStr, type: diaperType, status: diaperStatus },
        ...prev
      ]);
      setActiveModal("none");
      showToast("success", "Thành công!", "Đã ghi nhận thay tã thành công! 💩");
    } catch (err) {
      showToast("error", "Thất bại!", "Không thể lưu thông tin thay tã.");
    }
  };

  const handleAddMedicationSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const now = new Date();
      const timeStr = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      onAddMedication({
        babyId: activeBaby.id,
        name: medName,
        dosage: medDosage,
        time: timeStr,
        date: "Today",
        prescribedBy: prescribedBy || "Self Logged"
      });
      setActiveModal("none");
      showToast("success", "Thành công!", "Đã lưu nhật ký dùng thuốc thành công! 💊");
    } catch (err) {
      showToast("error", "Thất bại!", "Không thể lưu thông tin thuốc.");
    }
  };

  const handleAddMeasurementSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    try {
      onAddMeasurement({
        babyId: activeBaby.id,
        date: new Date().toISOString().split("T")[0],
        ageInMonths: growthAgeMonths,
        weight: growthWeight,
        height: growthHeight,
        headCircumference: 42.5,
        status: "Normal"
      });
      setActiveModal("none");
      showToast("success", "Thành công!", "Đã cập nhật chỉ số tăng trưởng thành công! 📈");
    } catch (err) {
      showToast("error", "Thất bại!", "Không thể lưu chỉ số tăng trưởng.");
    }
  };

  // Combine feeds, meds, diapers into a single chronological timeline for today
  const combinedTimeline = [
    ...feeds.map(f => ({
      id: f.id,
      time: f.time,
      type: "feed",
      title: f.type === "Solids" ? "Solids Feed" : f.type === "Formula" ? "Formula Feed" : "Breast Feed",
      detail: f.details,
      rawType: f.type
    })),
    ...medications.map(m => ({
      id: m.id,
      time: m.time,
      type: "medication",
      title: m.name,
      detail: `Dosage: ${m.dosage} • Prescribed by: ${m.prescribedBy || "Self"}`,
      rawType: "Med"
    })),
    ...diaperLogs.map(d => ({
      id: d.id,
      time: d.time,
      type: "diaper",
      title: "Diaper Change",
      detail: `${d.type} Diaper • ${d.status}`,
      rawType: "Diaper"
    }))
  ].sort((a, b) => {
    const timeToMinutes = (tStr: string) => {
      const match = tStr.match(/(\d+):(\d+)\s*(AM|PM)/i);
      if (!match) return 0;
      let h = parseInt(match[1]);
      const m = parseInt(match[2]);
      const ampm = match[3].toUpperCase();
      if (ampm === "PM" && h < 12) h += 12;
      if (ampm === "AM" && h === 12) h = 0;
      return h * 60 + m;
    };
    return timeToMinutes(b.time) - timeToMinutes(a.time); // newest first
  });

  return (
    <div className="space-y-6" id="dashboard-view">
      
      {/* Floating Toast Notification (Success & Error) */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -25, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -25, scale: 0.9 }}
            className={`fixed top-6 right-6 z-50 text-white px-5 py-3.5 rounded-2xl shadow-2xl border border-white/20 flex items-center gap-3 backdrop-blur-xl transition-all ${
              toast.type === "success" ? "bg-[#1c648e]" : "bg-rose-600"
            }`}
          >
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center font-black text-xs shrink-0 ${
                toast.type === "success" ? "bg-emerald-400 text-slate-900" : "bg-white text-rose-600"
              }`}
            >
              {toast.type === "success" ? "✓" : "✕"}
            </div>
            <div>
              <h4 className="text-xs font-bold">{toast.title}</h4>
              <p className="text-[11px] text-white/90 font-medium">{toast.message}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      {/* 1. Header Profile Selector & Quick Action Panel */}
      <div className="relative z-30 bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          {/* Baby selector profile */}
          <div className="relative">
            <div
              onClick={() => setShowBabyDropdown(!showBabyDropdown)}
              className="flex items-center gap-4 cursor-pointer group"
            >
              <div className="relative">
                <img
                  src={activeBaby.avatarUrl}
                  alt={activeBaby.name}
                  className="w-16 h-16 rounded-full object-cover border-2 border-white/40 shadow-sm group-hover:scale-105 transition-transform"
                  onError={(e) => { (e.currentTarget as HTMLImageElement).src = "/static/img/leo.png"; }}
                />
                <span className="absolute bottom-0 right-0 w-4 h-4 bg-emerald-500 rounded-full border-2 border-white flex items-center justify-center">
                  <Check className="w-2.5 h-2.5 text-white" />
                </span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-primary font-bold text-2xl tracking-tight group-hover:text-primary/80">{activeBaby.name}</h1>
                  <ChevronDown className="w-5 h-5 text-primary group-hover:translate-y-0.5 transition-transform" />
                </div>
                <p className="text-sm font-semibold text-slate-500 mt-0.5">
                  {calculateAgeStr(activeBaby.birthDate) === "0 ngày" ? "Mới sinh" : calculateAgeStr(activeBaby.birthDate)} • {getLatestWeight()}
                </p>
              </div>
            </div>

            <AnimatePresence>
              {showBabyDropdown && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute left-0 top-full mt-3 w-64 bg-white border border-slate-100 rounded-2xl shadow-xl p-2 z-50 text-xs font-bold"
                >
                  <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider px-3 py-1.5">Chuyển hồ sơ em bé</p>
                  {Array.from(new Map(babies.map((b) => [b.name.trim().toLowerCase(), b])).values()).map((b) => {
                    const displayName = !b.name ? "Bé" : /^bé\b/i.test(b.name.trim()) ? b.name.trim() : `Bé ${b.name.trim()}`;
                    return (
                      <button
                        key={b.id}
                        onClick={() => {
                          onSelectBaby?.(b.id);
                          setShowBabyDropdown(false);
                        }}
                        className={`w-full text-left p-2.5 rounded-xl flex items-center justify-between cursor-pointer transition-all ${
                          b.id === activeBaby.id
                            ? "bg-primary/10 text-primary font-black"
                            : "text-slate-600 hover:bg-slate-50 font-medium"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <img
                            src={b.avatarUrl || "/static/img/leo.png"}
                            alt={b.name}
                            className="w-8 h-8 rounded-full object-cover"
                            onError={(e) => { (e.currentTarget as HTMLImageElement).src = "/static/img/leo.png"; }}
                          />
                          <div>
                            <p className="text-xs font-bold">{displayName}</p>
                            <p className="text-[10px] text-slate-400">{b.gender === "Boy" || b.gender === "boy" ? "Bé trai" : "Bé gái"}</p>
                          </div>
                        </div>
                        {b.id === activeBaby.id && <Check className="w-4 h-4 text-primary" />}
                      </button>
                    );
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

            {/* Action buttons */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => setActiveModal("add-entry")}
              className="inline-flex items-center gap-2 bg-primary hover:bg-primary/90 text-white px-6 py-2.5 rounded-full text-sm font-bold transition-all shadow-md shadow-primary/20 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              Thêm ghi chép
            </button>

            {/* Notification Popover Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsNotificationOpen(!isNotificationOpen)}
                className="p-3 bg-white/40 border border-white/20 rounded-full text-slate-500 hover:text-slate-700 transition-all cursor-pointer relative"
                title="Thông báo & Nhắc nhở"
              >
                <Bell className="w-5 h-5" />
                {notifications.some((n) => !n.read) && (
                  <span className="absolute top-2 right-2 w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse border border-white" />
                )}
              </button>

              {isNotificationOpen && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setIsNotificationOpen(false)}
                  />
                  <div className="absolute right-0 mt-2 w-80 bg-white/95 backdrop-blur-xl border border-white/50 rounded-2xl shadow-xl p-4 z-50 animate-in fade-in zoom-in-95 duration-150">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-3">
                    <h4 className="text-xs font-bold text-slate-800 flex items-center gap-2">
                      <Bell className="w-4 h-4 text-[#1c648e]" />
                      Thông báo & Nhắc nhở
                    </h4>
                    <button
                      onClick={handleMarkAllAsRead}
                      className="text-[10px] text-[#1c648e] hover:underline font-semibold cursor-pointer"
                    >
                      Đã đọc tất cả
                    </button>
                  </div>

                  <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
                    {notifications.length === 0 ? (
                      <p className="text-xs text-slate-400 text-center py-4">Không có thông báo mới nào</p>
                    ) : (
                      notifications.map((n) => (
                        <div
                          key={n.id}
                          className={`p-3 rounded-xl border text-xs transition-all ${
                            n.read
                              ? "bg-slate-50/50 border-slate-100 text-slate-500 opacity-75"
                              : "bg-white border-sky-100 text-slate-800 shadow-xs"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-bold text-slate-800 text-[11px] flex items-center gap-1.5">
                              {n.type === "medication" && "💊"}
                              {n.type === "feeding" && "🍼"}
                              {n.type === "safety" && "⚠️"}
                              {n.type === "system" && "📌"}
                              {n.type === "health_check" && "🩺"}
                              {n.title}
                            </span>
                            {!n.read && <span className="w-1.5 h-1.5 bg-sky-500 rounded-full shrink-0" />}
                          </div>
                          <p className="text-[10px] text-slate-600 leading-snug">{n.message}</p>
                          {n.type === "health_check" && (
                            <button
                              type="button"
                              onClick={() => {
                                setNotifications((prev) => prev.filter((item) => item.id !== n.id));
                                setToast({
                                  title: "Sức Khỏe Bé",
                                  message: "✅ Đã xác nhận: Bé đã khỏi bệnh!",
                                  type: "success"
                                });
                                setTimeout(() => setToast(null), 3000);
                              }}
                              className="mt-2 text-[10px] font-bold bg-emerald-600 hover:bg-emerald-700 text-white px-2.5 py-1 rounded-lg transition-all cursor-pointer flex items-center gap-1 shadow-2xs"
                            >
                              <CheckCircle2 className="w-3 h-3" />
                              ✓ Đồng Ý (Bé Đã Khỏi)
                            </button>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </>
            )}
            </div>

            {/* Settings button - Quick Settings Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsSettingsOpen(!isSettingsOpen)}
                className="p-3 bg-white/40 border border-white/20 rounded-full text-slate-500 hover:text-slate-700 transition-all cursor-pointer relative"
                title="Cài đặt nhanh"
              >
                <Settings className="w-5 h-5" />
              </button>

              {isSettingsOpen && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setIsSettingsOpen(false)}
                  />
                  <div className="absolute right-0 mt-2 w-72 bg-white/95 backdrop-blur-xl border border-white/50 rounded-2xl shadow-xl p-4 z-50 animate-in fade-in zoom-in-95 duration-150">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-3">
                    <h4 className="text-xs font-bold text-slate-800 flex items-center gap-2">
                      <Settings className="w-4 h-4 text-[#1c648e]" />
                      Cài đặt nhanh
                    </h4>
                  </div>

                  <div className="space-y-3 text-xs">
                    {/* Sound Alert Toggle */}
                    <div className="flex items-center justify-between py-1">
                      <div className="flex items-center gap-2 text-slate-700 font-medium">
                        {isSoundEnabled ? <Volume2 className="w-4 h-4 text-emerald-500" /> : <VolumeX className="w-4 h-4 text-slate-400" />}
                        <span>Âm thanh nhắc nhở</span>
                      </div>
                      <button
                        onClick={() => setIsSoundEnabled(!isSoundEnabled)}
                        className={`w-10 h-5 flex items-center rounded-full p-0.5 transition-colors cursor-pointer ${
                          isSoundEnabled ? "bg-[#1c648e]" : "bg-slate-300"
                        }`}
                      >
                        <div
                          className={`w-4 h-4 bg-white rounded-full shadow-md transform transition-transform ${
                            isSoundEnabled ? "translate-x-5" : "translate-x-0"
                          }`}
                        />
                      </button>
                    </div>

                    {/* Unit System Selector */}
                    <div className="flex items-center justify-between py-1">
                      <span className="text-slate-700 font-medium">Đơn vị đo lường</span>
                      <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200">
                        <button
                          onClick={() => setUnitSystem("metric")}
                          className={`px-2 py-1 text-[10px] font-bold rounded-md transition-all cursor-pointer ${
                            unitSystem === "metric" ? "bg-white text-[#1c648e] shadow-xs" : "text-slate-500"
                          }`}
                        >
                          Metric (ml/kg)
                        </button>
                        <button
                          onClick={() => setUnitSystem("imperial")}
                          className={`px-2 py-1 text-[10px] font-bold rounded-md transition-all cursor-pointer ${
                            unitSystem === "imperial" ? "bg-white text-[#1c648e] shadow-xs" : "text-slate-500"
                          }`}
                        >
                          Imperial (oz/lbs)
                        </button>
                      </div>
                    </div>

                    <div className="border-t border-slate-100 pt-2.5 mt-2">
                      <button
                        onClick={() => {
                          setIsSettingsOpen(false);
                          onNavigateTab?.("profile");
                        }}
                        className="w-full flex items-center justify-between p-2.5 rounded-xl bg-sky-50/70 hover:bg-sky-100/70 text-[#1c648e] font-bold text-[11px] transition-all cursor-pointer"
                      >
                        <span>Hồ sơ & Phân quyền đầy đủ</span>
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </>
            )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-5 gap-3 sm:gap-4 mt-8 max-w-3xl mx-auto">
          {[
            { label: "Ăn uống", icon: Droplet, color: "text-[#7cb9e8] bg-[#7cb9e8]/10 border-[#7cb9e8]/20", modal: "feed" },
            { label: "Giấc ngủ", icon: Moon, color: "text-[#b19cd9] bg-[#b19cd9]/10 border-[#b19cd9]/20", modal: "sleep" },
            { label: "Uống thuốc", icon: Pill, color: "text-[#b2e2f2] bg-[#b2e2f2]/20 border-[#b2e2f2]/30", modal: "medication" },
            { label: "Tăng trưởng", icon: TrendingUp, color: "text-emerald-600 bg-emerald-50 border-emerald-200", modal: "growth" },
            { label: "Bệnh trạng", icon: Activity, color: "text-rose-600 bg-rose-50 border-rose-200", modal: "health" }
          ].map((action, idx) => {
            const Icon = action.icon;
            return (
              <button
                key={idx}
                onClick={() => {
                  if (action.modal === "health") {
                    onNavigateTab?.("health");
                  } else {
                    setActiveModal(action.modal as any);
                  }
                }}
                className="flex flex-col items-center gap-2 cursor-pointer group"
              >
                <div className={`w-12 h-12 sm:w-14 sm:h-14 rounded-full border flex items-center justify-center transition-all ${action.color} group-hover:scale-105 group-hover:shadow-md`}>
                  <Icon className="w-5 h-5 sm:w-6 sm:h-6" />
                </div>
                <span className="text-[11px] sm:text-xs font-bold text-slate-600 group-hover:text-primary">{action.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. Real-time Status Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          { title: "LẦN BÚ CUỐI", value: lastFeedStr, subtitle: lastFeedDetail.replace("Formula Milk", "Sữa công thức").replace("Breastmilk", "Sữa mẹ"), icon: Droplet, time: "🍼 " + (lastFeed ? lastFeed.time : "01:00 PM"), color: "text-accent-blue bg-accent-blue/10 border-accent-blue/20" },
          { title: "TỔNG GIỜ NGỦ", value: isNapTimerRunning ? "Đang tính..." : "12.5 giờ", subtitle: "Mục tiêu: 14 giờ", icon: Moon, time: "💤 4 giấc hôm nay", color: "text-accent-purple bg-accent-purple/10 border-accent-purple/20" }
        ].map((card, idx) => {
          const Icon = card.icon;
          return (
            <div key={idx} className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-5 flex flex-col justify-between space-y-4 hover:scale-105 transition-transform duration-300">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-medium uppercase tracking-wide text-slate-500">{card.title}</span>
                <div className={`p-1.5 rounded-full ${card.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div>
                <h3 className="text-primary font-semibold text-xl">{card.value}</h3>
                <p className="text-xs font-semibold text-slate-400 mt-0.5">{card.subtitle}</p>
              </div>
              <div className="text-[10px] font-bold text-slate-500 bg-white/40 border border-white/20 rounded-lg px-2 py-1 inline-flex items-center gap-1 self-start">
                {card.time}
              </div>
            </div>
          );
        })}
      </div>

      {/* 3. Columns Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left column: AI chat & Growth chart */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* AI Chat Widget */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 flex flex-col h-[400px]">
            <div className="flex items-center justify-between pb-3 border-b border-white/20 shrink-0">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-primary animate-pulse" />
                <h3 className="text-primary font-bold text-sm tracking-tight flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-primary" />
                  Trợ lý Trò chuyện AI
                </h3>
              </div>
              <span className="text-[10px] font-bold text-slate-400 bg-white/40 border border-white/20 rounded-md px-2 py-0.5">
                Trợ lý đắc lực
              </span>
            </div>

            {/* Chats list area */}
            <div ref={chatContainerRef} className="flex-1 overflow-y-auto py-4 space-y-4 pr-1 text-xs">
              {chats.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 space-y-2">
                  <MessageSquare className="w-8 h-8 text-slate-300" />
                  <p className="text-xs">Hỏi bất cứ điều gì về cữ ăn, giấc ngủ hoặc lịch uống thuốc của {activeBaby.name}.</p>
                </div>
              ) : (
                chats.slice(-6).map((chat) => (
                  <div key={chat.id} className={`flex flex-col ${chat.role === "user" ? "items-end" : "items-start"}`}>
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-2.5 leading-relaxed ${
                        chat.role === "user"
                          ? "bg-primary text-white rounded-br-none"
                          : "bg-white/70 border border-white/40 text-slate-700 rounded-bl-none shadow-xs"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{chat.content}</p>

                      {/* Smart extractions verification inside chat */}
                      {chat.extraction && (
                        <div className="mt-3 p-3 bg-white/80 border border-white/40 rounded-xl space-y-2 shadow-xs text-slate-800">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-[10px] font-bold uppercase text-primary tracking-wide">
                              ✨ Gợi ý từ AI
                            </span>
                            <span className="text-[9px] font-bold text-slate-400">{chat.extraction.time}</span>
                          </div>
                          <div>
                            <p className="text-xs font-bold text-slate-800">{chat.extraction.title.replace("Feeding Log", "Cữ bú/ăn dặm").replace("Medication Log", "Uống thuốc").replace("Solids Feed", "Ăn dặm").replace("Nap Duration", "Thời gian ngủ")}</p>
                            <p className="text-[10px] text-slate-500">{chat.extraction.detail.replace("Formula", "Sữa công thức").replace("Breastmilk", "Sữa mẹ").replace("Start Nap Tracking", "Bắt đầu đo giấc ngủ")}</p>
                          </div>
                          <button
                            onClick={() => onConfirmExtraction(chat.extraction!)}
                            className="w-full inline-flex items-center justify-center gap-1.5 bg-primary/10 hover:bg-primary/20 text-primary py-1.5 rounded-lg text-[10px] font-bold transition-all cursor-pointer"
                          >
                            <Check className="w-3.5 h-3.5" />
                            Lưu vào Cơ sở dữ liệu
                          </button>
                        </div>
                      )}
                    </div>
                    <span className="text-[9px] text-slate-400 font-bold mt-1 px-1">{chat.timestamp}</span>
                  </div>
                ))
              )}
              {isAiLoading && (
                <div className="flex items-center gap-1.5 pl-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              )}
            </div>

            {/* Voice record soundwaves simulation */}
            {isRecording && (
              <div className="pb-3 flex items-center justify-center gap-1 shrink-0 animate-pulse bg-[#7cb9e8]/10 border border-[#7cb9e8]/20 rounded-2xl p-2 mb-2">
                <span className="text-xs font-bold text-primary animate-pulse mr-2 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                  Đang ghi âm giọng nói...
                </span>
                {[1, 2, 3, 4, 5, 4, 3, 2, 1, 2, 3, 4, 3, 2, 1].map((h, i) => (
                  <span
                    key={i}
                    className="w-0.5 bg-primary rounded-full transition-all"
                    style={{
                      height: `${h * 4}px`,
                      animation: "bounce 0.8s infinite alternate",
                      animationDelay: `${i * 50}ms`
                    }}
                  />
                ))}
              </div>
            )}

            {/* Chat Input form */}
            <form onSubmit={handleChatSubmit} className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={handleToggleMic}
                className={`p-3 rounded-full border transition-all cursor-pointer ${
                  isRecording
                    ? "bg-red-50 text-red-600 border-red-200 animate-pulse"
                    : "bg-white/40 border-white/20 text-slate-400 hover:text-slate-600 hover:bg-white/80"
                }`}
              >
                <Mic className="w-4 h-4" />
              </button>
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder={`Hỏi bất cứ điều gì về cách chăm sóc ${activeBaby.name}...`}
                className="flex-1 bg-white/40 focus:bg-white/80 border border-white/20 focus:border-primary/35 focus:outline-hidden rounded-full px-4 py-3 text-xs text-slate-800 transition-all placeholder-slate-400"
              />
              <button
                type="submit"
                disabled={isAiLoading || !chatInput.trim()}
                className="p-3 bg-primary hover:bg-primary/90 disabled:bg-slate-100 text-white disabled:text-slate-300 rounded-full transition-all shadow-md shadow-primary/20 cursor-pointer"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>

          {/* Growth trajectory WHO comparison Chart */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/20 pb-3">
              <div>
                <h3 className="text-primary font-bold text-sm tracking-tight flex items-center gap-1.5">
                  <TrendingUp className="w-4 h-4 text-emerald-500" />
                  Tiến trình Tăng trưởng ({growthMetric === "weight" ? "Cân nặng" : "Chiều cao"})
                </h3>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  Đường trung vị WHO ({growthMetric === "weight" ? "kg" : "cm"}) so với số đo thực tế của {activeBaby.name}
                </p>
              </div>

              <div className="flex items-center gap-2 self-start sm:self-auto">
                {/* Metric Selector Toggle */}
                <div className="flex bg-slate-100/80 p-0.5 rounded-xl border border-slate-200/60">
                  <button
                    onClick={() => setGrowthMetric("weight")}
                    className={`px-2.5 py-1 text-[10px] font-extrabold rounded-lg transition-all cursor-pointer ${
                      growthMetric === "weight"
                        ? "bg-white text-primary shadow-xs"
                        : "text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    Cân nặng (kg)
                  </button>
                  <button
                    onClick={() => setGrowthMetric("height")}
                    className={`px-2.5 py-1 text-[10px] font-extrabold rounded-lg transition-all cursor-pointer ${
                      growthMetric === "height"
                        ? "bg-white text-primary shadow-xs"
                        : "text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    Chiều cao (cm)
                  </button>
                </div>

                <button
                  onClick={() => setActiveModal("growth")}
                  className="inline-flex items-center gap-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-600 border border-emerald-100 rounded-xl px-3 py-1 text-[10px] font-extrabold transition-all cursor-pointer shrink-0"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Thêm chỉ số
                </button>
              </div>
            </div>

            <div className="h-[240px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorBaby" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#1c648e" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#1c648e" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={9} fontWeight="bold" tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={9} fontWeight="bold" tickLine={false} domain={growthMetric === "weight" ? [2, 13] : [45, 85]} />
                  <Tooltip
                    formatter={(value: any) => [`${value} ${growthMetric === "weight" ? "kg" : "cm"}`]}
                    contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0", backgroundColor: "rgba(255, 255, 255, 0.9)" }}
                    labelStyle={{ fontSize: "10px", fontWeight: "bold", color: "#1c648e" }}
                    itemStyle={{ fontSize: "10px", padding: "1px 0" }}
                  />
                  <Legend wrapperStyle={{ fontSize: "10px", fontWeight: "bold", color: "#64748b" }} iconType="circle" />
                  <Area type="monotone" dataKey={activeBaby.name} stroke="#1c648e" strokeWidth={2.5} fillOpacity={1} fill="url(#colorBaby)" activeDot={{ r: 6 }} />
                  <Area type="monotone" dataKey="WHO Median" stroke="#7cb9e8" strokeWidth={1.5} strokeDasharray="3 3" fillOpacity={0} />
                  <Area type="monotone" dataKey="WHO 3rd" stroke="#ef4444" strokeWidth={1} strokeDasharray="4 4" fillOpacity={0} />
                  <Area type="monotone" dataKey="WHO 97th" stroke="#f59e0b" strokeWidth={1} strokeDasharray="4 4" fillOpacity={0} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>

        {/* Right column: AI Insights & Daily timeline */}
        <div className="space-y-6">
          
          {/* AI Cry Detector Card */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-primary font-bold text-sm tracking-tight flex items-center gap-1.5">
                <Mic className="w-4.5 h-4.5 text-rose-500 animate-pulse" />
                Phân tích Tiếng khóc AI
              </h3>
              <span className="text-[9px] font-bold text-rose-600 bg-rose-50 border border-rose-100 rounded-md px-2 py-0.5">
                Real-time AI
              </span>
            </div>

            <div className="flex items-center justify-center gap-4 py-1">
              {/* Mic Icon Button */}
              <button
                onClick={() => handleStartCryAnalysis()}
                disabled={isAnalyzingCry}
                title="Thu âm tiếng khóc qua Micro"
                className="w-12 h-12 rounded-full bg-rose-500 hover:bg-rose-600 disabled:bg-slate-300 text-white flex items-center justify-center transition-all shadow-md cursor-pointer hover:scale-105"
              >
                {isAnalyzingCry ? (
                  <RefreshCw className="w-5 h-5 animate-spin" />
                ) : (
                  <Mic className="w-5 h-5" />
                )}
              </button>

              {/* Upload Icon Button */}
              <button
                onClick={() => cryFileInputRef.current?.click()}
                disabled={isAnalyzingCry}
                title="Tải file ghi âm tiếng khóc (.wav, .mp3)"
                className="w-12 h-12 rounded-full bg-white border border-rose-200 hover:bg-rose-50 text-rose-500 disabled:bg-slate-100 flex items-center justify-center transition-all shadow-xs cursor-pointer hover:scale-105"
              >
                <Upload className="w-5 h-5 text-rose-500" />
              </button>

              <input
                type="file"
                ref={cryFileInputRef}
                accept="audio/*,.wav,.mp3,.m4a,.ogg"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    handleStartCryAnalysis(file);
                    e.target.value = "";
                  }
                }}
              />
            </div>

            {/* Cry Analysis Result Display Card */}
            {cryResult && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 bg-white/80 border border-slate-100 rounded-2xl space-y-3 shadow-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-extrabold text-slate-800">{cryResult.label}</span>
                  <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 border border-emerald-100 rounded-md px-2 py-0.5">
                    Độ tin cậy: {cryResult.confidence}%
                  </span>
                </div>

                <p className="text-xs text-slate-600 font-medium leading-relaxed">
                  {cryResult.advice}
                </p>

                {/* Multi-class Reason Scores Breakdown */}
                {cryResult.reasonScores && Object.keys(cryResult.reasonScores).length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider">Bảng tỷ lệ các khả năng:</span>
                    <div className="space-y-1">
                      {Object.entries(cryResult.reasonScores).slice(0, 4).map(([reason, score]) => {
                        const reasonLabels: Record<string, string> = {
                          hungry: "Đói bú 🍼",
                          tired: "Gắt ngủ 🥱",
                          pain: "Đau/Đầy hơi 😣",
                          burp: "Cần ợ hơi 💨",
                          diaper: "Bẩn tã 💩",
                          discomfort: "Khó chịu 🌡️",
                          lonely: "Cần bế 🫂",
                          scared: "Giật mình 😨"
                        };
                        const pct = Math.round(score * 100);
                        return (
                          <div key={reason} className="flex items-center gap-2 text-[10px]">
                            <span className="w-24 text-slate-600 font-semibold truncate">{reasonLabels[reason] || reason}</span>
                            <div className="flex-1 bg-slate-100 h-1.5 rounded-full overflow-hidden">
                              <div className="bg-sky-500 h-full rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
                            </div>
                            <span className="w-8 text-right text-slate-500 font-bold">{pct}%</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                <div className="p-2.5 bg-sky-50/60 border border-sky-100 rounded-xl flex items-center justify-between text-xs text-sky-800 font-bold">
                  <span className="truncate pr-2">🎵 Âm thanh dỗ: {cryResult.soothingSound.split("/").pop()}</span>
                  <button
                    onClick={() => {
                      try {
                        const audio = new Audio(cryResult.soothingSound);
                        audio.play().catch(() => showToast("error", "Âm thanh", "Không thể phát tệp âm thanh này"));
                      } catch(e) {}
                    }}
                    className="text-[10px] bg-sky-600 hover:bg-sky-700 text-white px-2.5 py-1 rounded-lg transition-all cursor-pointer shrink-0"
                  >
                    Bật nhạc dỗ
                  </button>
                </div>

                {/* Parent Feedback Buttons */}
                <div className="pt-1 flex items-center justify-between text-[10px] text-slate-400 font-bold border-t border-slate-100">
                  <span>AI đoán đúng không?</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleSendCryFeedback(true)}
                      className={`px-2 py-1 rounded-lg border cursor-pointer transition-all ${
                        cryFeedback === "accurate" ? "bg-emerald-500 text-white border-emerald-500" : "bg-white hover:bg-slate-50 text-slate-600"
                      }`}
                    >
                      👍 Đúng
                    </button>
                    <button
                      onClick={() => handleSendCryFeedback(false)}
                      className={`px-2 py-1 rounded-lg border cursor-pointer transition-all ${
                        cryFeedback === "inaccurate" ? "bg-rose-500 text-white border-rose-500" : "bg-white hover:bg-slate-50 text-slate-600"
                      }`}
                    >
                      👎 Chưa chuẩn
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </div>

          {/* AI Insights & Recommendations */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
            <h3 className="text-primary font-bold text-sm tracking-tight flex items-center gap-1.5">
              <Sparkles className="w-4.5 h-4.5 text-primary" />
              Đánh giá từ AI
            </h3>

            <div className="space-y-3.5">
              {/* Insight 1 */}
              <div className="p-4 bg-blue-50/50 border border-blue-100 rounded-2xl space-y-1.5">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-blue-800">Chuyển sang ăn dặm</h4>
                  <span className="text-[9px] font-bold text-blue-500 bg-blue-100 px-2 py-0.5 rounded-md">
                    Dinh dưỡng
                  </span>
                </div>
                <p className="text-[11px] text-blue-700 leading-relaxed">
                  {activeBaby.name} đã được {calculateAgeStr(activeBaby.birthDate) === "0 days" ? "mới sinh" : calculateAgeStr(activeBaby.birthDate).replace("months", "tháng").replace("days", "ngày")} hôm nay! Thời điểm hoàn hảo để bắt đầu làm quen với các món nghiền như bơ hoặc khoai lang nghiền.
                </p>
                <a href="#" className="inline-flex items-center gap-1 text-[10px] font-bold text-blue-600 hover:text-blue-800 transition-colors">
                  Xem hướng dẫn
                  <ArrowRight className="w-3 h-3" />
                </a>
              </div>

              {/* Insight 2 */}
              <div className="p-4 bg-rose-50/50 border border-rose-100 rounded-2xl space-y-1.5">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-rose-800">Nhắc lịch uống thuốc</h4>
                  <span className="text-[9px] font-bold text-rose-500 bg-rose-100 px-2 py-0.5 rounded-md">
                    Nhắc nhở
                  </span>
                </div>
                <p className="text-[11px] text-rose-700 leading-relaxed">
                  Khuyên dùng liều Vitamin D tiếp theo vào khoảng 4:00 chiều (trong 45 phút nữa).
                </p>
                <div className="text-[9px] font-bold text-rose-500 bg-white border border-rose-100 rounded px-2 py-0.5 inline-block">
                  HÔM NAY 4:00 CHIỀU
                </div>
              </div>
            </div>
          </div>

          {/* Daily Timeline */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-white/20 pb-3">
              <h3 className="text-primary font-bold text-sm tracking-tight flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-slate-400" />
                Dòng thời gian hoạt động
              </h3>
              <span className="text-[9px] font-bold text-slate-400 bg-white/40 border border-white/20 rounded-md px-2 py-0.5">
                Hôm nay
              </span>
            </div>

            <div className="relative pl-4 border-l border-slate-100 space-y-5">
              {combinedTimeline.slice(0, 5).map((item, idx) => {
                let dotColor = "bg-[#7cb9e8] ring-[#7cb9e8]/20";
                if (item.type === "medication") dotColor = "bg-[#b2e2f2] ring-[#b2e2f2]/30";
                if (item.type === "diaper") dotColor = "bg-[#fdfd96] ring-[#fdfd96]/30";

                return (
                  <div key={idx} className="relative group">
                    <span className={`absolute -left-[20.5px] top-1 w-2.5 h-2.5 rounded-full ring-4 ${dotColor}`} />
                    
                    <div className="space-y-0.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-700">{item.title.replace("Formula Feed", "Bú sữa công thức").replace("Breast Feed", "Bú sữa mẹ").replace("Solids Feed", "Ăn dặm").replace("Diaper Change", "Thay tã")}</span>
                        <span className="text-[9px] font-bold text-slate-400">{item.time}</span>
                      </div>
                      <p className="text-[10px] text-slate-400 leading-relaxed font-semibold">{item.detail.replace("Formula", "Sữa công thức").replace("Dosage:", "Liều lượng:").replace("Prescribed by:", "Kê đơn bởi:").replace("Self", "Tự cho").replace("Wet Diaper", "Tã ướt").replace("Dirty Diaper", "Tã bẩn").replace("Normal", "Bình thường").replace("Soft", "Mềm")}</p>
                    </div>
                  </div>
                );
              })}

              {combinedTimeline.length === 0 && (
                <div className="text-center text-slate-400 py-6 text-xs">
                  Chưa ghi nhận hoạt động nào hôm nay. Hãy ghi nhanh ở trên!
                </div>
              )}
            </div>
          </div>

        </div>

      </div>

      {/* --- MODALS SECTION --- */}
      <AnimatePresence>
        
        {/* Modal: Quick log with BOTH Voice Input & Manual Category Selection */}
        {activeModal === "add-entry" && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-black text-slate-800 flex items-center gap-1.5">
                  <Plus className="w-4 h-4 text-primary" />
                  Thêm ghi chép mới
                </h3>
                <button
                  onClick={() => {
                    if (isListening) stopListening();
                    setActiveModal("none");
                  }}
                  className="text-xs font-bold text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  Đóng
                </button>
              </div>

              {/* Nhập liệu bằng giọng nói */}
              <div className="p-4 bg-sky-50/70 border border-sky-100/80 rounded-2xl space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-primary flex items-center gap-1.5">
                    <Mic className="w-4 h-4 text-primary" />
                    Nhập liệu bằng giọng nói
                  </span>
                  {isListening && (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-red-500 animate-pulse">
                      <span className="w-2 h-2 rounded-full bg-red-500" />
                      Đang lắng nghe...
                    </span>
                  )}
                </div>

                <div className="flex justify-center py-1">
                  <button
                    type="button"
                    onClick={() => {
                      if (isListening) {
                        stopListening();
                        handleProcessVoiceTranscript(transcript);
                      } else {
                        startListening();
                      }
                    }}
                    className={`p-4 rounded-full border-2 transition-all cursor-pointer shadow-md flex items-center justify-center ${
                      isListening
                        ? "bg-red-500 border-red-400 text-white animate-pulse shadow-red-200"
                        : "bg-white border-sky-200 text-primary hover:bg-sky-100 hover:scale-105"
                    }`}
                    title={isListening ? "Dừng & Phân tích" : "Chạm vào Micro để bắt đầu nói"}
                  >
                    <Mic className={`w-7 h-7 ${isListening ? "animate-bounce" : ""}`} />
                  </button>
                </div>

                {transcript && (
                  <div className="p-2.5 bg-white border border-sky-100 rounded-xl text-[11px] text-slate-700 font-medium leading-snug">
                    <span className="text-[9px] font-bold text-primary block uppercase">Văn bản nhận diện:</span>
                    "{transcript}"
                  </div>
                )}

                {isExtractingVoice && (
                  <div className="text-[10px] font-bold text-primary animate-pulse flex items-center justify-center gap-1">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Gemini AI đang bóc tách dữ liệu...</span>
                  </div>
                )}
              </div>

              {/* Chọn các danh mục sau */}
              <div className="space-y-2">
                <span className="text-[11px] font-bold text-slate-500 block">Chọn các danh mục sau</span>
                <div className="grid grid-cols-2 gap-2.5">
                  {[
                    { label: "🍼 Cữ ăn/uống", modal: "feed" },
                    { label: "💤 Giấc ngủ", modal: "sleep" },
                    { label: "💊 Uống thuốc", modal: "medication" },
                    { label: "📈 Chỉ số WHO", modal: "growth" },
                    { label: "🏥 Bệnh trạng", modal: "health" }
                  ].map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        if (item.modal === "health") {
                          setActiveModal("none");
                          onNavigateTab?.("health");
                        } else {
                          setActiveModal(item.modal as any);
                        }
                      }}
                      className="p-3 bg-slate-50 hover:bg-slate-100/80 border border-slate-100 rounded-2xl text-left text-xs font-bold text-slate-600 hover:text-primary transition-all cursor-pointer"
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        )}

        {/* Modal: Quick log feeding */}
        {activeModal === "feed" && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-black text-slate-800 flex items-center gap-1.5">
                  🍼 Ghi nhận cữ ăn/uống
                </h3>
                <button onClick={() => setActiveModal("add-entry")} className="text-xs font-bold text-primary hover:text-primary/80 cursor-pointer">
                  Quay lại
                </button>
              </div>

              <form onSubmit={handleAddFeedSubmit} className="space-y-4 text-xs font-bold text-slate-600">
                <div className="space-y-1">
                  <label className="block">Loại thức ăn/uống</label>
                  <div className="grid grid-cols-3 gap-2">
                    {["Formula", "Breast", "Solids"].map((type) => {
                      const labels: Record<string, string> = {
                        Formula: "Sữa CT",
                        Breast: "Sữa mẹ",
                        Solids: "Ăn dặm"
                      };
                      return (
                        <button
                          key={type}
                          type="button"
                          onClick={() => setFeedType(type as any)}
                          className={`py-2 rounded-xl border text-center transition-all cursor-pointer ${
                            feedType === type
                              ? "bg-primary border-primary text-white"
                              : "bg-slate-50 border-slate-200 hover:bg-slate-100"
                          }`}
                        >
                          {labels[type]}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {feedType !== "Solids" ? (
                  <div className="space-y-1">
                    <label className="block">Lượng dùng (ml)</label>
                    <input
                      type="number"
                      value={feedAmount}
                      onChange={(e) => setFeedAmount(parseInt(e.target.value))}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/40 focus:outline-hidden"
                    />
                  </div>
                ) : (
                  <div className="space-y-1">
                    <label className="block">Chi tiết món ăn dặm</label>
                    <input
                      type="text"
                      value={feedDetails}
                      onChange={(e) => setFeedDetails(e.target.value)}
                      placeholder="Ví dụ: Khoai lang nghiền, bột bí đỏ"
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/40 focus:outline-hidden"
                    />
                  </div>
                )}

                <button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-white py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer"
                >
                  Lưu nhật ký
                </button>
              </form>
            </motion.div>
          </div>
        )}

        {/* Modal: Quick log sleep */}
        {activeModal === "sleep" && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-black text-slate-800 flex items-center gap-1.5">
                  💤 Theo dõi giấc ngủ
                </h3>
                <button onClick={() => setActiveModal("add-entry")} className="text-xs font-bold text-primary hover:text-primary/80 cursor-pointer">
                  Quay lại
                </button>
              </div>

              <div className="text-center space-y-4 py-4">
                <div className="text-3xl font-mono font-bold text-slate-700">
                  {isNapTimerRunning ? (
                    <span>
                      {Math.floor(napElapsedTime / 3600)}g {Math.floor((napElapsedTime % 3600) / 60)}ph {napElapsedTime % 60}g
                    </span>
                  ) : (
                    "00:00:00"
                  )}
                </div>
                
                <p className="text-xs text-slate-400 font-semibold px-4">
                  {isNapTimerRunning ? `Bấm giờ đang ghi nhận giấc ngủ của ${activeBaby.name} dưới nền.` : `Nhấn Bắt đầu khi ${activeBaby.name} bắt đầu đi vào giấc ngủ.`}
                </p>

                <button
                  onClick={onStartNapTimer}
                  className={`w-full py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer ${
                    isNapTimerRunning ? "bg-red-500 hover:bg-red-600 text-white" : "bg-primary hover:bg-primary/95 text-white"
                  }`}
                >
                  {isNapTimerRunning ? "Dừng & Lưu nhật ký" : "Bắt đầu tính giờ ngủ"}
                </button>
              </div>
            </motion.div>
          </div>
        )}

        {/* Modal: Quick log diaper */}
        {activeModal === "diaper" && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-black text-slate-800 flex items-center gap-1.5">
                  💩 Thay tã cho bé
                </h3>
                <button onClick={() => setActiveModal("add-entry")} className="text-xs font-bold text-primary hover:text-primary/80 cursor-pointer">
                  Quay lại
                </button>
              </div>

              <form onSubmit={handleAddDiaperSubmit} className="space-y-4 text-xs font-bold text-slate-600">
                <div className="space-y-1">
                  <label className="block">Loại tã</label>
                  <div className="grid grid-cols-3 gap-2">
                    {["Wet", "Dirty", "Both"].map((type) => {
                      const labels: Record<string, string> = {
                        Wet: "Ướt",
                        Dirty: "Bẩn",
                        Both: "Cả hai"
                      };
                      return (
                        <button
                          key={type}
                          type="button"
                          onClick={() => setDiaperType(type as any)}
                          className={`py-2 rounded-xl border text-center transition-all cursor-pointer ${
                            diaperType === type
                              ? "bg-primary border-primary text-white"
                              : "bg-slate-50 border-slate-200 hover:bg-slate-100"
                          }`}
                        >
                          {labels[type]}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="block">Trạng thái chất thải</label>
                  <input
                    type="text"
                    value={diaperStatus}
                    onChange={(e) => setDiaperStatus(e.target.value)}
                    placeholder="Ví dụ: Bình thường, phân lỏng, khô"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/40 focus:outline-hidden"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-white py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer"
                >
                  Lưu nhật ký tã
                </button>
              </form>
            </motion.div>
          </div>
        )}

        {/* Modal: Quick log medication */}
        {activeModal === "medication" && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-black text-slate-800 flex items-center gap-1.5">
                  💊 Ghi nhận dùng thuốc
                </h3>
                <button onClick={() => setActiveModal("add-entry")} className="text-xs font-bold text-primary hover:text-primary/80 cursor-pointer">
                  Quay lại
                </button>
              </div>

              <form onSubmit={handleAddMedicationSubmit} className="space-y-4 text-xs font-bold text-slate-600">
                <div className="space-y-1">
                  <label className="block">Tên thuốc</label>
                  <input
                    type="text"
                    required
                    value={medName}
                    onChange={(e) => setMedName(e.target.value)}
                    placeholder="Ví dụ: Hapacol 150mg, Vitamin D"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/40 focus:outline-hidden"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block">Liều lượng</label>
                  <input
                    type="text"
                    required
                    value={medDosage}
                    onChange={(e) => setMedDosage(e.target.value)}
                    placeholder="Ví dụ: 150mg, 2 giọt"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/40 focus:outline-hidden"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block">Người kê đơn</label>
                  <input
                    type="text"
                    value={prescribedBy}
                    onChange={(e) => setPrescribedBy(e.target.value)}
                    placeholder="Ví dụ: Bác sĩ nhi, tự bổ sung"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/40 focus:outline-hidden"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-white py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer"
                >
                  Lưu nhật ký uống thuốc
                </button>
              </form>
            </motion.div>
          </div>
        )}

        {/* Modal: Quick log growth metric */}
        {activeModal === "growth" && (
          <div className="fixed inset-0 bg-[#1c648e]/20 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-sm font-black text-slate-800 flex items-center gap-1.5">
                  📈 Nhập chỉ số tăng trưởng WHO
                </h3>
                <button onClick={() => setActiveModal("add-entry")} className="text-xs font-bold text-primary hover:text-primary/80 cursor-pointer">
                  Quay lại
                </button>
              </div>

              <form onSubmit={handleAddMeasurementSubmit} className="space-y-4 text-xs font-bold text-slate-600">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="block">Tuổi (Tháng)</label>
                    <input
                      type="number"
                      required
                      value={growthAgeMonths}
                      onChange={(e) => setGrowthAgeMonths(parseInt(e.target.value))}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/40"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="block">Cân nặng (kg)</label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      value={growthWeight}
                      onChange={(e) => setGrowthWeight(parseFloat(e.target.value))}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/40"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="block">Chiều cao (cm)</label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={growthHeight}
                    onChange={(e) => setGrowthHeight(parseFloat(e.target.value))}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:border-primary/40"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-white py-2.5 rounded-xl font-bold transition-all shadow-md cursor-pointer"
                >
                  Lưu số đo mới
                </button>
              </form>
            </motion.div>
          </div>
        )}

      </AnimatePresence>

    </div>
  );
}
