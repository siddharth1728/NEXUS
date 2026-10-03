"use client";

import React from "react";
import { X, FileText, CheckCircle2, Quote, ShieldCheck, Sparkles } from "lucide-react";
import { Button } from "./Button";

export interface ProvenanceData {
  sourceTitle: string;
  sourceType?: string;
  sourceLocation?: string; // e.g. "Page 14 · Section 3: Authentication"
  excerpt?: string;        // e.g. "All incoming requests must be cryptographically verified against the tenant JWKS before reaching upstream handlers."
  extractedFacts?: string[]; // e.g. ["JWT validation is required on all upstream routes", "JWKS endpoint must rotate keys hourly"]
  requirements?: string[];   // e.g. ["Zero-trust auth perimeter compliance"]
  derivedActionTitle: string;
  verificationEvidence?: string;
}

interface SourceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  data: ProvenanceData | null;
}

export function SourceDrawer({ isOpen, onClose, data }: SourceDrawerProps) {
  if (!isOpen || !data) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/30 backdrop-blur-xs animate-in fade-in duration-200">
      <div 
        className="w-full max-w-xl bg-[#F7F7F5] h-full shadow-2xl border-l border-[#E5E7EB] flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drawer Header */}
        <div className="px-8 py-6 border-b border-[#E5E7EB] bg-white flex items-start justify-between">
          <div>
            <span className="text-xs font-mono font-medium text-[#2563EB] tracking-wide">
              GROUNDED PROVENANCE
            </span>
            <h2 className="font-display text-2xl text-[#171717] mt-1">
              Why does NEXUS believe this action exists?
            </h2>
            <p className="text-sm text-[#5F6368] mt-1">
              Direct causal lineage from source intelligence to executable action.
            </p>
          </div>
          <button 
            onClick={onClose} 
            className="p-2 rounded-lg text-[#5F6368] hover:text-[#171717] hover:bg-[#F2F2F0] transition-colors"
            aria-label="Close drawer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Causal Stream with Living Line */}
        <div className="p-8 space-y-6 flex-1">
          {/* Step 1: The Source Document */}
          <div className="relative pl-8">
            {/* Thread line */}
            <div className="absolute left-3.5 top-6 bottom-0 w-[2px] bg-[#E5E7EB]" />
            <div className="absolute left-1.5 top-1.5 w-5 h-5 rounded-full bg-white border-2 border-[#2563EB] flex items-center justify-center">
              <span className="w-1.5 h-1.5 rounded-full bg-[#2563EB]" />
            </div>

            <div className="bg-white p-5 rounded-xl border border-[#E5E7EB] shadow-xs">
              <div className="flex items-center justify-between text-xs text-[#5F6368] mb-2 font-mono">
                <span className="flex items-center gap-1.5 font-medium text-[#171717]">
                  <FileText className="w-3.5 h-3.5 text-[#2563EB]" />
                  Source
                </span>
                {data.sourceLocation && (
                  <span className="bg-[#F7F7F5] px-2 py-0.5 rounded border border-[#ECECE9]">
                    {data.sourceLocation}
                  </span>
                )}
              </div>
              <h3 className="text-base font-semibold text-[#171717]">
                {data.sourceTitle}
              </h3>
            </div>
          </div>

          {/* Step 2: The Direct Excerpt */}
          {data.excerpt && (
            <div className="relative pl-8">
              <div className="absolute left-3.5 top-0 bottom-0 w-[2px] bg-[#E5E7EB]" />
              <div className="absolute left-1.5 top-1.5 w-5 h-5 rounded-full bg-white border-2 border-[#7C3AED] flex items-center justify-center">
                <Quote className="w-2.5 h-2.5 text-[#7C3AED]" />
              </div>

              <div className="bg-white p-5 rounded-xl border border-[#E5E7EB] shadow-xs">
                <span className="text-xs font-mono font-medium text-[#7C3AED] block mb-2">
                  Excerpt
                </span>
                <blockquote className="font-display text-lg text-[#171717] leading-relaxed italic border-l-2 border-[#7C3AED] pl-3 py-1">
                  &ldquo;{data.excerpt}&rdquo;
                </blockquote>
              </div>
            </div>
          )}

          {/* Step 3: Extracted Facts */}
          <div className="relative pl-8">
            <div className="absolute left-3.5 top-0 bottom-0 w-[2px] bg-[#E5E7EB]" />
            <div className="absolute left-1.5 top-1.5 w-5 h-5 rounded-full bg-white border-2 border-[#D97706] flex items-center justify-center">
              <Sparkles className="w-2.5 h-2.5 text-[#D97706]" />
            </div>

            <div className="bg-white p-5 rounded-xl border border-[#E5E7EB] shadow-xs space-y-3">
              <span className="text-xs font-mono font-medium text-[#D97706] block">
                Extracted Facts
              </span>
              <div className="space-y-2">
                {data.extractedFacts && data.extractedFacts.length > 0 ? (
                  data.extractedFacts.map((fact, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 text-sm text-[#171717] leading-snug">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#D97706] shrink-0 mt-2" />
                      <span>{fact}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-[#5F6368]">
                    Verified policy constraints derived from repository specifications.
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Step 4: Derived Requirements (if present) */}
          {data.requirements && data.requirements.length > 0 && (
            <div className="relative pl-8">
              <div className="absolute left-3.5 top-0 bottom-0 w-[2px] bg-[#E5E7EB]" />
              <div className="absolute left-1.5 top-1.5 w-5 h-5 rounded-full bg-white border-2 border-[#15803D] flex items-center justify-center">
                <CheckCircle2 className="w-2.5 h-2.5 text-[#15803D]" />
              </div>

              <div className="bg-white p-5 rounded-xl border border-[#E5E7EB] shadow-xs">
                <span className="text-xs font-mono font-medium text-[#15803D] block mb-2">
                  Derived Requirement
                </span>
                <ul className="space-y-1.5">
                  {data.requirements.map((req, idx) => (
                    <li key={idx} className="text-sm text-[#171717] flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#15803D]" />
                      <span>{req}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Step 5: The Synthesized Action */}
          <div className="relative pl-8">
            <div className="absolute left-1.5 top-1.5 w-5 h-5 rounded-full bg-[#15803D] text-white flex items-center justify-center shadow-xs">
              <ShieldCheck className="w-3 h-3" />
            </div>

            <div className="bg-[#F0FDF4] p-5 rounded-xl border border-[#BBF7D0] shadow-xs space-y-2">
              <span className="text-xs font-mono font-semibold text-[#15803D] block">
                Derived Action
              </span>
              <h4 className="text-base font-semibold text-[#171717]">
                {data.derivedActionTitle}
              </h4>
              {data.verificationEvidence && (
                <div className="pt-3 border-t border-[#BBF7D0] text-xs text-[#15803D] flex items-center gap-1.5">
                  <span className="font-semibold">Expected Proof:</span>
                  <span className="font-mono bg-white/80 px-2 py-0.5 rounded border border-[#86EFAC]">
                    {data.verificationEvidence}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Drawer Footer */}
        <div className="px-8 py-5 border-t border-[#E5E7EB] bg-white flex items-center justify-between">
          <span className="text-xs font-mono text-[#5F6368]">
            Tamper-evident source provenance
          </span>
          <Button variant="secondary" onClick={onClose}>
            Done
          </Button>
        </div>
      </div>
    </div>
  );
}
