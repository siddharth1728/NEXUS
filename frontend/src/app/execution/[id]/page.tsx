"use client";

import React, { useState, use } from "react";
import Link from "next/link";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { LivingLine } from "@/components/ui/LivingLine";
import { 
  ArrowLeft, 
  ShieldCheck, 
  Check, 
  X, 
  AlertTriangle, 
  Code 
} from "lucide-react";

export default function ExecutionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [approving, setApproving] = useState(false);
  const [executionState, setExecutionState] = useState<string>("AWAITING_APPROVAL");

  const execution = {
    id,
    action_id: "act-sec-42",
    connector_name: "github",
    tool_name: "GITHUB_ISSUE_CREATE",
    state: executionState,
    parameters: {
      owner: "acme",
      repo: "nexus",
      title: "Enforce JWT authentication on API edge gateway",
      body: "Security review constraint identified in Architecture_Guidelines.pdf. Requires cryptographic signature verification.",
      labels: ["security", "p1-compliance"]
    },
    created_at: "2026-10-03T10:00:00.000Z",
    updated_at: "2026-10-03T12:00:00.000Z",
  };

  const handleApprove = () => {
    setApproving(true);
    setTimeout(() => {
      setExecutionState("SUCCEEDED");
      setApproving(false);
    }, 1200);
  };

  const handleReject = () => {
    setApproving(true);
    setTimeout(() => {
      setExecutionState("FAILED");
      setApproving(false);
    }, 800);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div>
        <Link 
          href="/execution" 
          className="inline-flex items-center text-sm font-medium text-[#5F6368] hover:text-[#171717] transition-colors gap-2"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Execution
        </Link>
      </div>

      {/* Living Line Header */}
      <div className="bg-white rounded-2xl border border-[#E5E7EB] p-6 shadow-2xs">
        <LivingLine 
          currentStage={executionState === "SUCCEEDED" ? "verification" : "execution"} 
          completedStages={executionState === "SUCCEEDED" ? ["information", "understanding", "action", "execution"] : ["information", "understanding", "action"]}
        />
      </div>

      {/* Main Header */}
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-4 border-b border-[#ECECE9] pb-6">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <StatusBadge status={execution.state} size="md" />
            <span className="text-xs font-mono text-[#8A8F98]">ID: {execution.id}</span>
          </div>
          <h1 className="font-display text-4xl sm:text-5xl text-[#171717]">
            Execution Dispatch
          </h1>
          <p className="text-sm font-mono text-[#5F6368]">
            Connector: <strong className="text-[#171717]">{execution.connector_name}</strong> · Capability: <strong className="text-[#2563EB]">{execution.tool_name}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/verification">
            <Button variant="outline" size="md">
              <ShieldCheck className="w-4 h-4 text-[#15803D] mr-2" />
              Verification Engine
            </Button>
          </Link>
        </div>
      </div>

      {/* Approval Alert if Pending */}
      {execution.state === "AWAITING_APPROVAL" && (
        <div className="p-6 rounded-2xl bg-[#FAF5FF] border border-[#E9D5FF] flex flex-col md:flex-row items-center justify-between gap-6 shadow-2xs">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-white border border-[#C084FC] flex items-center justify-center text-[#7C3AED] shrink-0 mt-0.5">
              <AlertTriangle className="w-5 h-5 text-[#7C3AED]" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-[#7C3AED] uppercase tracking-wider">
                Human Approval Required
              </h3>
              <p className="text-sm text-[#171717] max-w-2xl leading-relaxed">
                This dispatch mutates the external repository <span className="font-mono text-[#7C3AED] font-semibold">acme/nexus</span> via GitHub API. 
                Inspect execution parameters before authorizing.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Button 
              size="md" 
              variant="outline" 
              onClick={handleReject} 
              isLoading={approving}
              className="text-[#DC2626] border-[#FECACA] hover:bg-[#FEF2F2]"
            >
              <X className="w-4 h-4 mr-1.5" />
              Reject Dispatch
            </Button>
            <Button 
              size="md" 
              variant="primary" 
              onClick={handleApprove} 
              isLoading={approving}
            >
              <Check className="w-4 h-4 mr-1.5" />
              Approve & Execute
            </Button>
          </div>
        </div>
      )}

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column (8 cols): Execution Details & Payload */}
        <div className="lg:col-span-8 space-y-6">
          <div className="bg-white rounded-2xl border border-[#E5E7EB] p-8 space-y-4 shadow-2xs">
            <div className="flex items-center gap-2.5 pb-4 border-b border-[#ECECE9]">
              <Code className="w-5 h-5 text-[#2563EB]" />
              <h2 className="text-lg font-semibold text-[#171717]">
                Execution Parameters (JSON Payload)
              </h2>
            </div>
            <pre className="p-5 text-xs font-mono text-[#171717] overflow-x-auto bg-[#F7F7F5] rounded-xl border border-[#ECECE9]">
              {JSON.stringify(execution.parameters, null, 2)}
            </pre>
          </div>
        </div>

        {/* Right Column (4 cols): Target System & Audit Rail */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-white rounded-2xl border border-[#E5E7EB] p-8 space-y-4 shadow-2xs">
            <h2 className="text-lg font-semibold text-[#171717] pb-4 border-b border-[#ECECE9]">
              Target System
            </h2>
            <div className="space-y-4 text-sm">
              <div className="space-y-1">
                <span className="text-xs font-mono text-[#8A8F98] uppercase tracking-wider block">
                  Connector
                </span>
                <span className="font-mono bg-[#F7F7F5] border border-[#ECECE9] px-3 py-1.5 rounded-xl block text-[#171717]">
                  {execution.connector_name}
                </span>
              </div>

              <div className="space-y-1">
                <span className="text-xs font-mono text-[#8A8F98] uppercase tracking-wider block">
                  Tool Capability
                </span>
                <span className="font-mono bg-[#EFF6FF] border border-[#BFDBFE] text-[#2563EB] px-3 py-1.5 rounded-xl block font-medium">
                  {execution.tool_name}
                </span>
              </div>

              <div className="pt-4 border-t border-[#ECECE9] space-y-2 text-xs text-[#5F6368]">
                <div className="flex justify-between">
                  <span>Created:</span>
                  <span className="font-mono text-[#171717]">{new Date(execution.created_at).toLocaleTimeString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Last Audit:</span>
                  <span className="font-mono text-[#171717]">{new Date(execution.updated_at).toLocaleTimeString()}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
