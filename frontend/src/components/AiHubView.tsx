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
  Square
} from "lucide-react";
import { BabyProfile, ChatMessage, SmartExtraction, ToolStep } from "../types";

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


  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isUploadingChatFile, setIsUploadingChatFile] = useState(false);

  const { isListening, transcript, startListening, stopListening } = useSpeechRecognition({
    silenceTimeoutMs: 1500,
    onSilence: (finalText) => {
      if (finalText && finalText.trim()) {
        setInputText("");
        onSendMessage(finalText.trim());
      }
    }
  });

  const handleFileUploadInChat = async (file: File) => {
    setIsUploadingChatFile(true);
    try {
      const formData = new FormData();
      formData.append("audio_file", file);

      const baseUrl = import.meta.env.VITE_API_BASE_URL || "";
      const token = localStorage.getItem("token") || "mock-token";

      const res = await fetch(`${baseUrl}/api/v1/babies/${activeBaby.id}/cry-prediction`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        const pred = data.prediction || "discomfort";
        const soundPlayed = data.sound_played || "/static/sounds/lullabies/classic_lullaby.mp3";
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

      {/* 1. Cột Trái (20%): Lịch sử hội thoại (Recent Chats) */}
      <div className="w-[22%] bg-white/40 border-r border-white/20 flex flex-col p-4 space-y-5 select-none shrink-0 h-full">
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
                    : "text-slate-500 hover:bg-white/40"
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


        {/* User Mini-Profile panel */}
        <div className="relative">
          <button
            onClick={() => setShowSwitchBabyDropdown(!showSwitchBabyDropdown)}
            className="w-full p-3 bg-white/60 hover:bg-white border border-white/40 rounded-2xl flex items-center justify-between gap-2 cursor-pointer transition-all shadow-xs"
          >
            <div className="flex items-center gap-2.5">
              <img
                src={activeBaby.avatarUrl || "/static/img/leo.png"}
                alt={activeBaby.name}
                className="w-8 h-8 rounded-full object-cover border border-white shrink-0"
                onError={(e) => { (e.currentTarget as HTMLImageElement).src = "/static/img/leo.png"; }}
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
                        src={b.avatarUrl || "/static/img/leo.png"}
                        alt={b.name}
                        className="w-6 h-6 rounded-full object-cover"
                        onError={(e) => { (e.currentTarget as HTMLImageElement).src = "/static/img/leo.png"; }}
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

      {/* 2. Cột Trung tâm (55%): Cửa sổ Chat thông minh (The AI Hub) */}
      <div className="flex-1 flex flex-col bg-[#f8fafc] relative h-full">
        {/* Header Chat */}
        {(() => {
          const currentThread = threads.find((t) => t.id === activeThreadId);
          return (
            <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-white/70 backdrop-blur-md">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-black text-slate-800">{currentThread?.title || "Trò chuyện với Trợ lý AI"}</h2>
                  <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-[#1c648e]/10 text-[#1c648e]">
                    {formatBabyName(activeBaby.name)}
                  </span>
                </div>

                <p className="text-[10px] text-slate-400 font-medium flex items-center gap-1.5 mt-0.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block animate-pulse" />
                  Sẵn sàng hỗ trợ tư vấn — Tích hợp Gemini Flash
                </p>
              </div>

              <div className="flex items-center gap-3 text-slate-600">
                <button className="p-2 hover:bg-white/60 rounded-xl cursor-pointer transition-colors">
                  <Phone className="w-4 h-4 text-slate-600" />
                </button>
                <button className="p-2 hover:bg-white/60 rounded-xl cursor-pointer transition-colors">
                  <Video className="w-4 h-4 text-slate-600" />
                </button>
              </div>
            </div>
          );
        })()}

        {/* Messages List Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs leading-relaxed">

          {chats.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-400 space-y-3 py-12">
              <div className="w-12 h-12 rounded-full bg-[#1c648e]/10 text-[#1c648e] flex items-center justify-center">
                <Sparkles className="w-6 h-6" />
              </div>
              <p className="text-xs font-bold text-slate-600">Phiên trò chuyện mới cho {activeBaby.name}</p>
              <p className="text-[11px] text-slate-400 text-center max-w-xs leading-relaxed">
                Hãy đặt câu hỏi về cữ bú, giấc ngủ, chỉ số cân nặng hoặc cách chăm sóc {activeBaby.name} bên dưới!
              </p>
            </div>
          ) : (
            chats.map((msg) => (
              <div
                key={msg.id}
                className={`flex items-start gap-3 max-w-[85%] ${msg.role === "user" ? "ml-auto justify-end" : "mr-auto"
                  }`}
              >
                {msg.role === "assistant" && (
                  <div className="w-8 h-8 rounded-full bg-[#1c648e]/10 text-[#1c648e] flex items-center justify-center shrink-0 mt-0.5">
                    <Sparkles className="w-4.5 h-4.5" />
                  </div>
                )}

                <div
                  className={`rounded-3xl p-4 shadow-sm ${msg.role === "user"
                      ? "bg-[#1c648e] text-white rounded-tr-xs"
                      : "bg-white/70 border border-white/40 text-slate-700 rounded-tl-xs"
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
        <div className="p-4 bg-white/20 border-t border-white/20 select-none">
          <div className="max-w-3xl mx-auto flex items-center gap-2.5 bg-white/80 border border-white/40 rounded-full px-4 py-2 shadow-xs">
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploadingChatFile || isAiLoading}
              className="p-1 text-slate-400 hover:text-[#1c648e] transition-colors cursor-pointer disabled:opacity-50"
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
              placeholder={`Hỏi về cữ bú hoặc giấc ngủ của ${activeBaby.name}...`}
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

          <div className="text-center mt-2.5">
            <span className="text-[8px] font-bold text-slate-400 tracking-widest uppercase">
              Dữ liệu em bé được bảo mật & mã hóa
            </span>
          </div>
        </div>
      </div>

      {/* 3. Cột Phải (25%): Trích xuất thông minh (Smart Extraction) */}
      <div className="w-[25%] bg-white/40 border-l border-white/20 p-5 flex flex-col justify-between shrink-0 h-full overflow-y-auto space-y-6">

        {/* Suggested log extractions */}
        <div className="space-y-4">
          <div>
            <h3 className="text-xs font-bold text-slate-700 tracking-wide flex items-center gap-1.5">
              <Sparkles className="w-4.5 h-4.5 text-[#1c648e] animate-pulse" />
              Trích xuất thông minh
            </h3>
            <p className="text-[9px] text-slate-400 font-semibold mt-0.5">Nhật ký gợi ý từ trò chuyện</p>
          </div>

          <div className="space-y-4">

            {/* Suggested Feeding Log Card */}
            <div className="bg-white/60 border border-white/40 rounded-2xl p-4 space-y-4 shadow-sm hover:bg-white/80 transition-all">
              <div className="flex items-center justify-between">
                <div className="w-8 h-8 rounded-xl bg-sky-50 text-[#1c648e] flex items-center justify-center font-bold">
                  🍼
                </div>
                <span className="text-[9px] text-slate-400 font-bold">12:00 PM</span>
              </div>

              <div>
                <h4 className="text-xs font-bold text-slate-800">Nhật ký cữ bú</h4>
                <p className="text-[10px] text-slate-400 font-semibold mt-0.5">LƯỢNG SỮA</p>
                <p className="text-lg font-black text-slate-800 mt-0.5">150ml</p>
                <p className="text-[8px] text-slate-400 italic mt-1">Phát hiện trong ghi âm</p>
              </div>

              <button
                onClick={() => onConfirmExtraction({
                  type: "feeding",
                  title: "Nhật ký cữ bú",
                  detail: "150ml Sữa công thức",
                  value: 150,
                  time: "12:00 PM"
                })}
                className="w-full bg-[#1c648e] hover:bg-[#154c6d] text-white text-[10px] font-bold py-2 rounded-xl transition-all cursor-pointer shadow-xs"
              >
                Xác nhận ghi nhật ký
              </button>
            </div>

            {/* Suggested Nap Duration (Pending) Card */}
            <div className="bg-white/60 border border-white/40 rounded-2xl p-4 space-y-4 shadow-sm hover:bg-white/80 transition-all">
              <div className="flex items-center justify-between">
                <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold">
                  🌙
                </div>
                <span className="text-[9px] text-slate-400 font-bold">Đang chờ</span>
              </div>

              <div>
                <h4 className="text-xs font-bold text-slate-800">Thời lượng giấc ngủ?</h4>
                <p className="text-[10px] text-slate-500 leading-relaxed font-semibold mt-1">
                  {activeBaby.name} dường như đang ngủ. Bạn có muốn bắt đầu đếm giờ ngủ không?
                </p>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => { }}
                  className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-600 text-[10px] font-bold py-2 rounded-xl transition-all cursor-pointer"
                >
                  Không
                </button>
                <button
                  onClick={onStartNapTimer}
                  className="flex-1 bg-[#22c55e] hover:bg-emerald-600 text-white text-[10px] font-bold py-2 rounded-xl transition-all cursor-pointer shadow-xs"
                >
                  {isNapTimerRunning ? "Dừng" : "Bắt đầu"}
                </button>
              </div>
            </div>

          </div>
        </div>

        {/* Daily summary completion bar */}
        <div className="bg-[#e0f2fe]/40 border border-[#e0f2fe]/60 rounded-2xl p-4 space-y-3 mt-auto">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wide flex items-center gap-1">
              <Award className="w-3.5 h-3.5 text-[#1c648e]" />
              TỔNG HỢP HÀNG NGÀY
            </span>
          </div>

          <div className="w-full bg-slate-200/50 h-1.5 rounded-full overflow-hidden">
            <div className="bg-[#1c648e] h-full rounded-full w-[65%]" />
          </div>

          <div className="text-right">
            <span className="text-[9px] font-bold text-[#1c648e]">Hoàn thành 65% mục tiêu ngày</span>
          </div>
        </div>

      </div>

    </div>
  );
}
