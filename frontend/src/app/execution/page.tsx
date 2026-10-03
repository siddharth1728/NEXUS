"use client";

import React, { useState } from "react";
import Link from "next/link";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { 
  ShieldCheck, 
  CheckCircle2, 
  Check, 
  X, 
  Clock, 
  ArrowRight,
  Lock
} from "lucide-react";

interface ExecutionTask {
  id: string;
  operation: string;
  target: string;
  title: string;
  capability: string;
  policy: string;
  expectedEffect: string;
  parameters: Record<string, string>;
  status: "READY" | "AWAITING_APPROVAL" | "AUTHORIZED" | "RUNNING" | "SUCCEEDED" | "VERIFIED" | "REJECTED";
  stepStatus?: string;
  responsePayload?: string;
}

export default function ExecutionPage() {
  const [tasks, setTasks] = useState<ExecutionTask[]>([
    {
      id: "exec-gh-01",
      operation: "Create GitHub Issue",
      target: "acme / nexus",
      title: "Enforce JWT authentication on API edge gateway",
      capability: "GITHUB_ISSUE_CREATE",
      policy: "Human Approval Required",
      expectedEffect: "Creates one GitHub issue in repository acme/nexus with grounded spec references.",
      parameters: {
        repository: "acme/nexus",
        title: "Enforce JWT authentication on API edge gateway",
        labels: "security, architecture",
        assignee: "security-lead",
      },
      status: "AWAITING_APPROVAL",
    },
    {
      id: "exec-cal-02",
      operation: "Schedule Calendar Event",
      target: "Google Calendar (work-calendar)",
      title: "Sprint Review & Action Verification Session",
      capability: "GOOGLE_CALENDAR_CREATE_EVENT",
      policy: "Pre-Authorized Policy",
      expectedEffect: "Invites security leads to 30-min compliance confirmation.",
      parameters: {
        calendar_id: "primary",
        event_name: "Sprint Review & Action Verification Session",
        duration: "30 minutes",
      },
      status: "VERIFIED",
      stepStatus: "Event booked (evt_98243) and verified via Calendar API",
    },
  ]);

  const handleApprove = (taskId: string) => {
    // 1. Authorized
    setTasks(prev => prev.map(t => {
      if (t.id !== taskId) return t;
      return { ...t, status: "AUTHORIZED", stepStatus: "Policy authorized · generating cryptographic dispatch token" };
    }));

    // 2. Running
    setTimeout(() => {
      setTasks(prev => prev.map(t => {
        if (t.id !== taskId) return t;
        return { ...t, status: "RUNNING", stepStatus: "Connector in flight: POST https://api.github.com/repos/acme/nexus/issues" };
      }));
    }, 900);

    // 3. Succeeded
    setTimeout(() => {
      setTasks(prev => prev.map(t => {
        if (t.id !== taskId) return t;
        return { 
          ...t, 
          status: "SUCCEEDED", 
          stepStatus: "GitHub responded HTTP 201 Created · Issue #43 generated",
          responsePayload: '{"id": 43, "html_url": "https://github.com/acme/nexus/issues/43", "state": "open"}'
        };
      }));
    }, 2000);

    // 4. Verified
    setTimeout(() => {
      setTasks(prev => prev.map(t => {
        if (t.id !== taskId) return t;
        return { 
          ...t, 
          status: "VERIFIED", 
          stepStatus: "Independent observation verified external state · SHA-256 match",
        };
      }));
    }, 3200);
  };

  const handleReject = (taskId: string) => {
    setTasks(prev => prev.map(t => {
      if (t.id !== taskId) return t;
      return { ...t, status: "REJECTED", stepStatus: "Rejected by human reviewer · Action blocked" };
    }));
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Editorial Header */}
      <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-4 border-b border-[#ECECE9] pb-6">
        <div>
          <span className="text-xs font-mono font-medium text-[#2563EB] tracking-wider uppercase">
            Control Surface
          </span>
          <h1 className="font-display text-4xl sm:text-5xl text-[#171717] mt-1.5">
            Execution
          </h1>
          <p className="text-base text-[#5F6368] mt-2">
            Calm, policy-controlled execution plane dispatching actions to connected systems.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/verification">
            <Button variant="outline" size="md">
              <ShieldCheck className="w-4 h-4 text-[#15803D] mr-2" />
              Verification Proof Log
            </Button>
          </Link>
        </div>
      </div>

      {/* Execution Lifecycle Living Line */}
      <div className="bg-white rounded-2xl border border-[#E5E7EB] p-6 shadow-2xs">
        <div className="flex items-center justify-between mb-4">
          <span className="text-xs font-mono font-medium text-[#5F6368]">
            EXECUTION CONTROL PIPELINE
          </span>
          <span className="text-xs font-mono text-[#15803D] flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#15803D] animate-pulse" />
            Backend Authoritative
          </span>
        </div>

        {/* Stepper bar */}
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 text-center text-xs font-mono select-none">
          {["READY", "AWAITING APPROVAL", "AUTHORIZED", "RUNNING", "SUCCEEDED", "VERIFIED"].map((stage, idx) => (
            <div key={stage} className="p-2.5 rounded-xl border border-[#ECECE9] bg-[#F7F7F5] flex flex-col items-center">
              <span className="text-[10px] text-[#8A8F98]">0{idx + 1}</span>
              <span className="font-semibold text-[#171717] mt-0.5">{stage}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Deliberate Approval Workspace */}
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-[#ECECE9] pb-3">
          <div>
            <h2 className="text-2xl font-semibold text-[#171717] tracking-tight">
              Approval Workspace
            </h2>
            <p className="text-sm text-[#5F6368] mt-0.5">
              Review and authorize operations before connector invocation.
            </p>
          </div>
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-[#EFF6FF] text-[#2563EB] font-medium border border-[#BFDBFE]">
            {tasks.filter(t => t.status === "AWAITING_APPROVAL").length} Awaiting Authorization
          </span>
        </div>

        <div className="space-y-6">
          {tasks.map((task) => {
            const isPending = task.status === "AWAITING_APPROVAL";
            const isCompleted = task.status === "VERIFIED" || task.status === "SUCCEEDED";

            return (
              <div 
                key={task.id} 
                className="bg-white rounded-2xl border border-[#E5E7EB] shadow-2xs overflow-hidden space-y-6 p-7 sm:p-8"
              >
                {/* Header Row */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-6 border-b border-[#ECECE9]">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-3">
                      <span className="font-display text-2xl text-[#171717]">
                        {task.operation}
                      </span>
                      <span className="text-xs font-mono bg-[#F7F7F5] border border-[#ECECE9] px-2.5 py-0.5 rounded-md text-[#5F6368]">
                        {task.capability}
                      </span>
                    </div>
                    <h3 className="text-base text-[#5F6368] font-normal">
                      {task.title}
                    </h3>
                  </div>

                  <StatusBadge 
                    status={isPending ? "requires_approval" : task.status.toLowerCase()} 
                    size="md" 
                  />
                </div>

                {/* Structured Context Fields: What / Where / Capability / Policy */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
                  <div className="space-y-1">
                    <span className="text-xs font-mono text-[#8A8F98] uppercase tracking-wider block">
                      Target Repository / Service
                    </span>
                    <span className="font-medium text-[#171717] font-mono text-sm">
                      {task.target}
                    </span>
                  </div>

                  <div className="space-y-1">
                    <span className="text-xs font-mono text-[#8A8F98] uppercase tracking-wider block">
                      Security Policy
                    </span>
                    <span className="text-[#7C3AED] font-medium flex items-center gap-1.5 text-sm">
                      <Lock className="w-3.5 h-3.5 text-[#7C3AED]" />
                      {task.policy}
                    </span>
                  </div>

                  <div className="space-y-1">
                    <span className="text-xs font-mono text-[#8A8F98] uppercase tracking-wider block">
                      Execution ID
                    </span>
                    <span className="text-[#5F6368] font-mono text-xs">
                      {task.id}
                    </span>
                  </div>
                </div>

                {/* Expected Effect Box */}
                <div className="p-4 rounded-xl bg-[#F7F7F5] border border-[#ECECE9] space-y-1">
                  <span className="text-xs font-mono text-[#5F6368] uppercase tracking-wider block">
                    Expected Effect
                  </span>
                  <p className="text-sm text-[#171717] leading-relaxed">
                    {task.expectedEffect}
                  </p>
                </div>

                {/* Relevant Parameters */}
                <div className="space-y-2">
                  <span className="text-xs font-mono text-[#8A8F98] uppercase tracking-wider block">
                    Relevant Parameters
                  </span>
                  <div className="p-4 rounded-xl bg-[#F7F7F5] border border-[#ECECE9] font-mono text-xs text-[#171717] space-y-1">
                    {Object.entries(task.parameters).map(([key, val]) => (
                      <div key={key} className="flex items-center gap-2">
                        <span className="text-[#5F6368]">{key}:</span>
                        <span className="font-semibold">{val}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Live Lifecycle State Progression */}
                {!isPending && (
                  <div className="p-4 rounded-xl bg-[#EFF6FF] border border-[#BFDBFE] flex items-center justify-between text-sm">
                    <div className="flex items-center gap-3 text-[#2563EB]">
                      {isCompleted ? (
                        <CheckCircle2 className="w-5 h-5 text-[#15803D]" />
                      ) : (
                        <Clock className="w-5 h-5 animate-spin text-[#2563EB]" />
                      )}
                      <span className="font-medium text-[#171717]">{task.stepStatus}</span>
                    </div>

                    {isCompleted && (
                      <Link href="/verification">
                        <Button size="sm" variant="secondary">
                          <span>Inspect Evidence</span>
                          <ArrowRight className="w-4 h-4 ml-1.5" />
                        </Button>
                      </Link>
                    )}
                  </div>
                )}

                {/* Deliberate Approval Controls */}
                {isPending && (
                  <div className="pt-4 border-t border-[#ECECE9] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <span className="text-xs text-[#5F6368]">
                      Human confirmation required. Backend validates cryptographic signature before executing.
                    </span>

                    <div className="flex items-center gap-3">
                      <Button 
                        size="md" 
                        variant="outline" 
                        onClick={() => handleReject(task.id)}
                        className="text-[#DC2626] hover:bg-[#FEF2F2] border-[#FECACA]"
                      >
                        <X className="w-4 h-4 mr-1.5" />
                        Reject Operation
                      </Button>

                      <Button 
                        size="md" 
                        variant="primary" 
                        onClick={() => handleApprove(task.id)}
                      >
                        <Check className="w-4 h-4 mr-1.5" />
                        Authorize & Execute
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
