"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  FileText, 
  BrainCircuit, 
  CheckSquare, 
  PlayCircle, 
  ShieldCheck, 
  X,
  Sparkles,
  BookOpen
} from "lucide-react";
import { Button } from "./Button";

export function OnboardingBanner() {
  const [dismissed, setDismissed] = useState(false);
  const [activeStep, setActiveStep] = useState(0);

  if (dismissed) return null;

  const steps = [
    {
      num: "01",
      title: "Information",
      desc: "Ingest unstructured PDF, spec, or policy",
      icon: FileText,
      color: "text-[#2563EB]"
    },
    {
      num: "02",
      title: "Context",
      desc: "Extract atomic facts and compliance constraints",
      icon: BrainCircuit,
      color: "text-[#7C3AED]"
    },
    {
      num: "03",
      title: "Action",
      desc: "Synthesize dependency-aware executable work",
      icon: CheckSquare,
      color: "text-[#2563EB]"
    },
    {
      num: "04",
      title: "Execution",
      desc: "Dispatch through zero-trust connectors with approval",
      icon: PlayCircle,
      color: "text-[#D97706]"
    },
    {
      num: "05",
      title: "Verification",
      desc: "Independently observe external state and verify proof",
      icon: ShieldCheck,
      color: "text-[#15803D]"
    },
  ];

  return (
    <div className="bg-white rounded-2xl border border-[#E5E7EB] p-6 shadow-2xs space-y-5 relative overflow-hidden transition-all">
      {/* Top Banner Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#ECECE9] pb-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#EFF6FF] border border-[#BFDBFE] flex items-center justify-center text-[#2563EB]">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-[#171717]">
              Understanding NEXUS: The Context-to-Action Engine
            </h2>
            <p className="text-xs text-[#5F6368]">
              How fragmented information becomes grounded work, safe execution, and verified external proof.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/documents">
            <Button size="sm" variant="secondary">
              <BookOpen className="w-3.5 h-3.5 mr-1.5 text-[#2563EB]" />
              Add Source
            </Button>
          </Link>
          <button
            onClick={() => setDismissed(true)}
            className="p-1 rounded-md text-[#8A8F98] hover:text-[#171717] hover:bg-[#F7F7F5] transition-colors"
            aria-label="Dismiss guide"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 5-Step Visual Loop */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
        {steps.map((s, idx) => {
          const Icon = s.icon;
          const isSelected = activeStep === idx;
          return (
            <div
              key={s.num}
              onClick={() => setActiveStep(idx)}
              className={`p-4 rounded-xl border text-left cursor-pointer transition-all ${
                isSelected 
                  ? "bg-[#F7F7F5] border-[#2563EB] shadow-2xs" 
                  : "bg-white border-[#ECECE9] hover:border-[#D1D5DB]"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-mono text-[#8A8F98] font-bold">{s.num}</span>
                <Icon className={`w-4 h-4 ${s.color}`} />
              </div>
              <h3 className="text-sm font-semibold text-[#171717] mb-1">
                {s.title}
              </h3>
              <p className="text-xs text-[#5F6368] leading-snug">
                {s.desc}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
