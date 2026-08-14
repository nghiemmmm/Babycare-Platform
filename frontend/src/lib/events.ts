import { useEffect } from "react";

const BABY_DATA_UPDATED_EVENT = "baby-data-updated";

/**
 * Bắn Custom Event thông báo toàn cục rằng dữ liệu em bé vừa có sự thay đổi
 * (từ AI Chatbot, Form tay, hoặc Voice Logging).
 */
export function notifyBabyDataUpdated() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(BABY_DATA_UPDATED_EVENT));
  }
}

/**
 * Custom React Hook cho phép các Component (App, DashboardView, HealthView...)
 * tự động lắng nghe Event và gọi re-fetch dữ liệu mới trong < 100ms mà không cần F5.
 */
export function useBabyDataListener(onUpdate: () => void) {
  useEffect(() => {
    function handleEvent() {
      onUpdate();
    }

    window.addEventListener(BABY_DATA_UPDATED_EVENT, handleEvent);
    return () => {
      window.removeEventListener(BABY_DATA_UPDATED_EVENT, handleEvent);
    };
  }, [onUpdate]);
}
