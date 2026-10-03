"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  CheckCircle2, 
  AlertCircle, 
  ExternalLink, 
  Terminal, 
  Eye, 
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { Button } from "@/components/ui/Button";

interface VerificationRecord {
  id: string;
  actionTitle: string;
  actionId: string;
  targetService: string;
  executionStatus: "SUCCESS" | "FAILED";
  executionDetails: string;
  observationDetails: string;
  evidenceChecks: { check: string; passed: boolean; expected?: string; observed?: string }[];
  verdict: "VERIFIED" | "NOT_VERIFIED";
  timestamp: string;
  externalRef: string;
  rawPayload?: string;
}

export default function VerificationPage() {
  const [selectedRecordId, setSelectedRecordId] = useState<string>("verif-01");
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  const records: VerificationRecord[] = [
    {
      id: "verif-01",
      actionTitle: "Publish Sprint Milestone to GitHub Issues",
      actionId: "act-gh-42",
      targetService: "GitHub · acme/nexus",
      executionStatus: "SUCCESS",
      executionDetails: "Request accepted · HTTP 201 Created in 142ms",
      observationDetails: "Issue #42 found on remote repository through independent read poll",
      evidenceChecks: [
        { check: "Repository matches acme/nexus", passed: true },
        { check: "Issue number #42 exists on remote repository", passed: true },
        { check: "Remote title matches 'Publish Sprint Milestone'", passed: true },
        { check: "Payload SHA-256 matches action synthesis", passed: true },
      ],
      verdict: "VERIFIED",
      timestamp: "Today, 18:24 UTC",
      externalRef: "https://github.com/acme/nexus/issues/42",
      rawPayload: JSON.stringify({
        id: 42,
        number: 42,
        title: "Publish Sprint Milestone",
        state: "open",
        sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      }, null, 2),
    },
    {
      id: "verif-02",
      actionTitle: "Schedule Sprint Verification in Google Calendar",
      actionId: "act-cal-88",
      targetService: "Google Calendar",
      executionStatus: "SUCCESS",
      executionDetails: "Request accepted · HTTP 200 OK in 98ms",
      observationDetails: "Event evt_98243 found with matching attendee invitations",
      evidenceChecks: [
        { check: "Calendar confirmed in primary workspace", passed: true },
        { check: "Time slot within requested 30-min window", passed: true },
        { check: "Invited security reviewer accounts present", passed: true },
      ],
      verdict: "VERIFIED",
      timestamp: "Today, 16:10 UTC",
      externalRef: "https://calendar.google.com/event?id=evt_98243",
      rawPayload: JSON.stringify({
        id: "evt_98243",
        status: "confirmed",
        summary: "Sprint Verification Session",
        attendees: ["sec-lead@nexus.internal"]
      }, null, 2),
    },
    {
      id: "verif-03",
      actionTitle: "Sync Security Policy to Webhook Gateway",
      actionId: "act-hook-12",
      targetService: "Webhook Perimeter",
      executionStatus: "SUCCESS",
      executionDetails: "Request accepted · HTTP 200 OK received from edge proxy",
      observationDetails: "Target edge proxy returned older configuration version in live audit probe",
      evidenceChecks: [
        { check: "HTTP 200 acknowledgment received", passed: true },
        { 
          check: "Configuration version check", 
          passed: false,
          expected: "v2.4",
          observed: "v2.3"
        },
        { 
          check: "Cryptographic configuration hash verified", 
          passed: false,
          expected: "sha256:7f83b165...",
          observed: "sha256:1a84f932..."
        },
      ],
      verdict: "NOT_VERIFIED",
      timestamp: "Yesterday, 22:45 UTC",
      externalRef: "https://edge-proxy.internal/audit/1209",
      rawPayload: JSON.stringify({
        status: "mismatch_detected",
        current_version: "v2.3",
        dispatched_version: "v2.4",
        divergence_reason: "Worker process delayed config reload"
      }, null, 2),
    },
  ];

  const selectedRecord = records.find(r => r.id === selectedRecordId) || records[0];
  const isVerified = selectedRecord.verdict === "VERIFIED";

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Editorial Header */}
      <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-4 border-b border-[#ECECE9] pb-6">
        <div>
          <span className="text-xs font-mono font-medium text-[#2563EB] tracking-wider uppercase">
            Forensic Truth
          </span>
          <h1 className="font-display text-4xl sm:text-5xl text-[#171717] mt-1.5">
            Verification
          </h1>
          <p className="text-base text-[#5F6368] mt-2">
            Independent proof comparing execution intent against observed external reality.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/execution">
            <Button variant="secondary" size="md">
              <Terminal className="w-4 h-4 mr-2" />
              Execution Surface
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column (5 cols): Audit Records Stream */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-[#ECECE9]">
            <span className="text-sm font-semibold text-[#171717]">
              Proof Stream
            </span>
            <span className="text-xs font-mono text-[#5F6368]">
              {records.length} records evaluated
            </span>
          </div>

          <div className="space-y-3">
            {records.map((record) => {
              const isSelected = record.id === selectedRecordId;
              const passed = record.verdict === "VERIFIED";

              return (
                <div
                  key={record.id}
                  onClick={() => {
                    setSelectedRecordId(record.id);
                    setShowTechnicalDetails(false);
                  }}
                  className={`p-5 rounded-2xl border transition-all cursor-pointer shadow-2xs ${
                    isSelected 
                      ? "bg-white border-[#2563EB] ring-2 ring-[#EFF6FF]" 
                      : "bg-white border-[#E5E7EB] hover:border-[#D1D5DB]"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono text-[#5F6368]">
                      {record.targetService}
                    </span>
                    <span className={`text-xs font-mono px-2.5 py-0.5 rounded-full border font-semibold ${
                      passed
                        ? "bg-[#F0FDF4] text-[#15803D] border-[#BBF7D0]"
                        : "bg-[#FEF2F2] text-[#DC2626] border-[#FECACA]"
                    }`}>
                      {passed ? "VERIFIED" : "NOT VERIFIED"}
                    </span>
                  </div>

                  <h3 className="text-base font-medium text-[#171717] line-clamp-1">
                    {record.actionTitle}
                  </h3>

                  <div className="flex items-center justify-between text-xs text-[#8A8F98] font-mono mt-3">
                    <span>{record.actionId}</span>
                    <span>{record.timestamp}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column (7 cols): Human-Readable Evidence Story */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-white rounded-2xl border border-[#E5E7EB] p-8 shadow-2xs space-y-7">
            {/* Header info */}
            <div className="border-b border-[#ECECE9] pb-6 space-y-2">
              <div className="flex items-center gap-3">
                <span className={`w-3 h-3 rounded-full ${isVerified ? "bg-[#15803D]" : "bg-[#DC2626]"}`} />
                <span className="text-xs font-mono font-semibold tracking-wider text-[#8A8F98] uppercase">
                  {selectedRecord.targetService}
                </span>
              </div>

              <h2 className="font-display text-3xl text-[#171717]">
                {selectedRecord.actionTitle}
              </h2>

              <div className="flex items-center gap-3 text-xs text-[#5F6368] pt-1">
                <span>Action: <strong className="font-mono text-[#171717]">{selectedRecord.actionId}</strong></span>
                <span>·</span>
                <a 
                  href={selectedRecord.externalRef} 
                  target="_blank" 
                  rel="noreferrer" 
                  className="text-[#2563EB] hover:underline flex items-center gap-1 font-mono"
                >
                  Remote Target <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>

            {/* Human-Readable Evidence Progression */}
            <div className="space-y-6">
              {/* Step 1: Execution */}
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-[#F0FDF4] border border-[#BBF7D0] flex items-center justify-center text-[#15803D] shrink-0 mt-0.5">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
                <div className="space-y-1 flex-1">
                  <span className="text-xs font-mono font-semibold text-[#5F6368] uppercase tracking-wide block">
                    Execution
                  </span>
                  <p className="text-base text-[#171717] font-medium">
                    {selectedRecord.executionDetails}
                  </p>
                </div>
              </div>

              {/* Step 2: Observation */}
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-[#EFF6FF] border border-[#BFDBFE] flex items-center justify-center text-[#2563EB] shrink-0 mt-0.5">
                  <Eye className="w-4 h-4" />
                </div>
                <div className="space-y-1 flex-1">
                  <span className="text-xs font-mono font-semibold text-[#5F6368] uppercase tracking-wide block">
                    Observation
                  </span>
                  <p className="text-base text-[#171717] font-medium">
                    {selectedRecord.observationDetails}
                  </p>
                </div>
              </div>

              {/* Step 3: Evidence Checklist */}
              <div className="flex items-start gap-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5 border ${
                  isVerified 
                    ? "bg-[#F0FDF4] border-[#BBF7D0] text-[#15803D]" 
                    : "bg-[#FEF2F2] border-[#FECACA] text-[#DC2626]"
                }`}>
                  {isVerified ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                </div>
                <div className="space-y-3 flex-1">
                  <span className="text-xs font-mono font-semibold text-[#5F6368] uppercase tracking-wide block">
                    Evidence Checks
                  </span>
                  <div className="space-y-2">
                    {selectedRecord.evidenceChecks.map((item, idx) => (
                      <div 
                        key={idx}
                        className={`p-3.5 rounded-xl border text-sm flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${
                          item.passed 
                            ? "bg-[#F0FDF4] border-[#BBF7D0] text-[#15803D]" 
                            : "bg-[#FEF2F2] border-[#FECACA] text-[#DC2626]"
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          {item.passed ? (
                            <CheckCircle2 className="w-4 h-4 text-[#15803D] shrink-0" />
                          ) : (
                            <AlertCircle className="w-4 h-4 text-[#DC2626] shrink-0" />
                          )}
                          <span className="text-[#171717] font-medium">{item.check}</span>
                        </div>

                        {item.expected && item.observed ? (
                          <div className="text-xs font-mono text-[#DC2626] bg-white px-2 py-1 rounded border border-[#FECACA]">
                            Expected: {item.expected} · Observed: {item.observed}
                          </div>
                        ) : (
                          <span className="text-xs font-mono font-semibold">
                            {item.passed ? "MATCH" : "MISMATCH"}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Step 4: Final Verdict Banner */}
              <div className={`p-6 rounded-2xl border space-y-2 ${
                isVerified 
                  ? "bg-[#F0FDF4] border-[#86EFAC]" 
                  : "bg-[#FEF2F2] border-[#FECACA]"
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-semibold uppercase tracking-wider text-[#5F6368]">
                    Verification Result
                  </span>
                  <span className={`text-xs font-mono font-bold px-3 py-1 rounded-full ${
                    isVerified ? "bg-[#15803D] text-white" : "bg-[#DC2626] text-white"
                  }`}>
                    {selectedRecord.verdict === "VERIFIED" ? "VERIFIED" : "NOT VERIFIED"}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-[#171717]">
                  {isVerified ? "Proof Confirmed by Independent Telemetry" : "Discrepancy Detected in External State"}
                </h3>
                <p className="text-sm text-[#5F6368] leading-relaxed">
                  {isVerified
                    ? "Execution intent matches external observed state across all forensic parameters. Outcome is cryptographically anchored."
                    : "The observed system state diverged from expected execution parameters. Action flagged for human review."}
                </p>
              </div>

              {/* Technical Forensic Detail Drawer/Collapsible */}
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                  className="text-xs font-mono text-[#2563EB] hover:text-[#1D4ED8] flex items-center gap-1.5 cursor-pointer font-medium"
                >
                  <span>{showTechnicalDetails ? "Hide technical evidence" : "Inspect technical evidence & payload"}</span>
                  {showTechnicalDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>

                {showTechnicalDetails && (
                  <div className="mt-3 p-4 rounded-xl bg-[#F7F7F5] border border-[#ECECE9] font-mono text-xs text-[#171717] overflow-x-auto">
                    <div className="text-[11px] text-[#8A8F98] mb-2">RAW TELEMETRY AUDIT RECORD:</div>
                    <pre className="whitespace-pre-wrap">{selectedRecord.rawPayload}</pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
