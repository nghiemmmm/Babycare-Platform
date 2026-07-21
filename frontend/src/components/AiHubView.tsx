import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  MessageSquare,
  Sparkles,
  Mic,
  Send,
  Paperclip,
  Check,
  ChevronDown,
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
  Award
} from "lucide-react";
import { BabyProfile, ChatMessage, SmartExtraction } from "../types";

interface AiHubViewProps {
  activeBaby: BabyProfile;
  chats: ChatMessage[];
  onSendMessage: (text: string) => Promise<void>;
  onConfirmExtraction: (ext: SmartExtraction) => void;
  isAiLoading: boolean;
  onStartNapTimer: () => void;
  isNapTimerRunning: boolean;
  napElapsedTime: number; // seconds
  threads: Array<{ id: string; title: string }>;
  activeThreadId: string;
  onSelectThread: (id: string) => void;
  onCreateThread: () => Promise<void>;
}

export default function AiHubView({
  activeBaby,
  chats,
  onSendMessage,
  onConfirmExtraction,
  isAiLoading,
  onStartNapTimer,
  isNapTimerRunning,
  napElapsedTime,
  threads,
  activeThreadId,
  onSelectThread,
  onCreateThread
}: AiHubViewProps) {
  const [inputText, setInputText] = useState("");
  const [activeThread, setActiveThread] = useState("sitting");
  const [showCitationDropdown, setShowCitationDropdown] = useState(false);
  const [showSwitchBabyDropdown, setShowSwitchBabyDropdown] = useState(false);
  
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
          
          {threads.map((thread) => (
            <button
              key={thread.id}
              onClick={() => onSelectThread(thread.id)}
              className={`w-full text-left p-3 rounded-xl text-xs font-bold transition-all flex items-center gap-2.5 cursor-pointer ${
                activeThreadId === thread.id
                  ? "bg-[#e0f2fe]/70 text-[#1c648e]"
                  : "text-slate-500 hover:bg-white/40"
              }`}
            >
              <MessageSquare className="w-4 h-4 shrink-0 text-[#1c648e]" />
              <span className="truncate">{thread.title}</span>
            </button>
          ))}
        </div>

        {/* User Mini-Profile panel */}
        <div className="p-3 bg-white/50 border border-white/30 rounded-2xl flex items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-rose-200 overflow-hidden flex items-center justify-center border border-white">
              <span className="text-[10px] font-black text-rose-600">Bo</span>
            </div>
            <div>
              <p className="text-xs font-bold text-slate-800">Bé Bo</p>
              <p className="text-[9px] text-slate-400 font-bold">6 tháng tuổi</p>
            </div>
          </div>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
        </div>
      </div>

      {/* 2. Cột Trung tâm (55%): Cửa sổ Chat thông minh (The AI Hub) */}
      <div className="flex-1 flex flex-col bg-slate-50/40 relative h-full">
        {/* Header Chat */}
        <div className="p-4 border-b border-white/20 flex items-center justify-between bg-white/30 backdrop-blur-md">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-black text-slate-800">Tiến trình tập ngồi của bé Bo</h2>
              
              {/* Switch Baby Dropdown selector button */}
              <div className="relative">
                <button
                  onClick={() => setShowSwitchBabyDropdown(!showSwitchBabyDropdown)}
                  className="bg-white/60 hover:bg-white border border-slate-200 px-2 py-0.5 rounded-md text-[9px] font-extrabold text-slate-500 inline-flex items-center gap-1 cursor-pointer"
                >
                  Chọn bé
                  <ChevronDown className="w-2.5 h-2.5" />
                </button>

                <AnimatePresence>
                  {showSwitchBabyDropdown && (
                    <motion.div
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 5 }}
                      className="absolute left-0 mt-1.5 w-32 bg-white border border-slate-100 rounded-xl shadow-lg p-1 z-50 text-[10px] font-bold"
                    >
                      <button className="w-full text-left p-2 hover:bg-slate-50 rounded-lg text-[#1c648e]">
                        Bé Bo (Đang chọn)
                      </button>
                      <button className="w-full text-left p-2 hover:bg-slate-50 rounded-lg text-slate-600">
                        {activeBaby.name}
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
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

        {/* Messages List Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs leading-relaxed">
          
          {/* AI Response Bubble 1 */}
          <div className="flex items-start gap-3 mr-auto max-w-[85%]">
            <div className="w-8 h-8 rounded-full bg-[#1c648e]/10 text-[#1c648e] flex items-center justify-center shrink-0 mt-0.5">
              <Sparkles className="w-4.5 h-4.5" />
            </div>
            <div className="space-y-2">
              <div className="bg-white/70 backdrop-blur-md border border-white/40 text-slate-700 rounded-3xl rounded-tl-xs p-4 shadow-sm">
                <p>
                  Dựa trên mô tả của bạn, bé đang tiến bộ rất nhanh về **tập ngồi tựa**. Ở mốc 6 tháng, nhiều bé mới đang bắt đầu chống tay đẩy người lên trong tư thế nằm sấp.
                </p>
                <p className="mt-2">
                  Hãy tiếp tục khuyến khích bé nằm sấp để tăng cường cơ liên sườn và cơ bụng cơ bản nhé!
                </p>
              </div>

              {/* Accordion citations */}
              <div className="relative">
                <button
                  onClick={() => setShowCitationDropdown(!showCitationDropdown)}
                  className="inline-flex items-center gap-1 text-[10px] font-bold text-[#1c648e] bg-[#e0f2fe]/40 border border-[#e0f2fe]/80 rounded-lg px-2.5 py-1 hover:bg-[#e0f2fe]/60 transition-colors cursor-pointer"
                >
                  <BookOpen className="w-3.5 h-3.5" />
                  XEM TÀI LIỆU THAM KHẢO
                  <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${showCitationDropdown ? "rotate-180" : ""}`} />
                </button>

                <AnimatePresence>
                  {showCitationDropdown && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-1.5 overflow-hidden p-2.5 bg-white/60 border border-white/30 rounded-xl space-y-1 text-[10px] font-semibold text-slate-500"
                    >
                      <p>📚 Mốc Phát triển Thể chất Trẻ sơ sinh WHO (2024)</p>
                      <p>🏥 Hướng dẫn Vận động Thể chất Nhi khoa AAP (Trang 142)</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </div>

          {/* User Voice Memo Bubble (Right) */}
          <div className="flex items-start gap-3 ml-auto max-w-[80%] justify-end">
            <div className="bg-[#7cb9e8]/15 border border-[#7cb9e8]/30 rounded-3xl rounded-tr-xs px-4 py-3 shadow-2xs flex items-center gap-3">
              <button
                onClick={handlePlayVoice}
                className="w-8 h-8 rounded-full bg-[#7cb9e8] text-white flex items-center justify-center transition-transform hover:scale-105 cursor-pointer"
              >
                {isVoicePlaying ? <Pause className="w-4 h-4 fill-white" /> : <Play className="w-4 h-4 fill-white ml-0.5" />}
              </button>
              
              {/* Voice waveform animation */}
              <div className="flex items-end gap-0.5 h-6 w-32 px-1">
                {[8, 12, 16, 6, 14, 18, 10, 5, 9, 15, 12, 6, 8, 14].map((h, idx) => (
                  <motion.div
                    key={idx}
                    animate={isVoicePlaying ? {
                      height: [h, h * 1.6, h * 0.4, h],
                    } : {}}
                    transition={{
                      repeat: Infinity,
                      duration: 1,
                      delay: idx * 0.08
                    }}
                    style={{
                      height: `${h * 1.1}px`,
                      opacity: voiceProgress > (idx / 14) * 100 ? 1 : 0.4
                    }}
                    className="w-[3px] bg-[#1c648e] rounded-full"
                  />
                ))}
              </div>
              <span className="text-[10px] font-black text-[#1c648e] font-mono">0:08</span>
            </div>

            <div className="w-8 h-8 rounded-full bg-sky-200 overflow-hidden flex items-center justify-center shrink-0 border border-white mt-1">
              <span className="text-[10px] font-black text-sky-700">M</span>
            </div>
          </div>

          {/* AI Response Bubble 2 */}
          <div className="flex items-start gap-3 mr-auto max-w-[85%]">
            <div className="w-8 h-8 rounded-full bg-[#1c648e]/10 text-[#1c648e] flex items-center justify-center shrink-0 mt-0.5">
              <Sparkles className="w-4.5 h-4.5" />
            </div>
            <div className="bg-[#ecfdf5]/70 border border-[#ecfdf5] backdrop-blur-md text-slate-700 rounded-3xl rounded-tl-xs p-4 shadow-sm">
              <p>
                Tôi ghi nhận là bé vừa bú bình xong **150ml**. Điều này rất tuyệt! Lượng sữa này hoàn toàn phù hợp với nhu cầu khuyến nghị cho độ tuổi của bé. Tôi đã tạo sẵn biểu mẫu ghi nhận cữ bú để bạn xác nhận ở góc phải màn hình.
              </p>
            </div>
          </div>

          {chats.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start gap-3 max-w-[85%] ${
                msg.role === "user" ? "ml-auto justify-end" : "mr-auto"
              }`}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-[#1c648e]/10 text-[#1c648e] flex items-center justify-center shrink-0 mt-0.5">
                  <Sparkles className="w-4.5 h-4.5" />
                </div>
              )}

              <div
                className={`rounded-3xl p-4 shadow-sm ${
                  msg.role === "user"
                    ? "bg-[#7cb9e8] text-white rounded-tr-xs"
                    : "bg-white/70 border border-white/40 text-slate-700 rounded-tl-xs"
                }`}
              >
                <p>{msg.content}</p>
              </div>
            </div>
          ))}

          {isAiLoading && (
            <div className="flex items-start gap-3 mr-auto">
              <div className="w-8 h-8 rounded-full bg-[#1c648e]/10 text-[#1c648e] flex items-center justify-center shrink-0 animate-pulse">
                <Sparkles className="w-4.5 h-4.5" />
              </div>
              <div className="bg-white/70 border border-white/40 text-slate-400 rounded-2xl rounded-tl-xs p-3.5 flex items-center gap-2">
                <span className="flex gap-1 animate-pulse">
                  <span className="w-1.5 h-1.5 bg-[#1c648e] rounded-full" />
                  <span className="w-1.5 h-1.5 bg-[#1c648e] rounded-full" />
                  <span className="w-1.5 h-1.5 bg-[#1c648e] rounded-full" />
                </span>
                <span className="text-[10px] font-bold">Trợ lý AI đang xử lý...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="p-4 bg-white/20 border-t border-white/20 select-none">
          <div className="max-w-3xl mx-auto flex items-center gap-2.5 bg-white/80 border border-white/40 rounded-full px-4 py-2 shadow-xs">
            <button className="p-1 text-slate-400 hover:text-slate-600 transition-colors cursor-pointer" title="Đính kèm tệp">
              <Paperclip className="w-4 h-4" />
            </button>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Hỏi về cữ bú hoặc giấc ngủ của ${activeBaby.name}...`}
              className="flex-1 bg-transparent border-none outline-hidden text-xs text-slate-700 placeholder-slate-400 font-medium"
            />
            <button className="p-1 text-slate-400 hover:text-[#1c648e] transition-colors cursor-pointer" title="Sử dụng micro">
              <Mic className="w-4 h-4" />
            </button>
            <button
              onClick={handleSend}
              disabled={!inputText.trim() || isAiLoading}
              className="w-8 h-8 rounded-full bg-[#1c648e] hover:bg-[#154c6d] text-white flex items-center justify-center disabled:bg-slate-200 disabled:text-slate-400 transition-all cursor-pointer shadow-xs"
            >
              <Send className="w-3.5 h-3.5 fill-white" />
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
                  onClick={() => {}}
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
