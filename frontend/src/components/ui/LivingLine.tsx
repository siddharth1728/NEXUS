"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { 
  FileText, 
  BrainCircuit, 
  CheckSquare, 
  PlayCircle, 
  Eye, 
  ShieldCheck, 
  ArrowRight
} from "lucide-react";

export type LivingLineStage = 
  | "information" 
  | "understanding" 
  | "action" 
  | "execution" 
  | "evidence" 
  | "verification" 
  | "progression";

interface LivingLineProps {
  currentStage?: LivingLineStage;
  completedStages?: LivingLineStage[];
  orientation?: "horizontal" | "vertical";
  className?: string;
  onStageClick?: (stage: LivingLineStage) => void;
  compact?: boolean;
}

export const STAGES_CONFIG: {
  key: LivingLineStage;
  name: string;
  tagline: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  { key: "information", name: "Information", tagline: "Source document", icon: FileText },
  { key: "understanding", name: "Understanding", tagline: "Extracted facts", icon: BrainCircuit },
  { key: "action", name: "Action", tagline: "Synthesized work", icon: CheckSquare },
  { key: "execution", name: "Execution", tagline: "Connector runtime", icon: PlayCircle },
  { key: "evidence", name: "Evidence", tagline: "Forensic observation", icon: Eye },
  { key: "verification", name: "Verification", tagline: "Proof of truth", icon: ShieldCheck },
  { key: "progression", name: "Progression", tagline: "Unlocked downstream", icon: ArrowRight },
];

export function LivingLine({
  currentStage = "action",
  completedStages = ["information", "understanding"],
  orientation = "horizontal",
  className,
  onStageClick,
  compact = false,
}: LivingLineProps) {
  const getStageStatus = (key: LivingLineStage) => {
    if (completedStages.includes(key)) return "completed";
    if (currentStage === key) return "active";
    return "idle";
  };

  if (orientation === "vertical") {
    return (
      <div className={cn("relative flex flex-col py-2", className)}>
        {STAGES_CONFIG.map((stage, idx) => {
          const status = getStageStatus(stage.key);
          const Icon = stage.icon;
          const isLast = idx === STAGES_CONFIG.length - 1;

          return (
            <div key={stage.key} className="flex items-start gap-4 relative group">
              {/* Connector line segment */}
              {!isLast && (
                <div 
                  className={cn(
                    "absolute left-[17px] top-[34px] w-[2px] h-[calc(100%-12px)] transition-all duration-500",
                    status === "completed" ? "bg-[#15803D]" : 
                    status === "active" ? "bg-gradient-to-b from-[#2563EB] to-[#E5E7EB]" : 
                    "bg-[#E5E7EB]"
                  )} 
                />
              )}

              {/* Node Icon Circle */}
              <button
                type="button"
                onClick={() => onStageClick?.(stage.key)}
                className={cn(
                  "relative z-10 w-9 h-9 rounded-full flex items-center justify-center transition-all duration-300 border cursor-pointer",
                  status === "completed" && "bg-[#F0FDF4] border-[#86EFAC] text-[#15803D] hover:ring-2 hover:ring-[#BBF7D0]",
                  status === "active" && "bg-white border-[#2563EB] text-[#2563EB] shadow-xs ring-4 ring-[#EFF6FF]",
                  status === "idle" && "bg-white border-[#E5E7EB] text-[#8A8F98] hover:border-[#D1D5DB] hover:text-[#171717]"
                )}
                aria-label={`Stage: ${stage.name}`}
              >
                <Icon className="w-4 h-4" />
                {status === "active" && (
                  <span className="absolute -inset-1 rounded-full border border-[#2563EB]/30 animate-ping pointer-events-none" />
                )}
              </button>

              {/* Label & Description */}
              <div className="pb-8 pt-1 flex flex-col">
                <div className="flex items-center gap-2">
                  <span className={cn(
                    "text-sm font-semibold tracking-tight transition-colors",
                    status === "completed" && "text-[#15803D]",
                    status === "active" && "text-[#171717]",
                    status === "idle" && "text-[#8A8F98]"
                  )}>
                    {stage.name}
                  </span>
                  {status === "completed" && (
                    <span className="text-[11px] font-mono px-1.5 py-0.2 bg-[#F0FDF4] text-[#15803D] rounded border border-[#BBF7D0]">
                      Proven
                    </span>
                  )}
                  {status === "active" && (
                    <span className="text-[11px] font-mono px-1.5 py-0.2 bg-[#EFF6FF] text-[#2563EB] rounded border border-[#BFDBFE]">
                      Current
                    </span>
                  )}
                </div>
                {!compact && (
                  <span className="text-xs text-[#5F6368] mt-0.5 font-normal">
                    {stage.tagline}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  // Horizontal presentation (The Living Line)
  return (
    <div className={cn("w-full py-4 select-none", className)}>
      <div className="relative flex items-center justify-between">
        {/* Living SVG connecting track */}
        <div className="absolute left-6 right-6 top-5 -translate-y-1/2 h-[2px] z-0 pointer-events-none">
          <svg className="w-full h-4 overflow-visible" preserveAspectRatio="none">
            {/* Background line */}
            <line 
              x1="0" 
              y1="2" 
              x2="100%" 
              y2="2" 
              stroke="#ECECE9" 
              strokeWidth="2" 
            />
            {/* Flowing animated dash representing live causality */}
            <line 
              x1="0" 
              y1="2" 
              x2="100%" 
              y2="2" 
              stroke="#2563EB" 
              strokeWidth="2" 
              className="living-line-flow opacity-60" 
            />
          </svg>
        </div>

        {STAGES_CONFIG.map((stage) => {
          const status = getStageStatus(stage.key);
          const Icon = stage.icon;

          return (
            <div 
              key={stage.key} 
              className="flex flex-col items-center relative z-10 group cursor-pointer"
              onClick={() => onStageClick?.(stage.key)}
            >
              <div
                className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 border bg-white",
                  status === "completed" && "bg-[#F0FDF4] border-[#86EFAC] text-[#15803D] hover:ring-3 hover:ring-[#BBF7D0]",
                  status === "active" && "border-[#2563EB] text-[#2563EB] ring-4 ring-[#EFF6FF] shadow-xs",
                  status === "idle" && "border-[#E5E7EB] text-[#8A8F98] hover:border-[#D1D5DB] hover:text-[#171717]"
                )}
              >
                <Icon className="w-4 h-4" />
                {status === "active" && (
                  <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-[#2563EB] ring-2 ring-white animate-pulse" />
                )}
              </div>

              <div className="mt-2 text-center flex flex-col items-center">
                <span
                  className={cn(
                    "text-xs font-medium tracking-tight transition-colors",
                    status === "completed" && "text-[#15803D] font-semibold",
                    status === "active" && "text-[#171717] font-semibold",
                    status === "idle" && "text-[#8A8F98]"
                  )}
                >
                  {stage.name}
                </span>
                {!compact && (
                  <span className="text-[11px] text-[#5F6368] hidden md:block max-w-[90px] leading-tight">
                    {stage.tagline}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
