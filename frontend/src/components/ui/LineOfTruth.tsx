"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { FileText, CheckSquare, PlayCircle, Eye, ShieldCheck, Check } from "lucide-react";

export type TruthStep = "source" | "action" | "execution" | "evidence" | "verification";

interface LineOfTruthProps {
  currentStep?: TruthStep;
  completedSteps?: TruthStep[];
  className?: string;
  sourceLabel?: string;
  actionLabel?: string;
  executionLabel?: string;
  evidenceLabel?: string;
  verificationLabel?: string;
}

export function LineOfTruth({
  currentStep = "action",
  completedSteps = ["source"],
  className,
  sourceLabel = "Source Ingested",
  actionLabel = "Action Synthesized",
  executionLabel = "Execution",
  evidenceLabel = "Evidence Observed",
  verificationLabel = "Verified",
}: LineOfTruthProps) {
  const steps: { key: TruthStep; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { key: "source", label: sourceLabel, icon: FileText },
    { key: "action", label: actionLabel, icon: CheckSquare },
    { key: "execution", label: executionLabel, icon: PlayCircle },
    { key: "evidence", label: evidenceLabel, icon: Eye },
    { key: "verification", label: verificationLabel, icon: ShieldCheck },
  ];

  const getStepState = (key: TruthStep) => {
    if (completedSteps.includes(key)) return "completed";
    if (currentStep === key) return "current";
    return "upcoming";
  };

  return (
    <div className={cn("w-full py-2 select-none", className)}>
      <div className="flex items-center w-full justify-between relative">
        {/* Dynamic Living Line behind nodes */}
        <div className="absolute left-6 right-6 top-1/2 -translate-y-1/2 h-[2px] bg-[#ECECE9] z-0">
          <div 
            className="h-full bg-[#15803D] transition-all duration-700"
            style={{
              width: `${(completedSteps.length / (steps.length - 1)) * 100}%`
            }}
          />
        </div>

        {steps.map((s) => {
          const state = getStepState(s.key);
          const Icon = s.icon;

          return (
            <div key={s.key} className="flex flex-col items-center relative z-10 group">
              <div
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 border bg-white",
                  state === "completed" && "bg-[#F0FDF4] border-[#86EFAC] text-[#15803D]",
                  state === "current" && "border-[#2563EB] text-[#2563EB] ring-4 ring-[#EFF6FF]",
                  state === "upcoming" && "border-[#E5E7EB] text-[#8A8F98]"
                )}
              >
                {state === "completed" ? (
                  <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                ) : (
                  <Icon className="w-3.5 h-3.5" />
                )}
              </div>
              <span
                className={cn(
                  "text-[12px] font-medium tracking-tight mt-1.5 transition-colors whitespace-nowrap hidden sm:block",
                  state === "completed" && "text-[#15803D] font-semibold",
                  state === "current" && "text-[#171717] font-semibold",
                  state === "upcoming" && "text-[#8A8F98]"
                )}
              >
                {s.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

