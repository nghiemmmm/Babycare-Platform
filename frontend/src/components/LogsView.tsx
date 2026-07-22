import React, { useState } from "react";
import {
  Clock,
  Coffee,
  Droplet,
  Pill,
  TrendingUp,
  Trash2
} from "lucide-react";
import { BabyProfile, FeedLog, MedicationLog, Measurement } from "../types";

interface LogsViewProps {
  activeBaby: BabyProfile;
  feeds: FeedLog[];
  medications: MedicationLog[];
  measurements: Measurement[];
  onAddFeed: (feed: Omit<FeedLog, "id">) => void;
  onDeleteFeed: (id: string) => void;
  onAddMedication: (med: Omit<MedicationLog, "id">) => void;
  onDeleteMedication: (id: string) => void;
  onAddMeasurement: (m: Omit<Measurement, "id">) => void;
}

export default function LogsView({
  activeBaby,
  feeds,
  medications,
  measurements,
  onDeleteFeed,
  onDeleteMedication,
}: LogsViewProps) {
  const [filterType, setFilterType] = useState<"all" | "feed" | "sleep" | "diaper" | "medication" | "growth">("all");

  // Sample diaper entries
  const diaperLogs = [
    { id: "d1", time: "10:30 AM", type: "Wet", status: "Bình thường", date: "Today" },
    { id: "d2", time: "07:15 AM", type: "Dirty", status: "Mềm", date: "Today" }
  ];

  // Combine all activity logs into a unified chronological stream
  const combinedLogs = [
    ...feeds.map((f) => ({
      id: f.id,
      category: "feed" as const,
      time: f.time,
      date: f.date || "Today",
      title: f.type === "Solids" ? "Ăn dặm" : f.type === "Formula" ? "Bú sữa công thức" : "Bú sữa mẹ",
      details: f.details,
      amount: f.amount ? `${f.amount} ml` : "",
      icon: Coffee,
      badgeColor: "bg-sky-100 text-sky-700 border-sky-200"
    })),
    ...medications.map((m) => ({
      id: m.id,
      category: "medication" as const,
      time: m.time,
      date: m.date || "Today",
      title: `Thuốc: ${m.name}`,
      details: `Liều dùng: ${m.dosage} • Chỉ định bởi: ${m.prescribedBy || "Tự ghi nhận"}`,
      amount: m.dosage,
      icon: Pill,
      badgeColor: "bg-purple-100 text-purple-700 border-purple-200"
    })),
    ...diaperLogs.map((d) => ({
      id: d.id,
      category: "diaper" as const,
      time: d.time,
      date: d.date,
      title: `Thay tã: ${d.type === "Dirty" ? "Tã bẩn (Phân)" : "Tã ướt (Nước tiểu)"}`,
      details: `Trạng thái: ${d.status}`,
      amount: d.type,
      icon: Droplet,
      badgeColor: "bg-[#fdfd96]/60 text-yellow-800 border-yellow-200"
    })),
    ...measurements.map((g) => ({
      id: g.id,
      category: "growth" as const,
      time: "09:00 AM",
      date: g.date,
      title: `Cập nhật chỉ số WHO`,
      details: `Cân nặng: ${g.weight} kg • Chiều cao: ${g.height} cm • Vòng đầu: ${g.headCircumference} cm`,
      amount: `${g.weight} kg`,
      icon: TrendingUp,
      badgeColor: "bg-emerald-100 text-emerald-700 border-emerald-200"
    }))
  ].sort((a, b) => {
    const timeToMins = (tStr: string) => {
      const match = tStr.match(/(\d+):(\d+)\s*(AM|PM)/i);
      if (!match) return 0;
      let h = parseInt(match[1]);
      const m = parseInt(match[2]);
      const ampm = match[3].toUpperCase();
      if (ampm === "PM" && h < 12) h += 12;
      if (ampm === "AM" && h === 12) h = 0;
      return h * 60 + m;
    };
    return timeToMins(b.time) - timeToMins(a.time);
  });

  const filteredLogs = filterType === "all" ? combinedLogs : combinedLogs.filter((l) => l.category === filterType);

  return (
    <div className="space-y-6" id="logs-view">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-primary font-bold text-2xl tracking-tight">Nhật ký Hoạt động Toàn diện</h1>
          <p className="text-xs text-slate-500 font-semibold mt-0.5">
            Dòng thời gian tổng hợp tất cả các cữ bú, giấc ngủ, thay tã và dùng thuốc của {activeBaby.name}.
          </p>
        </div>
        <div className="inline-flex items-center gap-1.5 bg-[#e0f2fe] text-[#1c648e] border border-sky-100 rounded-full px-4 py-1.5 text-xs font-bold shadow-xs">
          <Clock className="w-4 h-4 text-[#1c648e]" />
          Tự động đồng bộ thời gian thực
        </div>
      </div>

      {/* Filter Tabs & Quick Action Bar */}
      <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            {[
              { id: "all", label: "Tất cả hoạt động" },
              { id: "feed", label: "🍼 Cữ bú & Ăn dặm" },
              { id: "diaper", label: "💩 Thay tã" },
              { id: "medication", label: "💊 Uống thuốc" },
              { id: "growth", label: "📈 Tăng trưởng WHO" }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setFilterType(tab.id as any)}
                className={`px-4 py-2 rounded-xl text-xs font-bold border transition-all cursor-pointer ${
                  filterType === tab.id
                    ? "bg-[#1c648e] text-white border-[#1c648e] shadow-md shadow-[#1c648e]/20"
                    : "bg-white/60 border-slate-200 text-slate-600 hover:bg-white"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <span className="text-xs font-bold text-slate-400">
            Tổng số: <span className="text-slate-800 font-black">{filteredLogs.length}</span> ghi chép
          </span>
        </div>
      </div>

      {/* Main Timeline Stream */}
      <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 className="text-primary font-bold text-sm tracking-tight flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#1c648e]" />
            Dòng thời gian chi tiết
          </h3>
          <span className="text-xs font-bold text-slate-400 bg-white border border-slate-200 px-3 py-1 rounded-lg">
            Hôm nay
          </span>
        </div>

        <div className="relative pl-6 border-l-2 border-sky-100 space-y-6">
          {filteredLogs.length === 0 ? (
            <p className="text-xs text-slate-400 text-center py-8 font-semibold">Chưa có ghi chép nào trong danh mục này hôm nay.</p>
          ) : (
            filteredLogs.map((log) => {
              const Icon = log.icon;
              return (
                <div key={log.id} className="relative group">
                  {/* Timeline dot */}
                  <span className="absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-white border-2 border-[#1c648e] shadow-xs flex items-center justify-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#1c648e]" />
                  </span>

                  <div className="bg-white/80 border border-white/60 rounded-2xl p-4 shadow-xs hover:shadow-md transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <div className="p-2.5 rounded-xl bg-sky-50 text-[#1c648e] shrink-0 mt-0.5">
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h4 className="text-xs font-bold text-slate-800">{log.title}</h4>
                          <span className={`text-[9px] font-extrabold px-2 py-0.5 rounded-md border ${log.badgeColor}`}>
                            {log.time}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 font-medium leading-relaxed">{log.details}</p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between sm:justify-end gap-3 shrink-0 border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-100">
                      {log.amount && (
                        <span className="text-xs font-black text-slate-700 bg-slate-100 px-3 py-1 rounded-xl">
                          {log.amount}
                        </span>
                      )}
                      {(log.category === "feed" || log.category === "medication") && (
                        <button
                          onClick={() => {
                            if (log.category === "feed") onDeleteFeed(log.id);
                            if (log.category === "medication") onDeleteMedication(log.id);
                          }}
                          className="text-slate-400 hover:text-rose-500 transition-colors p-1 cursor-pointer"
                          title="Xóa ghi chép này"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
