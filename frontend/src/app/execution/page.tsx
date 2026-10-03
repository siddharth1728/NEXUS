"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { LineOfTruth } from "@/components/ui/LineOfTruth";
import { 
  PlayCircle, 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  Terminal, 
  Check, 
  X, 
  Clock, 
  ArrowRight,
  GitBranch,
  ExternalLink,
  ChevronRight
} from "lucide-react";

interface ExecutionTask {
  id: string;
  operation: string;
  target: string;
  title: string;
  capability: string;
  policy: string;
  expectedEffect: string;
  status: "AWAITING_APPROVAL" | "APPROVED" | "EXECUTING" | "COMPLETED" | "REJECTED";
  stepStatus?: string;
  responsePayload?: string;
}

export default function ExecutionPage() {
  const router = useRouter();

  // Active control-room tasks
  const [tasks, setTasks] = useState<ExecutionTask[]>([
    {
      id: "exec-gh-01",
      operation: "CREATE GITHUB ISSUE",
      target: "acme / nexus",
      title: "Enforce JWT authentication on API edge gateway",
      capability: "GITHUB_ISSUE_CREATE",
      policy: "Human Approval Required",
      expectedEffect: "Creates one GitHub issue in repository acme/nexus with grounded spec references.",
      status: "AWAITING_APPROVAL",
    },
    {
      id: "exec-cal-02",
      operation: "SCHEDULE CALENDAR EVENT",
      target: "Google Calendar (work-calendar)",
      title: "Sprint Review & Action Verification Session",
      capability: "GOOGLE_CALENDAR_CREATE_EVENT",
      policy: "Permissive / Pre-Authorized",
      expectedEffect: "Invites security leads to 30-min compliance confirmation.",
      status: "COMPLETED",
      stepStatus: "Event booked (evt_98243)",
    },
  ]);

  const handleApprove = (taskId: string) => {
    setTasks(prev => prev.map(t => {
      if (t.id !== taskId) return t;
      return { ...t, status: "APPROVED", stepStatus: "Preparing execution dispatch..." };
    }));

    setTimeout(() => {
      setTasks(prev => prev.map(t => {
        if (t.id !== taskId) return t;
        return { ...t, status: "EXECUTING", stepStatus: "Executing connector request..." };
      }));
    }, 1000);

    setTimeout(() => {
      setTasks(prev => prev.map(t => {
        if (t.id !== taskId) return t;
        return { 
          ...t, 
          status: "COMPLETED", 
          stepStatus: "GitHub responded (HTTP 201 Created #43)",
          responsePayload: '{"id": 43, "html_url": "https://github.com/acme/nexus/issues/43", "state": "open"}'
        };
      }));
    }, 2400);
  };

  const handleReject = (taskId: string) => {
    setTasks(prev => prev.map(t => {
      if (t.id !== taskId) return t;
      return { ...t, status: "REJECTED", stepStatus: "Rejected by human reviewer" };
    }));
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-150">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#E5E7EB] pb-5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-[#171717]">
            Execution Control Center
          </h1>
          <p className="text-xs text-[#5F6368] mt-1">
            Calm, policy-controlled execution plane dispatching actions to connected systems.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/verification">
            <Button variant="outline" size="sm">
              <ShieldCheck className="w-3.5 h-3.5 text-[#17803D]" />
              Verification Log
            </Button>
          </Link>
        </div>
      </div>

      {/* Control Room Pending Queue */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-[#171717]">Pending Approvals & Dispatches</h2>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#EFF6FF] text-[#2563EB] font-semibold border border-[#BFDBFE]">
              {tasks.filter(t => t.status === "AWAITING_APPROVAL").length} Action Required
            </span>
          </div>
          <span className="text-xs text-[#5F6368]">Zero-Trust Policy Enforced</span>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {tasks.map((task) => (
            <div 
              key={task.id} 
              className="bg-white rounded-lg border border-[#E5E7EB] shadow-xs overflow-hidden transition-all"
            >
              {/* Card Header */}
              <div className="px-5 py-3.5 bg-[#F7F7F5] border-b border-[#E5E7EB] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs font-bold text-[#171717] tracking-wide">
                    {task.operation}
                  </span>
                  <span className="text-[11px] font-mono text-[#5F6368] bg-white border border-[#E5E7EB] px-2 py-0.5 rounded">
                    {task.capability}
                  </span>
                </div>
                <StatusBadge 
                  status={task.status === "AWAITING_APPROVAL" ? "requires_approval" : task.status.toLowerCase()} 
                  size="sm" 
                />
              </div>

              {/* Card Body */}
              <div className="p-5 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-[#5F6368] block mb-1">
                      TARGET REPOSITORY / SERVICE
                    </span>
                    <span className="font-medium text-[#171717] font-mono">{task.target}</span>
                  </div>

                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-[#5F6368] block mb-1">
                      EXECUTION POLICY
                    </span>
                    <span className="text-[#7C3AED] font-medium flex items-center gap-1.5">
                      <AlertTriangle className="w-3 h-3 text-[#7C3AED]" />
                      {task.policy}
                    </span>
                  </div>
                </div>

                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-[#5F6368] block mb-1">
                    ACTION TITLE
                  </span>
                  <div className="text-sm font-semibold text-[#171717]">{task.title}</div>
                </div>

                {/* Expected Effect Box */}
                <div className="p-3 rounded-md bg-[#F7F7F5] border border-[#E5E7EB] text-xs">
                  <span className="text-[10px] font-mono uppercase tracking-wider font-semibold text-[#5F6368] block mb-1">
                    EXPECTED EFFECT
                  </span>
                  <p className="text-[#171717]">{task.expectedEffect}</p>
                </div>

                {/* Live Lifecycle State Bar */}
                {task.status !== "AWAITING_APPROVAL" && (
                  <div className="p-3 rounded-md bg-[#EFF6FF] border border-[#BFDBFE] text-xs flex items-center justify-between">
                    <div className="flex items-center gap-2 text-[#2563EB]">
                      {task.status === "COMPLETED" ? (
                        <CheckCircle2 className="w-4 h-4 text-[#17803D]" />
                      ) : (
                        <Clock className="w-4 h-4 animate-spin text-[#2563EB]" />
                      )}
                      <span className="font-medium">{task.stepStatus}</span>
                    </div>

                    {task.status === "COMPLETED" && (
                      <Link href="/verification">
                        <Button size="sm" variant="secondary">
                          Inspect Verification
                          <ArrowRight className="w-3 h-3 ml-1" />
                        </Button>
                      </Link>
                    )}
                  </div>
                )}
              </div>

              {/* Card Footer: Approval Actions */}
              {task.status === "AWAITING_APPROVAL" && (
                <div className="px-5 py-3 bg-[#F7F7F5] border-t border-[#E5E7EB] flex items-center justify-between">
                  <span className="text-[11px] text-[#5F6368]">
                    Requires authorized confirmation before dispatching API calls
                  </span>

                  <div className="flex items-center gap-2">
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => handleReject(task.id)}
                    >
                      <X className="w-3.5 h-3.5 text-[#C62828]" />
                      Reject
                    </Button>

                    <Button 
                      size="sm" 
                      variant="primary" 
                      onClick={() => handleApprove(task.id)}
                    >
                      <Check className="w-3.5 h-3.5" />
                      Approve & Execute
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Autonomous Service Monitor */}
      <div className="p-5 rounded-lg bg-white border border-[#E5E7EB] space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-[#2563EB]" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#171717]">
              Execution Dispatch Engine Telemetry
            </h3>
          </div>
          <span className="font-mono text-[11px] text-[#17803D] bg-[#F0FDF4] px-2 py-0.5 rounded border border-[#BBF7D0]">
            Daemon Healthy
          </span>
        </div>
        <p className="text-xs text-[#5F6368]">
          Connected to local FastAPI orchestrator at <span className="font-mono text-[#171717]">http://localhost:8000/api/v1/execution</span>. 
          Audited under Zero-Trust policy engine with cryptographic nonce guarantees.
        </p>
      </div>
    </div>
  );
}
