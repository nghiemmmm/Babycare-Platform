import React, { useState } from "react";
import {
  Clock,
  Coffee,
  Droplet,
  Pill,
  TrendingUp,
  Trash2,
  Calendar,
  Activity,
  BarChart3,
  CheckCircle2
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
  // Filter category state
  const [filterType, setFilterType] = useState<"all" | "feed" | "sleep" | "diaper" | "medication" | "growth">("all");
  
  // Time range filter state: "today", "yesterday", "7days", "all"
  const [timeRange, setTimeRange] = useState<"today" | "yesterday" | "7days" | "all">("today");

  // Sample diaper entries (including Today, Yesterday, and 7 Days Ago)
  const diaperLogs = [
    { id: "d1", time: "10:30 AM", type: "Wet", status: "Bình thường", date: "Today" },
    { id: "d2", time: "07:15 AM", type: "Dirty", status: "Mềm", date: "Today" },
    { id: "d3", time: "08:45 PM", type: "Wet", status: "Bình thường", date: "Yesterday" },
    { id: "d4", time: "02:20 PM", type: "Both", status: "Tự nhiên", date: "Yesterday" },
    { id: "d5", time: "09:00 AM", type: "Wet", status: "Bình thường", date: "7 Days Ago" }
  ];

  // Combined baseline logs from props + historical sample logs for Yesterday & 7 Days Ago
  const allRawLogs = [
    ...feeds.map((f) => ({
      id: f.id,
      category: "feed" as const,
      time: f.time,
      date: f.date || "Today",
      title: f.type === "Solids" ? "Ăn dặm" : f.type === "Formula" ? "Bú sữa công thức" : "Bú sữa mẹ",
      details: f.details,
      rawAmount: f.amount || 0,
      amountStr: f.amount ? `${f.amount} ml` : "",
      icon: Coffee,
      badgeColor: "bg-[#7cb9e8]/20 text-[#1c648e] border-[#7cb9e8]/30"
    })),
    // Yesterday sample feed logs
    {
      id: "f_y1",
      category: "feed" as const,
      time: "08:30 PM",
      date: "Yesterday",
      title: "Bú sữa công thức",
      details: "Formula Milk • 180ml trước khi đi ngủ",
      rawAmount: 180,
      amountStr: "180 ml",
      icon: Coffee,
      badgeColor: "bg-[#7cb9e8]/20 text-[#1c648e] border-[#7cb9e8]/30"
    },
    {
      id: "f_y2",
      category: "feed" as const,
      time: "01:15 PM",
      date: "Yesterday",
      title: "Ăn dặm",
      details: "Bột bí đỏ nghiền bơ",
      rawAmount: 1,
      amountStr: "1 cữ",
      icon: Coffee,
      badgeColor: "bg-[#7cb9e8]/20 text-[#1c648e] border-[#7cb9e8]/30"
    },
    // 7 Days ago sample feed logs
    {
      id: "f_7d1",
      category: "feed" as const,
      time: "10:00 AM",
      date: "7 Days Ago",
      title: "Bú sữa mẹ",
      details: "Sữa mẹ vắt cữ sáng",
      rawAmount: 160,
      amountStr: "160 ml",
      icon: Coffee,
      badgeColor: "bg-[#7cb9e8]/20 text-[#1c648e] border-[#7cb9e8]/30"
    },

    ...medications.map((m) => ({
      id: m.id,
      category: "medication" as const,
      time: m.time,
      date: m.date || "Today",
      title: `Thuốc: ${m.name}`,
      details: `Liều dùng: ${m.dosage} • Chỉ định bởi: ${m.prescribedBy || "Tự ghi nhận"}`,
      rawAmount: 0,
      amountStr: m.dosage,
      icon: Pill,
      badgeColor: "bg-purple-100 text-purple-700 border-purple-200"
    })),
    // Yesterday medication sample
    {
      id: "m_y1",
      category: "medication" as const,
      time: "09:00 AM",
      date: "Yesterday",
      title: "Thuốc: Vitamin D3",
      details: "Liều dùng: 2 giọt • Bổ sung hàng ngày",
      rawAmount: 0,
      amountStr: "2 giọt",
      icon: Pill,
      badgeColor: "bg-purple-100 text-purple-700 border-purple-200"
    },

    ...diaperLogs.map((d) => ({
      id: d.id,
      category: "diaper" as const,
      time: d.time,
      date: d.date,
      title: `Thay tã: ${d.type === "Dirty" ? "Tã bẩn (Phân)" : d.type === "Wet" ? "Tã ướt (Nước tiểu)" : "Cả hai"}`,
      details: `Trạng thái: ${d.status}`,
      rawAmount: 0,
      amountStr: d.type === "Wet" ? "Ướt" : d.type === "Dirty" ? "Bẩn" : "Cả hai",
      icon: Droplet,
      badgeColor: "bg-[#fdfd96]/60 text-yellow-800 border-yellow-200"
    })),

    ...measurements.map((g) => ({
      id: g.id,
      category: "growth" as const,
      time: "09:00 AM",
      date: g.date || "Today",
      title: `Cập nhật chỉ số WHO`,
      details: `Cân nặng: ${g.weight} kg • Chiều cao: ${g.height} cm • Vòng đầu: ${g.headCircumference} cm`,
      rawAmount: 0,
      amountStr: `${g.weight} kg`,
      icon: TrendingUp,
      badgeColor: "bg-emerald-100 text-emerald-700 border-emerald-200"
    }))
  ];

  // Helper filter by Time Range
  const isMatchingTimeRange = (logDate: string) => {
    if (timeRange === "today") return logDate === "Today";
    if (timeRange === "yesterday") return logDate === "Yesterday";
    if (timeRange === "7days") return logDate === "Today" || logDate === "Yesterday" || logDate === "7 Days Ago";
    return true; // "all"
  };

  // Filter logs by Category and Time Range
  const timeFilteredLogs = allRawLogs.filter((l) => isMatchingTimeRange(l.date));
  const finalFilteredLogs = filterType === "all"
    ? timeFilteredLogs
    : timeFilteredLogs.filter((l) => l.category === filterType);

  // Compute Summary Statistics based on active Time Range filter
  const totalMilkMl = timeFilteredLogs
    .filter((l) => l.category === "feed" && l.rawAmount > 1)
    .reduce((acc, l) => acc + l.rawAmount, 0);

  const feedCount = timeFilteredLogs.filter((l) => l.category === "feed").length;
  const diaperCount = timeFilteredLogs.filter((l) => l.category === "diaper").length;
  const medCount = timeFilteredLogs.filter((l) => l.category === "medication").length;

  const timeRangeLabel: Record<string, string> = {
    today: "Hôm nay",
    yesterday: "Hôm qua",
    "7days": "7 ngày qua",
    all: "Tất cả thời gian"
  };

  return (
    <div className="space-y-6" id="logs-view">
      
      {/* 1. Header & Time Range Selection Buttons */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-primary font-bold text-2xl tracking-tight">Nhật ký Hoạt động Toàn diện</h1>
          <p className="text-xs text-slate-500 font-semibold mt-0.5">
            Dòng thời gian tổng hợp cữ bú, giấc ngủ, thay tã và dùng thuốc của {activeBaby.name}.
          </p>
        </div>

        {/* Time Range Filter Buttons */}
        <div className="flex bg-white/60 backdrop-blur-md p-1 rounded-2xl border border-white/40 shadow-xs self-start lg:self-auto">
          {[
            { id: "today", label: "Hôm nay" },
            { id: "yesterday", label: "Hôm qua" },
            { id: "7days", label: "7 ngày trước" },
            { id: "all", label: "Tất cả" }
          ].map((btn) => (
            <button
              key={btn.id}
              onClick={() => setTimeRange(btn.id as any)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-extrabold transition-all cursor-pointer ${
                timeRange === btn.id
                  ? "bg-[#1c648e] text-white shadow-xs"
                  : "text-slate-500 hover:text-slate-800 hover:bg-white/50"
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Summary Statistics Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Stat 1: Total Milk Intake */}
        <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[28px] p-4 space-y-2 hover:scale-105 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Tổng lượng sữa</span>
            <div className="p-2 rounded-xl bg-sky-50 text-[#1c648e]">
              <Coffee className="w-4 h-4" />
            </div>
          </div>
          <div>
            <h3 className="text-xl font-extrabold text-[#1c648e]">{totalMilkMl} ml</h3>
            <p className="text-[10px] text-slate-400 font-semibold mt-0.5">{feedCount} cữ ăn/bú • {timeRangeLabel[timeRange]}</p>
          </div>
        </div>

        {/* Stat 2: Diaper Changes */}
        <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[28px] p-4 space-y-2 hover:scale-105 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Thay tã</span>
            <div className="p-2 rounded-xl bg-amber-50 text-amber-600">
              <Droplet className="w-4 h-4" />
            </div>
          </div>
          <div>
            <h3 className="text-xl font-extrabold text-slate-800">{diaperCount} cữ</h3>
            <p className="text-[10px] text-slate-400 font-semibold mt-0.5">Tã ướt & bẩn • {timeRangeLabel[timeRange]}</p>
          </div>
        </div>

        {/* Stat 3: Medication Administered */}
        <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[28px] p-4 space-y-2 hover:scale-105 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Uống thuốc</span>
            <div className="p-2 rounded-xl bg-purple-50 text-purple-600">
              <Pill className="w-4 h-4" />
            </div>
          </div>
          <div>
            <h3 className="text-xl font-extrabold text-slate-800">{medCount} liều</h3>
            <p className="text-[10px] text-slate-400 font-semibold mt-0.5">Đã cho uống • {timeRangeLabel[timeRange]}</p>
          </div>
        </div>

        {/* Stat 4: Growth Index */}
        <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[28px] p-4 space-y-2 hover:scale-105 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Chỉ số WHO</span>
            <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div>
            <h3 className="text-xl font-extrabold text-slate-800">
              {measurements[0] ? `${measurements[0].weight} kg` : "7.4 kg"}
            </h3>
            <p className="text-[10px] text-slate-400 font-semibold mt-0.5">
              Chiều cao: {measurements[0] ? `${measurements[0].height} cm` : "67 cm"}
            </p>
          </div>
        </div>
      </div>

      {/* 3. Category Filter Tabs */}
      <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-5 space-y-4">
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
            Hiển thị: <span className="text-[#1c648e] font-black">{finalFilteredLogs.length}</span> ghi chép ({timeRangeLabel[timeRange]})
          </span>
        </div>
      </div>

      {/* 4. Main Timeline Stream with Date Headers */}
      <div className="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px] p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 className="text-primary font-bold text-sm tracking-tight flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#1c648e]" />
            Dòng thời gian chi tiết
          </h3>
          <span className="text-xs font-bold text-[#1c648e] bg-sky-50 border border-sky-100 px-3 py-1 rounded-lg">
            Mốc thời gian: {timeRangeLabel[timeRange]}
          </span>
        </div>

        <div className="relative pl-6 border-l-2 border-sky-100 space-y-6">
          {finalFilteredLogs.length === 0 ? (
            <div className="text-center py-10 text-slate-400 space-y-2">
              <Calendar className="w-8 h-8 text-slate-300 mx-auto" />
              <p className="text-xs font-semibold">Chưa có ghi chép nào trong danh mục này ({timeRangeLabel[timeRange]}).</p>
            </div>
          ) : (
            finalFilteredLogs.map((log) => {
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
                          <span className="text-[9px] font-bold text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
                            {log.date === "Today" ? "Hôm nay" : log.date === "Yesterday" ? "Hôm qua" : log.date}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 font-medium leading-relaxed">{log.details}</p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between sm:justify-end gap-3 shrink-0 border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-100">
                      {log.amountStr && (
                        <span className="text-xs font-black text-slate-700 bg-slate-100 px-3 py-1 rounded-xl">
                          {log.amountStr}
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
