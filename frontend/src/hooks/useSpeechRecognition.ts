import { useState, useEffect, useCallback, useRef } from "react";

interface UseSpeechRecognitionOptions {
  silenceTimeoutMs?: number; // mặc định 1500ms
  enableDynamicTimeout?: boolean; // Tự động co giãn timeout theo ngữ cảnh câu nói
  onSilence?: (transcript: string) => void;
  onSpeechStart?: () => void;
  onSpeechEnd?: () => void;
}

interface UseSpeechRecognitionReturn {
  isListening: boolean;
  transcript: string;
  isSupported: boolean;
  error: string | null;
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;
}

/**
 * Tính toán Silence Timeout động (Dynamic Adaptive Endpointing):
 * - Câu đang mở/lửng lơ hoặc ngập ngừng (chưa có liều lượng/đơn vị) -> Kéo dài 2200ms
 * - Câu đã có cấu trúc hoàn chỉnh (có số lượng + đơn vị đo) -> Rút ngắn 1200ms
 */
function calculateDynamicTimeout(text: string, defaultTimeoutMs: number = 1500): number {
  if (!text || !text.trim()) return defaultTimeoutMs;
  const t = text.toLowerCase().trim();

  // 1. Dấu hiệu câu đang dang dở (Dangling / Incomplete State)
  const DRAFT_PATTERNS = [
    /\b(vừa|mới|cho bé|uống|bú|ăn|dặm|tiêm|dùng|uống thuốc)\s*$/,
    /\b(hapacol|paracetamol|vitamin|siro|kháng sinh|thuốc)\s*$/,
    /\b(sữa|cháo|bột|bình)\s*$/,
    /\b(\d+|một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười|trăm|chục|nghìn)\s*$/,
    /\b(khoảng|tầm|chừng|cỡ|được)\s*$/
  ];

  if (DRAFT_PATTERNS.some((p) => p.test(t))) {
    return Math.max(defaultTimeoutMs, 2200);
  }

  // 2. Dấu hiệu câu đã có cấu trúc hoàn chỉnh (Complete State)
  const COMPLETE_PATTERNS = [
    /\b\d+(\.\d+)?\s*(ml|cc|g|gam|kg|mg|gói|giọt|viên|độ|phút|tiếng)\b/,
    /\b(sữa mẹ|sữa công thức|thay tã|tè ướt|đi ngoài|đi ngủ|thức dậy)\b/
  ];

  if (COMPLETE_PATTERNS.some((p) => p.test(t))) {
    return Math.min(defaultTimeoutMs, 1200);
  }

  return defaultTimeoutMs;
}

export function useSpeechRecognition(options: UseSpeechRecognitionOptions = {}): UseSpeechRecognitionReturn {
  const {
    silenceTimeoutMs = 1500,
    enableDynamicTimeout = true,
    onSilence,
    onSpeechStart,
    onSpeechEnd
  } = options;

  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  
  const recognitionRef = useRef<any>(null);
  const silenceTimerRef = useRef<any>(null);
  const transcriptRef = useRef("");
  const isSubmittingRef = useRef(false);

  // Stable refs for callbacks
  const onSilenceRef = useRef(onSilence);
  const onSpeechStartRef = useRef(onSpeechStart);
  const onSpeechEndRef = useRef(onSpeechEnd);
  const silenceTimeoutMsRef = useRef(silenceTimeoutMs);
  const enableDynamicTimeoutRef = useRef(enableDynamicTimeout);

  useEffect(() => {
    onSilenceRef.current = onSilence;
    onSpeechStartRef.current = onSpeechStart;
    onSpeechEndRef.current = onSpeechEnd;
    silenceTimeoutMsRef.current = silenceTimeoutMs;
    enableDynamicTimeoutRef.current = enableDynamicTimeout;
  }, [onSilence, onSpeechStart, onSpeechEnd, silenceTimeoutMs, enableDynamicTimeout]);

  const SpeechRecognition =
    typeof window !== "undefined" &&
    ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition);

  const isSupported = Boolean(SpeechRecognition);

  const clearSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  }, []);

  const dispatchFinalTranscript = useCallback((text: string) => {
    if (isSubmittingRef.current) return;
    const cleanText = text.trim();
    if (!cleanText) return;

    isSubmittingRef.current = true;
    transcriptRef.current = "";
    if (onSilenceRef.current) {
      onSilenceRef.current(cleanText);
    }
  }, []);

  useEffect(() => {
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "vi-VN";

    recognition.onspeechstart = () => {
      clearSilenceTimer();
      if (onSpeechStartRef.current) {
        onSpeechStartRef.current();
      }
    };

    recognition.onspeechend = () => {
      if (onSpeechEndRef.current) {
        onSpeechEndRef.current();
      }
    };

    recognition.onresult = (event: any) => {
      let fullTranscript = "";
      for (let i = 0; i < event.results.length; i++) {
        fullTranscript += event.results[i][0].transcript;
      }
      setTranscript(fullTranscript);
      transcriptRef.current = fullTranscript;

      clearSilenceTimer();

      if (fullTranscript.trim()) {
        const timeoutDuration = enableDynamicTimeoutRef.current
          ? calculateDynamicTimeout(fullTranscript, silenceTimeoutMsRef.current)
          : silenceTimeoutMsRef.current;

        silenceTimerRef.current = setTimeout(() => {
          try {
            recognition.stop();
          } catch (e) {
            // ignore
          }
          setIsListening(false);
          dispatchFinalTranscript(transcriptRef.current);
        }, timeoutDuration);
      }
    };

    recognition.onerror = (event: any) => {
      clearSilenceTimer();
      setError(event.error || "Lỗi nhận diện giọng nói");
      setIsListening(false);
    };

    recognition.onend = () => {
      clearSilenceTimer();
      setIsListening(false);
      // Fallback: nếu ngắt tự nhiên từ trình duyệt mà chưa gửi
      if (transcriptRef.current.trim() && !isSubmittingRef.current) {
        dispatchFinalTranscript(transcriptRef.current);
      }
    };

    recognitionRef.current = recognition;

    return () => {
      clearSilenceTimer();
    };
  }, [SpeechRecognition, clearSilenceTimer, dispatchFinalTranscript]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) {
      if (!isSupported) {
        setError("Trình duyệt không hỗ trợ Web Speech API. Vui lòng thử dùng Chrome hoặc Edge.");
      }
      return;
    }
    setError(null);
    setTranscript("");
    transcriptRef.current = "";
    isSubmittingRef.current = false;
    clearSilenceTimer();
    try {
      recognitionRef.current.start();
      setIsListening(true);
    } catch (e) {
      console.warn("SpeechRecognition already active:", e);
    }
  }, [isSupported, clearSilenceTimer]);

  const stopListening = useCallback(() => {
    clearSilenceTimer();
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        // ignore
      }
      setIsListening(false);
      if (transcriptRef.current.trim() && !isSubmittingRef.current) {
        dispatchFinalTranscript(transcriptRef.current);
      }
    }
  }, [clearSilenceTimer, dispatchFinalTranscript]);

  const resetTranscript = useCallback(() => {
    clearSilenceTimer();
    setTranscript("");
    transcriptRef.current = "";
    isSubmittingRef.current = false;
  }, [clearSilenceTimer]);

  return {
    isListening,
    transcript,
    isSupported,
    error,
    startListening,
    stopListening,
    resetTranscript,
  };
}
