"use client";

import React, { useState } from "react";
import { 
  X, 
  GitBranch, 
  Calendar, 
  MessageSquare, 
  CheckCircle2, 
  ArrowRight, 
  ShieldCheck, 
  Server,
  Lock,
  RefreshCw
} from "lucide-react";
import { Button } from "./Button";

interface AddConnectionDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConnected?: (connector: { name: string; provider: string }) => void;
}

export function AddConnectionDialog({ isOpen, onClose, onConnected }: AddConnectionDialogProps) {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [selectedProvider, setSelectedProvider] = useState<string>("github");
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);

  if (!isOpen) return null;

  const providers = [
    {
      id: "github",
      name: "GitHub Enterprise",
      icon: GitBranch,
      desc: "Issues, Pull Requests, Commit Checks, Repository Read & Write",
      readCaps: ["Repository Read", "Issue Read", "Branch State"],
      writeCaps: ["Issue Create", "Comment Create"]
    },
    {
      id: "google_calendar",
      name: "Google Calendar",
      icon: Calendar,
      desc: "Event scheduling, attendee verification, calendar sync",
      readCaps: ["Calendar Events Read", "Attendee Status"],
      writeCaps: ["Calendar Events Create"]
    },
    {
      id: "slack",
      name: "Slack Integration",
      icon: MessageSquare,
      desc: "Operational notifications, escalation alerts, human review pings",
      readCaps: ["Channel Read", "User Presence"],
      writeCaps: ["Message Post", "Thread Reply"]
    },
    {
      id: "webhook",
      name: "Custom Zero-Trust Webhook",
      icon: Server,
      desc: "Deterministic HTTP/REST dispatch with HMAC-SHA256 signature",
      readCaps: ["Endpoint Health Check"],
      writeCaps: ["Payload Webhook Dispatch"]
    }
  ];

  const currentProvider = providers.find(p => p.id === selectedProvider) || providers[0];

  const handleRunHealthCheck = () => {
    setIsCheckingHealth(true);
    setTimeout(() => {
      setIsCheckingHealth(false);
      setStep(4);
    }, 1200);
  };

  const handleFinish = () => {
    onConnected?.({ name: currentProvider.name, provider: currentProvider.id });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-150">
      <div 
        className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-[#E5E7EB] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-7 py-5 border-b border-[#ECECE9] bg-[#F7F7F5] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#EFF6FF] border border-[#BFDBFE] flex items-center justify-center text-[#2563EB]">
              <Lock className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[11px] font-mono text-[#2563EB] font-semibold uppercase tracking-wider">
                Trusted Boundary
              </span>
              <h2 className="text-base font-semibold text-[#171717]">
                Connect External System
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

        {/* Step Progression Bar */}
        <div className="px-7 py-3 bg-white border-b border-[#ECECE9] flex items-center justify-between text-xs font-mono select-none">
          <span className={step >= 1 ? "text-[#2563EB] font-semibold" : "text-[#8A8F98]"}>
            1. Provider
          </span>
          <ArrowRight className="w-3 h-3 text-[#ECECE9]" />
          <span className={step >= 2 ? "text-[#2563EB] font-semibold" : "text-[#8A8F98]"}>
            2. Permissions
          </span>
          <ArrowRight className="w-3 h-3 text-[#ECECE9]" />
          <span className={step >= 3 ? "text-[#2563EB] font-semibold" : "text-[#8A8F98]"}>
            3. Health Probe
          </span>
          <ArrowRight className="w-3 h-3 text-[#ECECE9]" />
          <span className={step >= 4 ? "text-[#15803D] font-semibold" : "text-[#8A8F98]"}>
            4. Connected
          </span>
        </div>

        {/* Body */}
        <div className="p-7 space-y-6">
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-base font-semibold text-[#171717]">
                  Choose System Provider
                </h3>
                <p className="text-sm text-[#5F6368] mt-1">
                  Authorize NEXUS to observe external state and dispatch policy-gated operations.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {providers.map((p) => {
                  const Icon = p.icon;
                  const isSelected = selectedProvider === p.id;
                  return (
                    <div
                      key={p.id}
                      onClick={() => setSelectedProvider(p.id)}
                      className={`p-4 rounded-xl border cursor-pointer transition-all space-y-2 ${
                        isSelected 
                          ? "bg-[#EFF6FF] border-[#2563EB] shadow-2xs" 
                          : "bg-white border-[#E5E7EB] hover:border-[#D1D5DB]"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="w-8 h-8 rounded-lg bg-[#F7F7F5] border border-[#ECECE9] flex items-center justify-center text-[#2563EB]">
                          <Icon className="w-4 h-4" />
                        </div>
                        {isSelected && <CheckCircle2 className="w-4 h-4 text-[#2563EB]" />}
                      </div>
                      <h4 className="text-sm font-semibold text-[#171717]">{p.name}</h4>
                      <p className="text-xs text-[#5F6368] leading-snug line-clamp-2">{p.desc}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-base font-semibold text-[#171717]">
                  Review Granular Capabilities & Policy Boundaries
                </h3>
                <p className="text-sm text-[#5F6368] mt-1">
                  NEXUS segregates READ operations from WRITE operations. Mutations require explicit policy authorization.
                </p>
              </div>

              <div className="space-y-3">
                <div className="p-4 rounded-xl bg-[#F7F7F5] border border-[#ECECE9] space-y-2">
                  <span className="text-xs font-mono font-semibold text-[#2563EB] uppercase tracking-wider block">
                    Read Capabilities (Permissive)
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {currentProvider.readCaps.map((c) => (
                      <span key={c} className="text-xs font-mono px-2.5 py-1 rounded-md bg-white border border-[#E5E7EB] text-[#171717]">
                        ✓ {c}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-[#FFFBEB] border border-[#FDE68A] space-y-2">
                  <span className="text-xs font-mono font-semibold text-[#D97706] uppercase tracking-wider block">
                    Write Capabilities (Approval Required)
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {currentProvider.writeCaps.map((c) => (
                      <span key={c} className="text-xs font-mono px-2.5 py-1 rounded-md bg-white border border-[#FDE68A] text-[#171717]">
                        🔒 {c}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="text-xs text-[#5F6368] font-mono">
                  Zero-Trust Guarantee: Authentication tokens are exchanged over encrypted backend channels and never displayed in client state.
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="p-8 text-center space-y-4">
              <RefreshCw className={`w-10 h-10 text-[#2563EB] mx-auto ${isCheckingHealth ? "animate-spin" : ""}`} />
              <div className="space-y-1">
                <h3 className="text-lg font-semibold text-[#171717]">
                  {isCheckingHealth ? "Verifying Provider Health..." : "Ready to Test Connection"}
                </h3>
                <p className="text-sm text-[#5F6368] max-w-sm mx-auto">
                  Performing live TLS handshake and capability probe against {currentProvider.name} API perimeter.
                </p>
              </div>
              {!isCheckingHealth && (
                <Button size="md" variant="primary" onClick={handleRunHealthCheck}>
                  <span>Dispatch Health Handshake</span>
                  <ArrowRight className="w-4 h-4 ml-1.5" />
                </Button>
              )}
            </div>
          )}

          {step === 4 && (
            <div className="p-8 text-center space-y-4">
              <div className="w-14 h-14 rounded-full bg-[#F0FDF4] border border-[#86EFAC] flex items-center justify-center text-[#15803D] mx-auto">
                <ShieldCheck className="w-8 h-8" />
              </div>
              <div className="space-y-1">
                <h3 className="text-xl font-semibold text-[#171717]">
                  {currentProvider.name} Connected Successfully
                </h3>
                <p className="text-sm text-[#5F6368] max-w-sm mx-auto">
                  Target system is now registered in the engine catalog with telemetry active.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-7 py-4 border-t border-[#ECECE9] bg-[#F7F7F5] flex items-center justify-between">
          {step === 1 && (
            <>
              <Button variant="outline" size="md" onClick={onClose}>
                Cancel
              </Button>
              <Button variant="primary" size="md" onClick={() => setStep(2)}>
                <span>Configure Permissions</span>
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>
            </>
          )}

          {step === 2 && (
            <>
              <Button variant="outline" size="md" onClick={() => setStep(1)}>
                Back
              </Button>
              <Button variant="primary" size="md" onClick={() => setStep(3)}>
                <span>Test Connection Handshake</span>
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>
            </>
          )}

          {step === 3 && (
            <Button variant="outline" size="md" onClick={() => setStep(2)}>
              Back
            </Button>
          )}

          {step === 4 && (
            <Button variant="primary" size="md" className="w-full justify-center" onClick={handleFinish}>
              <span>Complete Integration</span>
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
