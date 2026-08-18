import { useState, useEffect, useCallback, useRef } from "react";

interface UseSpeechRecognitionOptions {
  silenceTimeoutMs?: number; // mặc định 1500ms (1.5 giây im lặng tự gửi)
  onSilence?: (transcript: string) => void;
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

export function useSpeechRecognition(options: UseSpeechRecognitionOptions = {}): UseSpeechRecognitionReturn {
  const { silenceTimeoutMs = 1500, onSilence } = options;
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);
  const silenceTimerRef = useRef<any>(null);
  const transcriptRef = useRef("");
  
  // Stable refs for callbacks to prevent useEffect teardown on parent re-renders
  const onSilenceRef = useRef(onSilence);
  const silenceTimeoutMsRef = useRef(silenceTimeoutMs);

  useEffect(() => {
    onSilenceRef.current = onSilence;
    silenceTimeoutMsRef.current = silenceTimeoutMs;
  }, [onSilence, silenceTimeoutMs]);

  const SpeechRecognition =
    typeof window !== "undefined" &&
    ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition);

  const isSupported = Boolean(SpeechRecognition);

  const clearSilenceTimer = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  };

  useEffect(() => {
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "vi-VN";

    recognition.onresult = (event: any) => {
      let fullTranscript = "";
      for (let i = 0; i < event.results.length; i++) {
        fullTranscript += event.results[i][0].transcript;
      }
      setTranscript(fullTranscript);
      transcriptRef.current = fullTranscript;

      // Đếm ngược tự động dừng & gửi khi người dùng ngừng nói (1.5s)
      clearSilenceTimer();
      if (fullTranscript.trim()) {
        silenceTimerRef.current = setTimeout(() => {
          try {
            recognition.stop();
          } catch (e) {
            // ignore
          }
          setIsListening(false);
          if (onSilenceRef.current && transcriptRef.current.trim()) {
            const textToProcess = transcriptRef.current;
            transcriptRef.current = ""; // ngăn gửi lặp
            onSilenceRef.current(textToProcess);
          }
        }, silenceTimeoutMsRef.current);
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
      if (transcriptRef.current.trim() && onSilenceRef.current) {
        const textToProcess = transcriptRef.current;
        transcriptRef.current = "";
        onSilenceRef.current(textToProcess);
      }
    };

    recognitionRef.current = recognition;

    return () => {
      clearSilenceTimer();
    };
  }, [SpeechRecognition]);

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
    clearSilenceTimer();
    try {
      recognitionRef.current.start();
      setIsListening(true);
    } catch (e) {
      console.warn("SpeechRecognition already active:", e);
    }
  }, [isSupported]);

  const stopListening = useCallback(() => {
    clearSilenceTimer();
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        // ignore
      }
      setIsListening(false);
      if (transcriptRef.current.trim() && onSilenceRef.current) {
        const textToProcess = transcriptRef.current;
        transcriptRef.current = "";
        onSilenceRef.current(textToProcess);
      }
    }
  }, []);

  const resetTranscript = useCallback(() => {
    clearSilenceTimer();
    setTranscript("");
    transcriptRef.current = "";
  }, []);

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
