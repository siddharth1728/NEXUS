"use client";

import React, { useState } from "react";
import { 
  X, 
  FileText, 
  CheckSquare, 
  ArrowRight, 
  CheckCircle2, 
  AlertTriangle,
  BrainCircuit
} from "lucide-react";
import { Button } from "./Button";
import { StatusBadge } from "./StatusBadge";

interface ActionCreationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onActionCreated?: (action: { title: string; source: string; requirement: string }) => void;
}

export function ActionCreationDialog({ isOpen, onClose, onActionCreated }: ActionCreationDialogProps) {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [selectedSource, setSelectedSource] = useState("Architecture_Guidelines_v2.pdf");
  const [detectedRequirement, setDetectedRequirement] = useState("All incoming client requests must undergo token authentication and cryptographic verification.");
  const [actionTitle, setActionTitle] = useState("Configure JWKS signature validation on edge ingress");
  const [actionPriority, setActionPriority] = useState("P1");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleComplete = () => {
    setIsSubmitting(true);
    setTimeout(() => {
      onActionCreated?.({
        title: actionTitle,
        source: selectedSource,
        requirement: detectedRequirement,
      });
      setIsSubmitting(false);
      onClose();
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-150">
      <div 
        className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-[#E5E7EB] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-7 py-5 border-b border-[#ECECE9] bg-[#F7F7F5] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#EFF6FF] border border-[#BFDBFE] flex items-center justify-center text-[#2563EB]">
              <BrainCircuit className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[11px] font-mono text-[#2563EB] font-semibold uppercase tracking-wider">
                Action Synthesis
              </span>
              <h2 className="text-base font-semibold text-[#171717]">
                Derive Action from Grounded Context
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-[#8A8F98] hover:text-[#171717] hover:bg-[#ECECE9]"
            aria-label="Close dialog"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Step Progression Track */}
        <div className="px-7 py-3 bg-white border-b border-[#ECECE9] flex items-center justify-between text-xs font-mono select-none">
          <span className={step >= 1 ? "text-[#2563EB] font-semibold" : "text-[#8A8F98]"}>
            1. Source Document
          </span>
          <ArrowRight className="w-3 h-3 text-[#ECECE9]" />
          <span className={step >= 2 ? "text-[#2563EB] font-semibold" : "text-[#8A8F98]"}>
            2. Detected Requirement
          </span>
          <ArrowRight className="w-3 h-3 text-[#ECECE9]" />
          <span className={step >= 3 ? "text-[#2563EB] font-semibold" : "text-[#8A8F98]"}>
            3. Action Review
          </span>
        </div>

        {/* Modal Body */}
        <div className="p-7 space-y-6">
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-base font-semibold text-[#171717]">
                  Select Grounded Source Intelligence
                </h3>
                <p className="text-sm text-[#5F6368] mt-1">
                  NEXUS will ground the synthesized work directly to verified text excerpts within this source.
                </p>
              </div>

              <div className="space-y-2.5">
                {[
                  { name: "Architecture_Guidelines_v2.pdf", meta: "18 facts · 7 requirements" },
                  { name: "Zero-Trust_Security_Perimeter.docx", meta: "24 facts · 11 requirements" },
                  { name: "Connector_Integration_Protocols.md", meta: "12 facts · 4 requirements" },
                ].map((doc) => (
                  <div
                    key={doc.name}
                    onClick={() => setSelectedSource(doc.name)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                      selectedSource === doc.name
                        ? "bg-[#EFF6FF] border-[#2563EB] shadow-2xs"
                        : "bg-white border-[#E5E7EB] hover:border-[#D1D5DB]"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="w-4 h-4 text-[#2563EB]" />
                      <div>
                        <span className="text-sm font-medium text-[#171717]">{doc.name}</span>
                        <span className="text-xs font-mono text-[#5F6368] block mt-0.5">{doc.meta}</span>
                      </div>
                    </div>
                    {selectedSource === doc.name && (
                      <CheckCircle2 className="w-4 h-4 text-[#2563EB]" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-base font-semibold text-[#171717]">
                  Detected Requirement & Epistemic Origin
                </h3>
                <p className="text-sm text-[#5F6368] mt-1">
                  Extracted policy constraint identified by automated ingestion. Review before creating actionable work.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#F7F7F5] border border-[#ECECE9] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-[#5F6368]">
                    Source: {selectedSource}
                  </span>
                  <StatusBadge status="inferred" size="sm" />
                </div>
                <textarea
                  value={detectedRequirement}
                  onChange={(e) => setDetectedRequirement(e.target.value)}
                  className="w-full text-sm text-[#171717] bg-white border border-[#E5E7EB] p-3 rounded-lg focus:outline-none focus:border-[#2563EB] leading-relaxed"
                  rows={3}
                />
              </div>

              <div className="p-3 rounded-xl bg-[#FFFBEB] border border-[#FDE68A] text-xs text-[#A65F00] flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-[#D97706] shrink-0 mt-0.5" />
                <span>
                  <strong>Epistemic Transparency:</strong> This requirement was extracted via automated semantic parsing and marked as <em>Inferred</em> until confirmed by operator review.
                </span>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-base font-semibold text-[#171717]">
                  Synthesize Candidate Action
                </h3>
                <p className="text-sm text-[#5F6368] mt-1">
                  Configure operational parameters and downstream dependencies.
                </p>
              </div>

              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-mono text-[#8A8F98] uppercase tracking-wider block">
                    Action Title
                  </label>
                  <input
                    type="text"
                    value={actionTitle}
                    onChange={(e) => setActionTitle(e.target.value)}
                    className="w-full text-sm text-[#171717] bg-white border border-[#E5E7EB] p-3 rounded-xl focus:outline-none focus:border-[#2563EB]"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-mono text-[#8A8F98] uppercase tracking-wider block">
                      Priority
                    </label>
                    <select
                      value={actionPriority}
                      onChange={(e) => setActionPriority(e.target.value)}
                      className="w-full text-sm text-[#171717] bg-white border border-[#E5E7EB] p-2.5 rounded-xl focus:outline-none focus:border-[#2563EB]"
                    >
                      <option value="P1">P1 — Critical Path</option>
                      <option value="P2">P2 — Standard</option>
                      <option value="P3">P3 — Low</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-mono text-[#8A8F98] uppercase tracking-wider block">
                      Target Connector
                    </label>
                    <input
                      type="text"
                      readOnly
                      value="GitHub (acme/nexus)"
                      className="w-full text-sm text-[#171717] bg-[#F7F7F5] border border-[#ECECE9] p-2.5 rounded-xl font-mono text-xs"
                    />
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-[#F0FDF4] border border-[#BBF7D0] text-xs text-[#15803D] flex items-center justify-between">
                  <span>State upon creation:</span>
                  <StatusBadge status="ready" size="sm" />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer Controls */}
        <div className="px-7 py-4 border-t border-[#ECECE9] bg-[#F7F7F5] flex items-center justify-between">
          {step > 1 ? (
            <Button 
              variant="outline" 
              size="md" 
              onClick={() => setStep((s) => (s - 1) as 1 | 2)}
            >
              Back
            </Button>
          ) : (
            <Button variant="outline" size="md" onClick={onClose}>
              Cancel
            </Button>
          )}

          {step < 3 ? (
            <Button 
              variant="primary" 
              size="md" 
              onClick={() => setStep((s) => (s + 1) as 2 | 3)}
            >
              <span>Continue</span>
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </Button>
          ) : (
            <Button 
              variant="primary" 
              size="md" 
              onClick={handleComplete}
              disabled={isSubmitting}
            >
              <CheckSquare className="w-4 h-4 mr-1.5" />
              <span>{isSubmitting ? "Synthesizing..." : "Create Grounded Action"}</span>
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
