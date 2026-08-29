import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";
import {
  MessageSquare,
  Sparkles,
  Mic,
  Send,
  Paperclip,
  Check,
  ChevronDown,
  ChevronRight,
  BookOpen,
  Calendar,
  Activity,
  Plus,
  Play,
  Pause,
  Clock,
  Phone,
  Video,
  Eye,
  Sliders,
  Award,
  Wrench,
  CheckCircle2,
  XCircle,
  Loader2,
  Terminal,
  FileText,
  Trash2,
  Square,
  UploadCloud,
  FileCode,
  Database,
  Layers,
  ShieldCheck,
  AlertCircle,
  FileCheck2
} from "lucide-react";
import { BabyProfile, ChatMessage, SmartExtraction, ToolStep } from "../types";
import { DEFAULT_AVATAR_URL, DEFAULT_SOOTHING_SOUND_URL } from "../data";
import { apiFetch } from "../lib/authClient";


interface AiHubViewProps {
  activeBaby: BabyProfile;
  babies: BabyProfile[];
  onSelectBaby: (id: string) => void;
  chats: ChatMessage[];
  onSendMessage: (text: string) => Promise<void>;
  onStopGeneration?: () => void;
  onConfirmExtraction: (ext: SmartExtraction) => void;
  isAiLoading: boolean;
  onStartNapTimer: () => void;
  isNapTimerRunning: boolean;
  napElapsedTime: number; // seconds
  threads: Array<{ id: string; title: string }>;
  activeThreadId: string;
  onSelectThread: (id: string) => void;
  onCreateThread: () => Promise<void>;
  onDeleteThread?: (id: string) => Promise<void> | void;
}

