"use client";

import React from "react";
import { X, FileText, ArrowDown, ExternalLink, ShieldCheck, Quote, BookOpen } from "lucide-react";
import { Button } from "./Button";

export interface ProvenanceData {
  sourceTitle: string;
  sourceType?: string;
  sourceLocation?: string; // e.g. "Page 14 / Section 3: Authentication"
  excerpt?: string;        // e.g. "...all incoming requests must be cryptographically verified against the tenant JWKS before reaching upstream handlers..."
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
    <div className="fixed inset-0 z-50 flex justify-end bg-black/20 backdrop-blur-xs animate-in fade-in duration-150">
      <div 
        className="w-full max-w-lg bg-white h-full shadow-2xl border-l border-[#E5E7EB] flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#E5E7EB] bg-[#F7F7F5]">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-[5px] bg-[#EFF6FF] border border-[#BFDBFE] flex items-center justify-center">
              <BookOpen className="w-3.5 h-3.5 text-[#2563EB]" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-[#171717]">Source Grounding & Provenance</h2>
              <p className="text-[11px] text-[#5F6368]">Traceability chain from source to action</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-1 rounded-[5px] text-[#5F6368] hover:text-[#171717] hover:bg-[#E5E7EB] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 flex-1">
          {/* Step 1: Source Origin */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-[#5F6368] flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-[#2563EB]" /> Source Document
              </span>
              {data.sourceLocation && (
                <span className="text-[11px] font-mono text-[#5F6368] bg-[#F2F2F0] px-2 py-0.5 rounded border border-[#E5E7EB]">
                  {data.sourceLocation}
                </span>
              )}
            </div>

            <div className="p-3.5 rounded-lg border border-[#E5E7EB] bg-[#F7F7F5]">
              <div className="text-sm font-medium text-[#171717] mb-1">{data.sourceTitle}</div>
              {data.excerpt ? (
                <div className="relative pl-3 mt-2 text-xs text-[#5F6368] italic border-l-2 border-[#2563EB]/40 bg-white p-2.5 rounded-[4px]">
                  &ldquo;{data.excerpt}&rdquo;
                </div>
              ) : (
                <p className="text-xs text-[#5F6368] mt-1">Direct context extracted from verified tenant repository index.</p>
              )}
            </div>
          </div>

          {/* Flow Connector */}
          <div className="flex items-center justify-center text-[#9CA3AF]">
            <ArrowDown className="w-4 h-4" />
          </div>

          {/* Step 2: Extracted Facts */}
          <div className="space-y-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#5F6368] flex items-center gap-1.5">
              <Quote className="w-3.5 h-3.5 text-[#7C3AED]" /> Grounded Facts
            </span>

            <div className="space-y-2">
              {data.extractedFacts && data.extractedFacts.length > 0 ? (
                data.extractedFacts.map((fact, idx) => (
                  <div key={idx} className="p-3 rounded-md border border-[#E5E7EB] bg-white text-xs text-[#171717] flex items-start gap-2">
                    <span className="font-mono text-[11px] text-[#2563EB] shrink-0 font-bold">F{idx + 1}</span>
                    <span>{fact}</span>
                  </div>
                ))
              ) : (
                <div className="p-3 rounded-md border border-[#E5E7EB] bg-white text-xs text-[#5F6368]">
                  Verified prerequisite constraint identified during automated ingestion.
                </div>
              )}
            </div>
          </div>

          {/* Flow Connector */}
          <div className="flex items-center justify-center text-[#9CA3AF]">
            <ArrowDown className="w-4 h-4" />
          </div>

          {/* Step 3: Derived Action */}
          <div className="space-y-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#5F6368] flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-[#17803D]" /> Derived Action
            </span>

            <div className="p-3.5 rounded-lg border border-[#BBF7D0] bg-[#F0FDF4] space-y-2">
              <div className="text-xs font-semibold text-[#17803D] uppercase tracking-wide">Synthesized Work Item</div>
              <div className="text-sm font-medium text-[#171717]">{data.derivedActionTitle}</div>
              {data.verificationEvidence && (
                <div className="pt-2 mt-2 border-t border-[#BBF7D0] text-[11px] text-[#17803D]">
                  Expected verification: <span className="font-mono">{data.verificationEvidence}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#E5E7EB] bg-[#F7F7F5] flex items-center justify-between">
          <span className="text-[11px] text-[#5F6368]">NEXUS Provenance Audit Record</span>
          <Button size="sm" variant="secondary" onClick={onClose}>
            Close Drawer
          </Button>
        </div>
      </div>
      <div className="fixed inset-0 -z-10" onClick={onClose} />
    </div>
  );
}
