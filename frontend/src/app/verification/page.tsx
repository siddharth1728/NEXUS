"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  ExternalLink, 
  ArrowDown, 
  Terminal, 
  Eye, 
  FileCheck,
  Search,
  Filter,
  Layers,
  ChevronRight
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";

interface VerificationRecord {
  id: string;
  actionTitle: string;
  actionId: string;
  targetService: string;
  executionStatus: "SUCCESS" | "FAILED";
  executionDetails: string;
  observationDetails: string;
  evidenceChecks: { check: string; passed: boolean }[];
  verdict: "VERIFIED" | "NOT_VERIFIED";
  timestamp: string;
  externalRef: string;
}

export default function VerificationPage() {
  const [selectedRecordId, setSelectedRecordId] = useState<string>("verif-01");

  const records: VerificationRecord[] = [
    {
      id: "verif-01",
      actionTitle: "Publish Sprint Milestone to GitHub Issues",
      actionId: "act-gh-42",
      targetService: "GitHub (acme/nexus)",
      executionStatus: "SUCCESS",
      executionDetails: "POST https://api.github.com/repos/acme/nexus/issues responded HTTP 201 Created in 142ms",
      observationDetails: "GET https://api.github.com/repos/acme/nexus/issues/42 observed active issue state in independent read poll",
      evidenceChecks: [
        { check: "Target repository equals 'acme/nexus'", passed: true },
        { check: "Issue number #42 exists on remote repository", passed: true },
        { check: "Remote title matches 'Publish Sprint Milestone'", passed: true },
        { check: "Payload SHA256 digest matches local action synthesis", passed: true },
      ],
      verdict: "VERIFIED",
      timestamp: "Today, 18:24 UTC",
      externalRef: "https://github.com/acme/nexus/issues/42",
    },
    {
      id: "verif-02",
      actionTitle: "Schedule Sprint Verification in Google Calendar",
      actionId: "act-cal-88",
      targetService: "Google Calendar",
      executionStatus: "SUCCESS",
      executionDetails: "POST https://www.googleapis.com/calendar/v3/calendars/primary/events responded HTTP 200",
      observationDetails: "GET /events/evt_98243 observed confirmed attendee status",
      evidenceChecks: [
        { check: "Calendar ID confirmed in primary account", passed: true },
        { check: "Start timestamp within requested 30-min window", passed: true },
        { check: "Invited security reviewer accounts present", passed: true },
      ],
      verdict: "VERIFIED",
      timestamp: "Today, 16:10 UTC",
      externalRef: "calendar.google.com/event?id=evt_98243",
    },
    {
      id: "verif-03",
      actionTitle: "Sync Security Policy to Webhook Gateway",
      actionId: "act-hook-12",
      targetService: "Webhook Perimeter",
      executionStatus: "SUCCESS",
      executionDetails: "POST https://edge-proxy.internal/v1/reload responded HTTP 200",
      observationDetails: "GET https://edge-proxy.internal/v1/config responded with older configuration version",
      evidenceChecks: [
        { check: "HTTP 200 acknowledgment received", passed: true },
        { check: "Observed version matches dispatched version v2.4", passed: false },
        { check: "Cryptographic configuration hash verified on edge", passed: false },
      ],
      verdict: "NOT_VERIFIED",
      timestamp: "Yesterday, 22:45 UTC",
      externalRef: "edge-proxy.internal/audit/1209",
    },
  ];

  const selectedRecord = records.find(r => r.id === selectedRecordId) || records[0];

  return (
    <div className="space-y-8 animate-in fade-in duration-150">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#E5E7EB] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-[#171717]">
              Verification Evidence Engine
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#F0FDF4] text-[#17803D] font-semibold border border-[#86EFAC]">
              Independent Grounding
            </span>
          </div>
          <p className="text-xs text-[#5F6368] mt-1">
            Forensic outcome verification comparing dispatch intent against independent external observations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/execution">
            <Button variant="secondary" size="sm">
              <Terminal className="w-3.5 h-3.5" />
              Execution Control Center
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (5 cols): Verification Stream */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#5F6368]">
              Verification Audit Stream
            </span>
            <span className="text-xs font-mono text-[#5F6368]">
              {records.length} Recorded
            </span>
          </div>

          <div className="bg-white rounded-lg border border-[#E5E7EB] divide-y divide-[#E5E7EB] overflow-hidden shadow-xs">
            {records.map((record) => {
              const isSelected = record.id === selectedRecordId;
              const isVerified = record.verdict === "VERIFIED";

              return (
                <div
                  key={record.id}
                  onClick={() => setSelectedRecordId(record.id)}
                  className={`p-4 transition-colors cursor-pointer ${
                    isSelected ? "bg-[#EFF6FF] border-l-2 border-l-[#2563EB]" : "hover:bg-[#F7F7F5]"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-[10px] text-[#5F6368] uppercase font-semibold">
                      {record.targetService}
                    </span>
                    <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded border font-semibold ${
                      isVerified
                        ? "bg-[#F0FDF4] text-[#17803D] border-[#BBF7D0]"
                        : "bg-[#FEF2F2] text-[#C62828] border-[#FECACA]"
                    }`}>
                      {record.verdict}
                    </span>
                  </div>

                  <div className="text-xs font-semibold text-[#171717] line-clamp-1">
                    {record.actionTitle}
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-[#5F6368] mt-2">
                    <span className="font-mono">{record.actionId}</span>
                    <span>{record.timestamp}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column (7 cols): Vertical Evidence Timeline */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#5F6368]">
              Vertical Evidence Timeline
            </span>
            <span className="text-[11px] font-mono text-[#5F6368]">
              Audit ID: {selectedRecord.id}
            </span>
          </div>

          <div className="bg-white rounded-lg border border-[#E5E7EB] p-6 shadow-xs space-y-6">
            {/* Header info */}
            <div className="border-b border-[#E5E7EB] pb-4">
              <span className="text-[10px] font-mono uppercase tracking-wider text-[#5F6368]">
                VERIFIED ACTION ITEM
              </span>
              <h2 className="text-base font-bold text-[#171717] mt-0.5">
                {selectedRecord.actionTitle}
              </h2>
              <div className="flex items-center gap-3 text-xs text-[#5F6368] mt-1.5">
                <span>Target: <strong className="text-[#171717] font-mono">{selectedRecord.targetService}</strong></span>
                <span>•</span>
                <a 
                  href={selectedRecord.externalRef} 
                  target="_blank" 
                  rel="noreferrer" 
                  className="text-[#2563EB] hover:underline flex items-center gap-1 font-mono"
                >
                  Remote Target <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>

            {/* Vertical Evidence Progression */}
            <div className="relative pl-6 space-y-6 border-l-2 border-[#E5E7EB]">
              {/* Step 1: Execution */}
              <div className="relative">
                <div className="absolute -left-[31px] top-0 w-5 h-5 rounded-full bg-white border-2 border-[#17803D] flex items-center justify-center">
                  <CheckCircle2 className="w-3 h-3 text-[#17803D]" />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[#171717] tracking-wider uppercase font-mono">
                      1. Execution
                    </span>
                    <span className="text-[10px] font-mono text-[#17803D] bg-[#F0FDF4] px-1.5 py-0.2 rounded border border-[#BBF7D0]">
                      HTTP 200 OK
                    </span>
                  </div>
                  <p className="text-xs text-[#5F6368] font-mono bg-[#F7F7F5] p-2.5 rounded border border-[#E5E7EB]">
                    {selectedRecord.executionDetails}
                  </p>
                </div>
              </div>

              {/* Step 2: Observation */}
              <div className="relative">
                <div className="absolute -left-[31px] top-0 w-5 h-5 rounded-full bg-white border-2 border-[#2563EB] flex items-center justify-center">
                  <Eye className="w-3 h-3 text-[#2563EB]" />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[#171717] tracking-wider uppercase font-mono">
                      2. Independent Observation
                    </span>
                    <span className="text-[10px] font-mono text-[#2563EB] bg-[#EFF6FF] px-1.5 py-0.2 rounded border border-[#BFDBFE]">
                      Observer Polled
                    </span>
                  </div>
                  <p className="text-xs text-[#5F6368] font-mono bg-[#F7F7F5] p-2.5 rounded border border-[#E5E7EB]">
                    {selectedRecord.observationDetails}
                  </p>
                </div>
              </div>

              {/* Step 3: Evidence Checks */}
              <div className="relative">
                <div className="absolute -left-[31px] top-0 w-5 h-5 rounded-full bg-white border-2 border-[#7C3AED] flex items-center justify-center">
                  <FileCheck className="w-3 h-3 text-[#7C3AED]" />
                </div>
                <div className="space-y-2">
                  <span className="text-xs font-bold text-[#171717] tracking-wider uppercase font-mono">
                    3. Forensic Evidence Assertions
                  </span>
                  <div className="space-y-1.5">
                    {selectedRecord.evidenceChecks.map((item, idx) => (
                      <div 
                        key={idx} 
                        className={`p-2.5 rounded-md border text-xs flex items-center justify-between ${
                          item.passed 
                            ? "bg-[#F0FDF4] border-[#BBF7D0] text-[#17803D]" 
                            : "bg-[#FEF2F2] border-[#FECACA] text-[#C62828]"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          {item.passed ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-[#17803D]" />
                          ) : (
                            <AlertCircle className="w-3.5 h-3.5 text-[#C62828]" />
                          )}
                          <span className="text-[#171717] font-medium">{item.check}</span>
                        </div>
                        <span className="font-mono text-[10px] font-bold">
                          {item.passed ? "MATCH" : "MISMATCH"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Step 4: Verification Verdict */}
              <div className="relative pt-2">
                <div className={`absolute -left-[31px] top-2 w-5 h-5 rounded-full bg-white border-2 flex items-center justify-center ${
                  selectedRecord.verdict === "VERIFIED" ? "border-[#17803D]" : "border-[#C62828]"
                }`}>
                  <ShieldCheck className={`w-3 h-3 ${
                    selectedRecord.verdict === "VERIFIED" ? "text-[#17803D]" : "text-[#C62828]"
                  }`} />
                </div>
                <div className={`p-4 rounded-lg border space-y-1 ${
                  selectedRecord.verdict === "VERIFIED" 
                    ? "bg-[#F0FDF4] border-[#86EFAC]" 
                    : "bg-[#FEF2F2] border-[#FECACA]"
                }`}>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold tracking-wider uppercase text-[#171717]">
                      4. Verification Verdict
                    </span>
                    <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
                      selectedRecord.verdict === "VERIFIED" 
                        ? "bg-[#17803D] text-white" 
                        : "bg-[#C62828] text-white"
                    }`}>
                      {selectedRecord.verdict}
                    </span>
                  </div>
                  <p className="text-xs text-[#5F6368] pt-1">
                    {selectedRecord.verdict === "VERIFIED"
                      ? "Independent telemetry confirms all assertions satisfied. Outcome is cryptographically grounded in audit ledger."
                      : "Evidence mismatch detected between dispatched payload and external observed state. Flagged for review."}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
