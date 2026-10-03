import React from "react";
import { cn } from "@/lib/utils";
import { FileText, CheckSquare, Terminal, Eye, ShieldCheck, Check } from "lucide-react";

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
  const steps: { key: TruthStep; label: string; icon: any }[] = [
    { key: "source", label: sourceLabel, icon: FileText },
    { key: "action", label: actionLabel, icon: CheckSquare },
    { key: "execution", label: executionLabel, icon: Terminal },
    { key: "evidence", label: evidenceLabel, icon: Eye },
    { key: "verification", label: verificationLabel, icon: ShieldCheck },
  ];

  const getStepState = (key: TruthStep) => {
    if (completedSteps.includes(key)) return "completed";
    if (currentStep === key) return "current";
    return "upcoming";
  };

  return (
    <div className={cn("flex items-center w-full py-2", className)}>
      <div className="flex items-center w-full justify-between relative">
        {/* Continuous connector line behind */}
        <div className="absolute left-4 right-4 top-1/2 -translate-y-1/2 h-[1px] bg-[#E5E7EB] z-0" />

        {steps.map((s, index) => {
          const state = getStepState(s.key);
          const Icon = s.icon;

          return (
            <div key={s.key} className="flex flex-col items-center relative z-10 group">
              <div
                className={cn(
                  "w-7 h-7 rounded-full flex items-center justify-center transition-all border",
                  state === "completed" && "bg-[#F0FDF4] border-[#86EFAC] text-[#17803D]",
                  state === "current" && "bg-[#EFF6FF] border-[#2563EB] text-[#2563EB] ring-2 ring-[#EFF6FF]",
                  state === "upcoming" && "bg-white border-[#E5E7EB] text-[#9CA3AF]"
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
                  "text-[10px] font-medium tracking-tight mt-1.5 whitespace-nowrap",
                  state === "completed" && "text-[#17803D]",
                  state === "current" && "text-[#2563EB] font-semibold",
                  state === "upcoming" && "text-[#9CA3AF]"
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