export default function AiHubView({
  activeBaby,
  babies,
  onSelectBaby,
  chats,
  onSendMessage,
  onStopGeneration,
  onConfirmExtraction,
  isAiLoading,
  onStartNapTimer,
  isNapTimerRunning,
  napElapsedTime,
  threads,
  activeThreadId,
  onSelectThread,
  onCreateThread,
  onDeleteThread
}: AiHubViewProps) {


  const [inputText, setInputText] = useState("");
  const [aiHubTab, setAiHubTab] = useState<"chat" | "knowledge">("chat");
  const [activeThread, setActiveThread] = useState("sitting");
  const [showCitationDropdown, setShowCitationDropdown] = useState(false);
  const [showSwitchBabyDropdown, setShowSwitchBabyDropdown] = useState(false);
  const [openToolTimelines, setOpenToolTimelines] = useState<Record<string, boolean>>({});

  const toggleToolTimeline = (msgId: string) => {
    setOpenToolTimelines((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const formatBabyName = (name: string) => {
    if (!name) return "Bé";
    const trimmed = name.trim();
    return /^bé\b/i.test(trimmed) ? trimmed : `Bé ${trimmed}`;
  };

  const rawList = babies && babies.length > 0 ? babies : activeBaby ? [activeBaby] : [];
  const uniqueBabies = Array.from(
    new Map(rawList.map((b) => [b.id, b])).values()
  );


  // Chat input attachment state
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isUploadingChatFile, setIsUploadingChatFile] = useState(false);

  const handleFileUploadInChat = async (file: File) => {
    setIsUploadingChatFile(true);
    try {
      const formData = new FormData();
      formData.append("audio_file", file);

      const res = await apiFetch(`/api/v1/babies/${activeBaby.id}/cry-prediction`, {
        method: "POST",
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        const pred = data.prediction || "discomfort";
        const soundPlayed = data.sound_played || DEFAULT_SOOTHING_SOUND_URL;
        const promptText = `[Đã đính kèm tệp âm thanh tiếng khóc: ${file.name}] Kết quả chẩn đoán âm thanh từ AI: ${pred} (Độ tin cậy ${Math.round((data.confidence || 0.85) * 100)}%). Âm thanh dỗ: ${soundPlayed}. Hãy tư vấn hướng xử lý phù hợp cho bé ${activeBaby.name}.`;
        await onSendMessage(promptText);
      } else {
        await onSendMessage(`[Đã đính kèm tệp: ${file.name}] Hãy hỗ trợ phân tích dữ liệu tệp này cho bé ${activeBaby.name}.`);
      }
    } catch (err) {
      console.error("Error uploading file in chat:", err);
      await onSendMessage(`[Đã đính kèm tệp: ${file.name}] Hãy hỗ trợ tôi tư vấn về bé ${activeBaby.name}.`);
    } finally {
      setIsUploadingChatFile(false);
    }
  };

  // Knowledge & Automated PDF Ingestion State
  const pdfInputRef = useRef<HTMLInputElement | null>(null);
  const [knowledgeDocs, setKnowledgeDocs] = useState<Array<{
    id: string;
    filename: string;
    file_type: string;
    file_size_kb: number;
    pages_count: number;
    chunks_count: number;
    uploaded_at: string;
    status: string;
  }>>([]);
  const [isIngestingPdf, setIsIngestingPdf] = useState(false);
  const [ingestStep, setIngestStep] = useState(0);
  const [ingestStatusText, setIngestStatusText] = useState("");
  const [ingestError, setIngestError] = useState<string | null>(null);
  const [isDraggingPdf, setIsDraggingPdf] = useState(false);

  const fetchKnowledgeDocs = async () => {
    try {
      const res = await apiFetch("/api/v1/knowledge/documents");
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) setKnowledgeDocs(data);
      }
    } catch (e) {
      console.error("Failed to load knowledge documents:", e);
    }
  };

  useEffect(() => {
    fetchKnowledgeDocs();
  }, []);

  // Automated Ingestion Pipeline Runner
  const handleUploadAndIngestPdf = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf") && !file.name.toLowerCase().endsWith(".md") && !file.name.toLowerCase().endsWith(".txt")) {
      alert("Vui lòng chọn tệp định dạng PDF, Markdown (.md) hoặc Text (.txt)");
      return;
    }

    setIsIngestingPdf(true);
    setIngestError(null);
    setIngestStep(1);
    setIngestStatusText("1. Đang tiếp nhận và kiểm tra tệp tài liệu...");

    try {
      // Step 1: Upload
      const formData = new FormData();
      formData.append("file", file);

      setTimeout(() => {
        setIngestStep(2);
        setIngestStatusText("2. Đang đọc và phân tích nội dung chăm sóc bé...");
      }, 600);

      setTimeout(() => {
        setIngestStep(3);
        setIngestStatusText("3. Đang ghi nhớ vào cơ sở tri thức của Trợ lý AI...");
      }, 1400);

      const res = await apiFetch("/api/v1/knowledge/upload-pdf", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Lỗi khi nạp tài liệu");
      }

      setIngestStep(3);
      setIngestStatusText("3. Hoàn tất! Tài liệu đã được lưu thành công vào trí nhớ AI ✓");
      await fetchKnowledgeDocs();

      setTimeout(() => {
        setIsIngestingPdf(false);
        setIngestStep(0);
        setIngestStatusText("");
      }, 1800);
    } catch (err: any) {
      console.error("Ingestion failed:", err);
      setIngestError(err.message || "Không thể tải lên tệp PDF. Mẹ vui lòng thử lại nhé.");
      setIsIngestingPdf(false);
    }
  };

  const [deletingDoc, setDeletingDoc] = useState<{ id: string; filename: string } | null>(null);
  const [isDeletingDoc, setIsDeletingDoc] = useState(false);

  const handleDeleteKnowledgeDoc = (docId: string, filename: string) => {
    setDeletingDoc({ id: docId, filename });
  };

  const handleConfirmDeleteKnowledgeDoc = async () => {
    if (!deletingDoc) return;
    setIsDeletingDoc(true);
    try {
      const res = await apiFetch(`/api/v1/knowledge/documents/${encodeURIComponent(deletingDoc.id)}`, { method: "DELETE" });
      if (res.ok) {
        await fetchKnowledgeDocs();
      }
    } catch (e) {
      console.error("Failed to delete document:", e);
    } finally {
      setIsDeletingDoc(false);
      setDeletingDoc(null);
    }
  };

  const { isListening, transcript, startListening, stopListening } = useSpeechRecognition({
    silenceTimeoutMs: 1500,
    onSilence: (finalText) => {
      if (finalText && finalText.trim()) {
        setInputText("");
        onSendMessage(finalText.trim());
      }
    }
  });

  useEffect(() => {
    if (transcript) {
      setInputText(transcript);
    }
  }, [transcript]);


  // Voice Memo Simulation State
  const [isVoicePlaying, setIsVoicePlaying] = useState(false);
  const [voiceProgress, setVoiceProgress] = useState(0);
  const voiceIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chats, isAiLoading]);

  // Voice memo simulation play logic
  const handlePlayVoice = () => {
    if (isVoicePlaying) {
      if (voiceIntervalRef.current) clearInterval(voiceIntervalRef.current);
      setIsVoicePlaying(false);
    } else {
      setIsVoicePlaying(true);
      voiceIntervalRef.current = setInterval(() => {
        setVoiceProgress((prev) => {
          if (prev >= 100) {
            clearInterval(voiceIntervalRef.current!);
            setIsVoicePlaying(false);
            return 0;
          }
          return prev + 5;
        });
      }, 300);
    }
  };

  useEffect(() => {
    return () => {
      if (voiceIntervalRef.current) clearInterval(voiceIntervalRef.current);
    };
  }, []);

  const handleSend = () => {
    if (!inputText.trim() || isAiLoading) return;
    onSendMessage(inputText);
    setInputText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Format Nap stopwatch time
  const formatStopwatch = (totalSeconds: number) => {
    const hrs = Math.floor(totalSeconds / 3600);
    const mins = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    return `${String(hrs).padStart(2, "0")}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  return (
    <div className="flex h-[calc(100vh-100px)] overflow-hidden -m-gutter font-sans" id="ai-hub-view">

      {/* 1. Cột Trái (22%): Lịch sử hội thoại & Điều hướng Chế độ */}
      <div className="w-[23%] bg-white/50 border-r border-slate-200/80 flex flex-col p-4 space-y-4 select-none shrink-0 h-full">
        {/* Workspace Mode Switcher */}
        <div className="bg-slate-100/90 p-1 rounded-2xl flex items-center gap-1">
          <button
            type="button"
            onClick={() => setAiHubTab("chat")}
            className={`flex-1 py-2 px-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
              aiHubTab === "chat"
                ? "bg-white text-[#1c648e] shadow-xs"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Trò chuyện AI</span>
          </button>
          <button
            type="button"
            onClick={() => setAiHubTab("knowledge")}
            className={`flex-1 py-2 px-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
              aiHubTab === "knowledge"
                ? "bg-white text-[#1c648e] shadow-xs"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>Tri thức RAG</span>
            <span className="text-[9px] bg-[#1c648e]/10 text-[#1c648e] px-1.5 py-0.2 rounded-full font-black">
              {knowledgeDocs.length}
            </span>
          </button>
        </div>

        {/* MODE 1: CHAT THREADS LIST */}
        {aiHubTab === "chat" ? (
          <>
            {/* New Chat Button */}
            <button
              onClick={onCreateThread}
              className="w-full bg-[#1c648e] hover:bg-[#154c6d] text-white py-2.5 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition-all cursor-pointer shadow-xs"
            >
              <Plus className="w-4 h-4" />
              Cuộc trò chuyện mới
            </button>

            {/* Recent Chats Thread List */}
            <div className="flex-1 overflow-y-auto space-y-1">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-2.5 mb-2">Cuộc trò chuyện gần đây</p>

              {threads.length === 0 ? (
                <p className="text-[11px] text-slate-400 text-center py-6">Chưa có cuộc trò chuyện nào</p>
              ) : (
                threads.map((thread) => (
                  <div
                    key={thread.id}
                    onClick={() => onSelectThread(thread.id)}
                    className={`w-full group text-left p-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-between gap-2 cursor-pointer ${activeThreadId === thread.id
                        ? "bg-[#e0f2fe]/70 text-[#1c648e]"
                        : "text-slate-500 hover:bg-white/60"
                      }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0 flex-1">
                      <MessageSquare className="w-4 h-4 shrink-0 text-[#1c648e]" />
                      <span className="truncate">{thread.title}</span>
                    </div>
                    {onDeleteThread && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm(`Bạn có chắc muốn xóa cuộc trò chuyện "${thread.title}"?`)) {
                            onDeleteThread(thread.id);
                          }
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 hover:bg-rose-100/80 rounded-lg text-slate-400 hover:text-rose-600 transition-all cursor-pointer shrink-0"
                        title="Xóa cuộc trò chuyện này"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          </>
        ) : (
          /* MODE 2: KNOWLEDGE SUMMARY PANEL - DÀNH CHO PHỤ HUYNH */
          <div className="flex-1 overflow-y-auto space-y-3.5">
            <div className="bg-white/80 p-4 rounded-2xl border border-slate-200/80 space-y-2">
              <span className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider block">
                Tủ Sách Y Khoa Của Bé
              </span>
              <div className="bg-[#e0f2fe]/60 p-3 rounded-2xl text-center">
                <span className="text-xl font-black text-[#1c648e] block">{knowledgeDocs.length}</span>
                <span className="text-[10px] font-bold text-slate-600">Tài liệu đã lưu</span>
              </div>
              <p className="text-[10px] text-slate-500 leading-relaxed font-normal pt-1">
                Các sổ khám và tài liệu y khoa mẹ tải lên sẽ giúp Trợ lý AI hiểu rõ hơn tình trạng sức khỏe của bé để tư vấn phù hợp nhất.
              </p>
            </div>

            <div className="bg-white/80 p-3.5 rounded-2xl border border-slate-200/80 space-y-2 text-xs">
              <span className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider block">
                Gợi ý tài liệu nên lưu
              </span>
              <ul className="space-y-2 text-[10.5px] text-slate-600">
                <li className="flex items-start gap-1.5 font-normal">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                  <span>Sổ khám bệnh định kỳ của bé</span>
                </li>
                <li className="flex items-start gap-1.5 font-normal">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                  <span>Đơn thuốc & phác đồ bác sĩ kê</span>
                </li>
                <li className="flex items-start gap-1.5 font-normal">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                  <span>Sổ tay ăn dặm & dinh dưỡng WHO</span>
                </li>
              </ul>
            </div>
          </div>
        )}

        {/* User Mini-Profile panel */}
        <div className="relative pt-2 border-t border-slate-200/60">
          <button
            onClick={() => setShowSwitchBabyDropdown(!showSwitchBabyDropdown)}
            className="w-full p-2.5 bg-white/80 hover:bg-white border border-slate-200/80 rounded-2xl flex items-center justify-between gap-2 cursor-pointer transition-all shadow-xs"
          >
            <div className="flex items-center gap-2.5">
              <img
                src={activeBaby.avatarUrl || DEFAULT_AVATAR_URL}
                alt={activeBaby.name}
                className="w-8 h-8 rounded-full object-cover border border-white shrink-0"
                onError={(e) => { (e.currentTarget as HTMLImageElement).src = DEFAULT_AVATAR_URL; }}
              />
              <div className="text-left">
                <p className="text-xs font-black text-slate-800">{formatBabyName(activeBaby.name)}</p>
                <p className="text-[9px] text-slate-400 font-bold">Đang chọn</p>
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          <AnimatePresence>
            {showSwitchBabyDropdown && (
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 5 }}
                className="absolute bottom-full left-0 mb-2 w-full bg-white border border-slate-100 rounded-2xl shadow-xl p-1.5 z-50 text-xs font-bold"
              >
                <p className="text-[9px] font-extrabold text-slate-400 uppercase tracking-wider px-2 py-1">Chọn hồ sơ bé</p>
                {uniqueBabies.map((b) => (
                  <button
                    key={b.id}
                    onClick={() => {
                      onSelectBaby(b.id);
                      setShowSwitchBabyDropdown(false);
                    }}
                    className={`w-full text-left p-2 rounded-xl flex items-center justify-between cursor-pointer transition-colors ${b.id === activeBaby.id
                        ? "bg-[#e0f2fe]/70 text-[#1c648e] font-black"
                        : "text-slate-600 hover:bg-slate-50 font-medium"
                      }`}
                  >
                    <div className="flex items-center gap-2">
                      <img
                        src={b.avatarUrl || DEFAULT_AVATAR_URL}
                        alt={b.name}
                        className="w-6 h-6 rounded-full object-cover"
                        onError={(e) => { (e.currentTarget as HTMLImageElement).src = DEFAULT_AVATAR_URL; }}
                      />
                      <span>{formatBabyName(b.name)}</span>
                    </div>
                    {b.id === activeBaby.id && <Check className="w-3.5 h-3.5 text-[#1c648e]" />}
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* 2. KHUNG NỘI DUNG CHÍNH (77% CHIỀU RỘNG): PHÂN TÁCH GIỮA CHAT VÀ NẠP TRI THỨC */}
      {aiHubTab === "chat" ? (
        /* ==================================================================== */
        /* SUB-VIEW 1: CỬA SỔ CHAT TRỢ LÝ AI RỘNG RÃI & HIỆN ĐẠI                */
        /* ==================================================================== */
        <div className="flex-1 flex flex-col bg-[#f8fafc] relative h-full">
          {/* Header Chat */}
          {(() => {
            const currentThread = threads.find((t) => t.id === activeThreadId);
            return (
              <div className="p-4 border-b border-slate-200/70 flex items-center justify-between bg-white/80 backdrop-blur-md">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-sm font-black text-slate-800">{currentThread?.title || "Trò chuyện với trợ lý AI"}</h2>
                    <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-[#1c648e]/10 text-[#1c648e]">
                      {formatBabyName(activeBaby.name)}
                    </span>
                  </div>

                  <p className="text-[10px] text-slate-400 font-medium flex items-center gap-1.5 mt-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block animate-pulse" />
                    Trợ lý AI Nhi khoa sẵn sàng — Đã nạp {knowledgeDocs.length} tài liệu RAG
                  </p>
                </div>

                <div className="flex items-center gap-2.5">
                  <button
                    type="button"
                    onClick={() => setAiHubTab("knowledge")}
                    className="text-xs font-bold text-[#1c648e] bg-[#e0f2fe]/80 hover:bg-[#e0f2fe] px-3 py-1.5 rounded-xl transition-all flex items-center gap-1.5 cursor-pointer shadow-2xs"
                  >
                    <UploadCloud className="w-3.5 h-3.5" />
                    <span>Nạp PDF tri thức ({knowledgeDocs.length})</span>
                  </button>
                </div>
              </div>
            );
          })()}

          {/* Messages List Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-5 text-xs leading-relaxed max-w-5xl w-full mx-auto">

            {/* Daily Baby Briefing Capsule */}
            <div className="bg-gradient-to-r from-[#e0f2fe]/90 to-sky-50 border border-[#1c648e]/20 p-4 rounded-3xl space-y-2 shadow-2xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-black text-[#1c648e] flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-[#1c648e]" />
                  Tóm Tắt Tình Trạng Bé Hôm Nay (AI Daily Briefing)
                </span>
                <span className="text-[10px] font-extrabold bg-white/90 text-slate-700 px-2.5 py-0.5 rounded-full border border-slate-200/80">
                  {activeBaby.name} • {String(activeBaby.gender).toLowerCase().includes("g") || String(activeBaby.gender).toLowerCase().includes("f") ? "Bé gái" : "Bé trai"}
                </span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed font-normal">
                Chào phụ huynh bé <strong>{activeBaby.name}</strong>! Trợ lý AI đã nạp hồ sơ của bé, các dị ứng liên quan và kết nối với cơ sở tri thức y khoa. Bạn có thể hỏi bất kỳ câu hỏi nào về sức khỏe, dinh dưỡng ăn dặm hoặc phân tích âm thanh tiếng khóc.
              </p>

              {/* Quick Prompt Chips */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {[
                  `🥣 Gợi ý thực đơn ăn dặm hôm nay cho bé ${activeBaby.name}`,
                  `💊 Hôm nay bé có những cữ thuốc nào cần uống?`,
                  `📈 Đánh giá cân nặng & chiều cao theo chuẩn WHO`,
                  `🌡️ Hướng dẫn xử lý khi bé bị sốt mọc răng`
                ].map((prompt, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setInputText(prompt);
                      onSendMessage(prompt);
                    }}
                    className="text-[11px] font-medium bg-white hover:bg-[#1c648e] text-slate-700 hover:text-white border border-slate-200/90 px-3 py-1.5 rounded-xl transition-all cursor-pointer shadow-2xs"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>

            {chats.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-slate-400 space-y-3">
                <div className="w-12 h-12 rounded-full bg-[#1c648e]/10 text-[#1c648e] flex items-center justify-center">
                  <Sparkles className="w-6 h-6" />
                </div>
                <p className="text-xs font-bold text-slate-600">Bắt đầu trò chuyện với Trợ lý AI</p>
                <p className="text-[11px] text-slate-400 text-center max-w-sm leading-relaxed">
                  Nhập câu hỏi bằng văn bản, bấm micro để nói tiếng Việt hoặc gửi ghi âm tiếng khóc để được tư vấn!
                </p>
              </div>
            ) : (
              chats.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex items-start gap-3 max-w-[90%] ${msg.role === "user" ? "ml-auto justify-end" : "mr-auto"
                    }`}
                >
                  {msg.role === "assistant" && (
                    <div className="w-8 h-8 rounded-full bg-[#1c648e]/10 text-[#1c648e] flex items-center justify-center shrink-0 mt-0.5">
                      <Sparkles className="w-4.5 h-4.5" />
                    </div>
                  )}

                  <div
                    className={`rounded-3xl p-4 shadow-xs ${msg.role === "user"
                        ? "bg-[#1c648e] text-white rounded-tr-xs"
                        : "bg-white border border-slate-200/80 text-slate-700 rounded-tl-xs"
                      }`}
                  >
                    {msg.role === "assistant" ? (
                      <div>
                        {/* Live Progress Badge khi đang nạp context & gọi tool */}
                        {msg.activeStepName && !msg.content && (
                          <div className="flex items-center gap-2 text-xs font-bold text-[#1c648e] bg-[#e0f2fe]/80 border border-[#1c648e]/20 px-3 py-2 rounded-2xl animate-pulse mb-2 shadow-2xs">
                            <Loader2 className="w-4 h-4 animate-spin text-[#1c648e]" />
                            <span>{msg.activeStepName}</span>
                          </div>
                        )}

                        <div className="prose prose-sm max-w-none text-slate-700 leading-relaxed [&_p]:mb-2 [&_p:last-child]:mb-0 [&_ul]:list-disc [&_ul]:pl-4 [&_ol]:list-decimal [&_ol]:pl-4 [&_li]:mb-1 [&_strong]:font-semibold [&_strong]:text-slate-900 [&_code]:bg-slate-100 [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_pre]:bg-slate-800 [&_pre]:text-slate-100 [&_pre]:p-3 [&_pre]:rounded-lg [&_pre]:overflow-x-auto">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                          {isAiLoading && msg.content && (
                            <span className="inline-block w-2 h-4 ml-1 bg-[#1c648e] animate-pulse rounded-xs align-middle" />
                          )}
                        </div>

                        {/* Mục "Đã làm gì" (Tool Steps Timeline Accordion) */}
                        {((msg.toolSteps && msg.toolSteps.length > 0) || (msg.tool_steps && msg.tool_steps.length > 0)) && (
                          <div className="mt-3 pt-2.5 border-t border-slate-100/80">
                            <button
                              onClick={() => toggleToolTimeline(msg.id)}
                              className="flex items-center gap-1.5 text-[11px] font-bold text-[#1c648e] hover:text-[#154c6d] bg-[#e0f2fe]/70 hover:bg-[#e0f2fe] px-3 py-1.5 rounded-xl transition-all cursor-pointer select-none shadow-2xs"
                            >
                              <Wrench className="w-3.5 h-3.5" />
                              <span>Đã làm gì ({(msg.toolSteps || msg.tool_steps || []).length} bước)</span>
                              {openToolTimelines[msg.id] ? (
                                <ChevronDown className="w-3.5 h-3.5 ml-0.5" />
                              ) : (
                                <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                              )}
                            </button>

                            <AnimatePresence>
                              {openToolTimelines[msg.id] && (
                                <motion.div
                                  initial={{ opacity: 0, height: 0 }}
                                  animate={{ opacity: 1, height: "auto" }}
                                  exit={{ opacity: 0, height: 0 }}
                                  className="mt-2.5 p-3 bg-slate-50/90 border border-slate-200/80 rounded-2xl space-y-2.5 text-[10px] overflow-hidden"
                                >
                                  <div className="flex items-center justify-between border-b border-slate-200/60 pb-1.5">
                                    <span className="font-extrabold text-slate-500 uppercase tracking-wider flex items-center gap-1 text-[9px]">
                                      <Clock className="w-3 h-3 text-[#1c648e]" />
                                      Tiến trình thực thi tác vụ Agent
                                    </span>
                                    <span className="text-[9px] text-slate-400 font-semibold">Chỉ hiển thị các lượt gọi tool thực tế</span>
                                  </div>

                                  {(msg.toolSteps || msg.tool_steps || []).map((step: ToolStep, idx: number) => (
                                    <div key={step.id || idx} className="bg-white p-3 rounded-xl border border-slate-200/70 shadow-2xs space-y-1.5">
                                      <div className="flex items-center justify-between font-bold">
                                        <div className="flex items-center gap-1.5 text-slate-800">
                                          <span className="w-4.5 h-4.5 rounded-full bg-[#1c648e]/10 text-[#1c648e] flex items-center justify-center text-[9px] font-black shrink-0">
                                            {idx + 1}
                                          </span>
                                          <span className="text-slate-800 text-xs font-black">{step.display_name || step.tool_name}</span>
                                        </div>

                                        <span className={`px-2 py-0.5 rounded-full text-[9px] font-extrabold flex items-center gap-1 ${step.status === "completed"
                                            ? "bg-emerald-100 text-emerald-700"
                                            : step.status === "failed"
                                              ? "bg-rose-100 text-rose-700"
                                              : "bg-amber-100 text-amber-700 animate-pulse"
                                          }`}>
                                          {step.status === "completed" ? (
                                            <CheckCircle2 className="w-3 h-3" />
                                          ) : step.status === "failed" ? (
                                            <XCircle className="w-3 h-3" />
                                          ) : (
                                            <Loader2 className="w-3 h-3 animate-spin" />
                                          )}
                                          {step.status === "completed" ? "Hoàn thành" : step.status === "failed" ? "Lỗi" : "Đang chạy"}
                                        </span>
                                      </div>

                                      {step.args && Object.keys(step.args).length > 0 && (
                                        <div className="text-slate-500 font-mono text-[9px] bg-slate-100/80 p-2 rounded-lg border border-slate-200/50 break-all">
                                          <span className="font-sans font-bold text-slate-600 mr-1">Tham số:</span>
                                          {JSON.stringify(step.args)}
                                        </div>
                                      )}

                                      {step.result_summary && (
                                        <p className="text-slate-600 font-medium text-[10.5px]">
                                          <span className="font-bold text-slate-700">Kết quả:</span> {step.result_summary}
                                        </p>
                                      )}

                                      <div className="flex items-center justify-between text-[8.5px] text-slate-400 font-medium pt-0.5">
                                        <span>Bắt đầu: {step.start_time ? new Date(step.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : 'Vừa xong'}</span>
                                        {step.duration_ms !== undefined && step.duration_ms !== null && (
                                          <span className="font-bold text-[#1c648e]">Thực thi: {(step.duration_ms / 1000).toFixed(2)}s</span>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                  </div>

                  {msg.role === "user" && (
                    <div className="w-8 h-8 rounded-full bg-sky-200 overflow-hidden flex items-center justify-center shrink-0 border border-white mt-1">
                      <span className="text-[10px] font-black text-sky-700">M</span>
                    </div>
                  )}
                </div>
              ))
            )}

            {/* Live Progress Card when Agent is Thinking */}
            {isAiLoading && (
              <div className="flex items-start gap-3 mr-auto max-w-[85%]">
                <div className="w-8 h-8 rounded-full bg-[#1c648e]/10 text-[#1c648e] flex items-center justify-center shrink-0 animate-pulse">
                  <Sparkles className="w-4.5 h-4.5" />
                </div>

                <div className="bg-white border border-slate-200/90 shadow-lg text-slate-700 rounded-3xl rounded-tl-xs p-4 space-y-3 min-w-[320px]">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 text-[#1c648e] animate-spin" />
                      <span className="text-xs font-black text-slate-800">Trợ lý AI đang suy nghĩ...</span>
                    </div>
                    <span className="text-[9px] font-black px-2.5 py-0.5 rounded-full bg-[#1c648e]/10 text-[#1c648e] animate-pulse">
                      Running
                    </span>
                  </div>

                  <div className="space-y-2 text-[10px]">
                    <p className="font-extrabold text-slate-400 uppercase tracking-wider text-[9px] flex items-center gap-1">
                      <Activity className="w-3.5 h-3.5 text-[#1c648e]" />
                      Tiến trình gọi tool thực tế
                    </p>

                    <div className="bg-slate-50 border border-slate-200/70 rounded-2xl p-3 space-y-1.5 shadow-2xs">
                      <div className="flex items-center justify-between font-bold text-slate-800">
                        <div className="flex items-center gap-1.5">
                          <Wrench className="w-3.5 h-3.5 text-[#1c648e]" />
                          <span>Tra cứu hồ sơ & tài liệu nhi khoa</span>
                        </div>
                        <span className="px-2 py-0.5 rounded-full text-[8.5px] font-black bg-amber-100 text-amber-700 flex items-center gap-1">
                          <Loader2 className="w-3 h-3 animate-spin" />
                          Running
                        </span>
                      </div>
                      <p className="text-[9px] text-slate-500 font-medium">
                        Tham số: <span className="font-mono bg-slate-200/60 px-1 py-0.5 rounded text-slate-700">baby_id: "{activeBaby.name}"</span>
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="p-4 bg-white/80 border-t border-slate-200/70 select-none">
            <div className="max-w-4xl mx-auto flex items-center gap-2.5 bg-slate-50 border border-slate-200/90 rounded-full px-4 py-2 shadow-2xs">
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploadingChatFile || isAiLoading}
                className="p-1.5 text-slate-400 hover:text-[#1c648e] transition-colors cursor-pointer disabled:opacity-50"
                title="Đính kèm tệp âm thanh / ghi âm tiếng khóc"
              >
                <Paperclip className="w-4 h-4" />
              </button>
              <input
                type="file"
                ref={fileInputRef}
                accept="audio/*,.wav,.mp3,.m4a,.ogg,.pdf,.png,.jpg"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    handleFileUploadInChat(file);
                    e.target.value = "";
                  }
                }}
              />
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={`Hỏi trợ lý AI về chăm sóc bé ${activeBaby.name}...`}
                className="flex-1 bg-transparent border-none outline-hidden text-xs text-slate-700 placeholder-slate-400 font-medium"
              />
              <button
                onClick={() => {
                  if (isListening) {
                    stopListening();
                  } else {
                    startListening();
                  }
                }}
                className={`p-1.5 rounded-full transition-all cursor-pointer ${isListening ? "bg-red-500 text-white animate-pulse" : "text-slate-400 hover:text-[#1c648e]"
                  }`}
                title={isListening ? "Đang lắng nghe... Bấm để dừng" : "Nói tiếng Việt để nhập tin nhắn"}
              >
                <Mic className="w-4 h-4" />
              </button>
              <button
                onClick={isAiLoading ? onStopGeneration : handleSend}
                disabled={!isAiLoading && !inputText.trim()}
                className={`w-8 h-8 rounded-full flex items-center justify-center transition-all cursor-pointer shadow-xs ${
                  isAiLoading
                    ? "bg-rose-500 hover:bg-rose-600 text-white animate-pulse"
                    : "bg-[#1c648e] hover:bg-[#154c6d] text-white disabled:bg-slate-200 disabled:text-slate-400"
                }`}
                title={isAiLoading ? "Dừng phản hồi" : "Gửi tin nhắn"}
              >
                {isAiLoading ? (
                  <Square className="w-3.5 h-3.5 fill-white" />
                ) : (
                  <Send className="w-3.5 h-3.5 fill-white" />
                )}
              </button>
            </div>

            <div className="text-center mt-2">
              <span className="text-[8px] font-bold text-slate-400 tracking-widest uppercase">
                Dữ liệu y tế của bé được bảo mật & hỗ trợ bởi mô hình Gemini Flash
              </span>
            </div>
          </div>
        </div>
      ) : (
        /* ==================================================================== */
        /* SUB-VIEW 2: TỦ SÁCH Y KHOA & SỔ KHÁM CỦA BÉ (TỐI GIẢN CHO PHỤ HUYNH)  */
        /* ==================================================================== */
        <div className="flex-1 flex flex-col bg-[#f8fafc] overflow-y-auto p-6 space-y-6">
          {/* Header */}
          <div className="bg-white border border-slate-200/80 p-5 rounded-3xl shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-[#1c648e]/10 text-[#1c648e] rounded-2xl shrink-0">
                <BookOpen className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-base font-black text-slate-800 tracking-tight">
                  Tủ Sách Y Khoa & Sổ Khám Của Bé
                </h1>
                <p className="text-xs text-slate-500 mt-0.5">
                  Lưu trữ sổ khám, đơn thuốc và tài liệu ăn dặm để Trợ lý AI tư vấn sát thực tế nhất cho bé {activeBaby.name}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setAiHubTab("chat")}
              className="inline-flex items-center gap-1.5 bg-[#1c648e] hover:bg-[#154c6d] text-white text-xs font-bold px-4 py-2 rounded-xl transition-all shadow-2xs cursor-pointer self-start sm:self-auto"
            >
              <MessageSquare className="w-4 h-4" />
              Quay lại phòng Chat
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* LEFT: DROPZONE & 3 GIAI ĐOẠN ĐƠN GIẢN (5 / 12) */}
            <div className="lg:col-span-5 space-y-4">
              <div className="bg-white border border-slate-200/80 rounded-3xl p-5 shadow-2xs space-y-3">
                <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <UploadCloud className="w-4 h-4 text-[#1c648e]" />
                  Thêm Tài Liệu Mới
                </h3>

                <div
                  onDragOver={(e) => {
                    e.preventDefault();
                    setIsDraggingPdf(true);
                  }}
                  onDragLeave={() => setIsDraggingPdf(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setIsDraggingPdf(false);
                    const file = e.dataTransfer.files?.[0];
                    if (file) handleUploadAndIngestPdf(file);
                  }}
                  onClick={() => pdfInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-3xl p-6 text-center transition-all cursor-pointer space-y-3 ${
                    isDraggingPdf
                      ? "border-[#1c648e] bg-[#e0f2fe]/60 scale-102"
                      : "border-slate-200 hover:border-[#1c648e] bg-slate-50 hover:bg-white"
                  }`}
                >
                  <input
                    type="file"
                    ref={pdfInputRef}
                    accept=".pdf,.md,.txt"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        handleUploadAndIngestPdf(file);
                        e.target.value = "";
                      }
                    }}
                  />

                  <div className="w-11 h-11 mx-auto rounded-2xl bg-[#1c648e]/10 text-[#1c648e] flex items-center justify-center">
                    <UploadCloud className="w-5 h-5" />
                  </div>

                  <div>
                    <p className="text-xs font-bold text-slate-800">
                      Kéo thả sổ khám hoặc file PDF vào đây
                    </p>
                    <p className="text-[11px] text-slate-400 font-medium mt-0.5">
                      Hỗ trợ tệp PDF, tài liệu văn bản (.pdf, .md, .txt)
                    </p>
                  </div>

                  <button
                    type="button"
                    disabled={isIngestingPdf}
                    className="text-xs font-bold bg-[#1c648e] hover:bg-[#154c6d] text-white px-4 py-2 rounded-xl transition-all shadow-2xs inline-flex items-center gap-1 cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Chọn tệp từ máy
                  </button>
                </div>
              </div>

              {/* Tiến trình nạp tài liệu dịu nhẹ */}
              {isIngestingPdf && (
                <div className="bg-[#e0f2fe]/80 border border-[#1c648e]/20 rounded-3xl p-4 space-y-2.5 shadow-2xs animate-pulse">
                  <div className="flex items-center justify-between text-xs font-bold text-[#1c648e]">
                    <span className="flex items-center gap-1.5">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Đang xử lý tài liệu cho bé...
                    </span>
                    <span className="text-[10px] bg-[#1c648e] text-white px-2 py-0.2 rounded-full font-bold">
                      Bước {ingestStep}/3
                    </span>
                  </div>

                  <p className="text-[11px] font-semibold text-slate-700">
                    {ingestStatusText}
                  </p>

                  <div className="w-full bg-white/80 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-[#1c648e] h-full transition-all duration-300 rounded-full"
                      style={{ width: `${(ingestStep / 3) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {ingestError && (
                <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 text-xs font-medium flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                  <span>{ingestError}</span>
                </div>
              )}

              {/* Lời nhắc an toàn */}
              <div className="bg-white border border-slate-200/80 rounded-3xl p-4 space-y-1.5 shadow-2xs text-xs text-slate-600">
                <div className="flex items-center gap-1.5 font-bold text-slate-800">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>Bảo mật dữ liệu gia đình</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed font-normal">
                  Mọi tài liệu y khoa bạn tải lên chỉ được sử dụng để hỗ trợ trả lời riêng cho bé {activeBaby.name}, không chia sẻ ra ngoài.
                </p>
              </div>
            </div>

            {/* RIGHT: DANH SÁCH TÀI LIỆU ĐÃ LƯU (7 / 12) */}
            <div className="lg:col-span-7 space-y-4">
              <div className="bg-white border border-slate-200/80 rounded-3xl p-5 shadow-2xs space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div>
                    <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                      <FileCheck2 className="w-4 h-4 text-emerald-600" />
                      Tài Liệu Đã Lưu ({knowledgeDocs.length})
                    </h3>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Trợ lý AI đã ghi nhớ các tài liệu này để sẵn sàng tư vấn
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={fetchKnowledgeDocs}
                    className="text-xs font-bold text-[#1c648e] hover:underline cursor-pointer"
                  >
                    Làm mới
                  </button>
                </div>

                <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1">
                  {knowledgeDocs.length === 0 ? (
                    <div className="text-center py-10 bg-slate-50 rounded-2xl border border-slate-100 p-6 space-y-2">
                      <FileText className="w-7 h-7 text-slate-300 mx-auto" />
                      <p className="text-xs font-bold text-slate-600">Chưa có tài liệu nào trong tủ sách</p>
                      <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
                        Mẹ có thể kéo thả sổ khám hoặc sách dinh dưỡng vào ô bên trái để lưu trữ nhé!
                      </p>
                    </div>
                  ) : (
                    knowledgeDocs.map((doc) => (
                      <div
                        key={doc.id}
                        className="p-3.5 bg-slate-50/70 hover:bg-white border border-slate-200/80 rounded-2xl shadow-2xs hover:border-[#1c648e]/30 transition-all flex items-start justify-between gap-3"
                      >
                        <div className="space-y-1.5 min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <FileCheck2 className="w-4 h-4 text-emerald-600 shrink-0" />
                            <p className="text-xs font-bold text-slate-900 truncate" title={doc.filename}>
                              {doc.filename}
                            </p>
                          </div>

                          <div className="flex flex-wrap items-center gap-2 text-[10px] text-slate-500 font-medium">
                            <span className="bg-white border border-slate-200 px-2 py-0.5 rounded-md font-semibold text-slate-700">
                              {doc.file_size_kb} KB
                            </span>
                            <span>•</span>
                            <span>{doc.pages_count} trang</span>
                          </div>

                          <div className="flex items-center gap-2 pt-0.5">
                            <span className="text-[9px] font-bold bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full inline-flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                              Đã nạp vào trí nhớ AI
                            </span>
                            <span className="text-[9.5px] text-slate-400">
                              Lưu ngày: {doc.uploaded_at}
                            </span>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={() => handleDeleteKnowledgeDoc(doc.id, doc.filename)}
                          className="p-1.5 text-slate-300 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors cursor-pointer shrink-0 mt-0.5"
                          title="Xóa tài liệu này"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL XÁC NHẬN XÓA TÀI LIỆU (NHI KHOA ẤM ÁP) */}
      {deletingDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl p-6 max-w-sm w-full shadow-2xl border border-slate-100 space-y-4 animate-in zoom-in-95 duration-200">
            <div className="w-12 h-12 rounded-2xl bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-500 mx-auto">
              <Trash2 className="w-6 h-6" />
            </div>

            <div className="text-center space-y-1.5">
              <h3 className="text-base font-bold text-slate-800">
                Xóa tài liệu khỏi bộ nhớ AI?
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Mẹ có chắc muốn xóa tài liệu <span className="font-semibold text-slate-700">"{deletingDoc.filename}"</span> không? Sau khi xóa, trợ lý AI sẽ không thể tham chiếu các kiến thức từ tài liệu này nữa.
              </p>
            </div>

            <div className="flex gap-2.5 pt-2">
              <button
                type="button"
                onClick={() => setDeletingDoc(null)}
                disabled={isDeletingDoc}
                className="flex-1 py-2.5 px-4 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-colors cursor-pointer disabled:opacity-50"
              >
                Giữ lại tài liệu
              </button>
              <button
                type="button"
                onClick={handleConfirmDeleteKnowledgeDoc}
                disabled={isDeletingDoc}
                className="flex-1 py-2.5 px-4 rounded-xl bg-rose-600 text-white text-xs font-bold hover:bg-rose-700 transition-colors shadow-sm cursor-pointer disabled:opacity-50 inline-flex items-center justify-center gap-1.5"
              >
                {isDeletingDoc ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Đang xóa...</span>
                  </>
                ) : (
                  <span>Xác nhận xóa</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

