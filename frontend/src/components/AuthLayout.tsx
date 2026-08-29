import { Heart } from "lucide-react";
import type { ReactNode } from "react";

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: ReactNode;
}

export default function AuthLayout({ title, subtitle, children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-10 font-sans text-slate-800">
      <div className="w-full max-w-md">
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div className="w-11 h-11 rounded-2xl bg-primary flex items-center justify-center shrink-0 shadow-lg shadow-primary/20">
            <Heart className="w-5 h-5 text-white" fill="white" />
          </div>
          <div>
            <div className="text-lg font-extrabold text-slate-800 leading-tight">BabyCare AI</div>
            <div className="text-xs text-slate-400 font-medium">Guardian Dashboard</div>
          </div>
        </div>

        <div className="bg-white/70 backdrop-blur-xl border border-white/40 shadow-[0_8px_32px_rgba(0,0,0,0.06)] rounded-[32px] p-8">
          <div className="text-center mb-6">
            <h1 className="text-2xl font-extrabold text-slate-800 tracking-tight mb-1.5">{title}</h1>
            <p className="text-sm text-slate-500">{subtitle}</p>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
