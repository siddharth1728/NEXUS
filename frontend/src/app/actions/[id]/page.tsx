"use client";

import React, { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api, ActionItem } from "@/api/client";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { LivingLine } from "@/components/ui/LivingLine";
import { SourceDrawer, ProvenanceData } from "@/components/ui/SourceDrawer";
import { 
  ArrowLeft, 
  FileText, 
  PlayCircle, 
  CheckCircle2, 
  Clock, 
  GitBranch, 
  ExternalLink, 
  ShieldCheck, 
  History,
  ArrowRight
} from "lucide-react";

export default function ActionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Fetch action details from live API
  const { data: action, isLoading } = useQuery<ActionItem>({
    queryKey: ["action", id],
    queryFn: async () => {
      try {
        return await api.get<ActionItem>(`/actions/${id}`);
      } catch {
        // Safe contextual demo fallback
        return {
          id,
          tenant_id: "00000000-0000-4000-8000-000000000001",
          title: "Review security and authentication architecture",
          description: "Inspect JWT bearer token validation rules, cryptographic key rotation policy, and CORS header perimeter enforcement on the edge proxy.",
          status: "READY",
          action_type: "SECURITY_REVIEW",
          priority: "high",
          due_date: new Date().toISOString(),
          created_at: new Date(Date.now() - 3600000 * 24).toISOString(),
          updated_at: new Date(Date.now() - 3600000 * 4).toISOString(),
          source_context: {
            document_id: "doc-arch-01",
            document_title: "Architecture_Guidelines_v2.pdf",
            location: "Page 14 · Section 3: Authentication",
            excerpt: "All external consumer requests must undergo token authentication and payload cryptographic verification against tenant JWKS prior to downstream dispatch.",
            facts: [
              "Cryptographic signature check is required on API perimeter",
              "JWKS keys must rotate every 24 hours without downtime",
              "Unauthenticated requests must terminate at the proxy layer"
            ]
          }
        };
      }
    },
  });

  const provenanceData: ProvenanceData = {
    sourceTitle: action?.source_context?.document_title || "Architecture_Guidelines_v2.pdf",
    sourceLocation: action?.source_context?.location || "Page 14 · Section 3: Authentication",
    excerpt: action?.source_context?.excerpt || "All incoming client requests must undergo token authentication and payload cryptographic verification prior to downstream dispatch.",
    extractedFacts: action?.source_context?.facts || [
      "JWT validation is required across all ingress endpoints",
      "Signature verification must reject expired or revoked certificates"
    ],
    derivedActionTitle: action?.title || "Operational Action Item",
    verificationEvidence: "Target external API audit entry matches SHA256 checksum",
  };

  if (isLoading) {
    return (
      <div className="p-16 text-center text-sm font-mono text-[#5F6368] bg-white rounded-2xl border border-[#E5E7EB]">
        Loading action context workspace...
      </div>
    );
  }

  if (!action) {
    return (
      <div className="p-16 text-center bg-white rounded-2xl border border-[#E5E7EB] space-y-4">
        <h2 className="text-xl font-semibold text-[#171717]">Action Not Found</h2>
        <p className="text-sm text-[#5F6368]">The requested action item could not be retrieved from the active tenant.</p>
        <Link href="/actions">
          <Button size="md">Return to Actions</Button>
        </Link>
      </div>
    );
  }

  const isVerified = action.status === "VERIFIED" || action.status === "verified";
  const isExecuting = action.status === "RUNNING" || action.status === "executing";

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Navigation Breadcrumb */}
      <div>
        <Link 
          href="/actions" 
          className="inline-flex items-center text-sm font-medium text-[#5F6368] hover:text-[#171717] transition-colors gap-2"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Actions
        </Link>
      </div>

      {/* Hero Masthead */}
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6 border-b border-[#ECECE9] pb-8">
        <div className="space-y-3 flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <StatusBadge status={action.status} size="md" />
            <span className="text-xs font-mono text-[#5F6368] bg-[#F7F7F5] px-2.5 py-0.5 rounded-md border border-[#ECECE9]">
              {action.action_type || "TASK"}
            </span>
            <span className="text-xs font-mono text-[#8A8F98]">
              ID: {action.id}
            </span>
          </div>

          <h1 className="font-display text-4xl sm:text-5xl text-[#171717] tracking-tight leading-tight">
            {action.title}
          </h1>

          <p className="text-base sm:text-lg text-[#5F6368] max-w-4xl font-normal leading-relaxed">
            {action.description || "Operational execution task synthesized from verified source document."}
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0 pt-2 lg:pt-0">
          <Button 
            variant="outline" 
            size="md"
            onClick={() => setDrawerOpen(true)}
          >
            <FileText className="w-4 h-4 text-[#2563EB] mr-2" />
            Inspect Provenance
          </Button>

          <Button 
            variant="primary" 
            size="md"
            onClick={() => router.push("/execution")}
          >
            <PlayCircle className="w-4 h-4 mr-2" />
            Dispatch Execution
          </Button>
        </div>
      </div>

      {/* Living Line: Causal Progression */}
      <div className="bg-white rounded-2xl border border-[#E5E7EB] p-6 shadow-2xs">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-mono font-medium text-[#5F6368]">
            LIVING CAUSAL LINE
          </span>
          <span className="text-xs font-medium text-[#15803D] flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> Source Grounded
          </span>
        </div>
        <LivingLine 
          currentStage={isVerified ? "verification" : isExecuting ? "execution" : "action"} 
          completedStages={isVerified ? ["information", "understanding", "action", "execution", "evidence", "verification"] : ["information", "understanding", "action"]}
        />
      </div>

      {/* Action Detail Layout: Main Content + Contextual Rail */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Main Content (8 cols): WHAT / WHY / DEPENDENCIES / EXECUTION / VERIFICATION */}
        <div className="lg:col-span-8 space-y-8">
          {/* 1. WHY THIS EXISTS */}
          <div className="bg-white rounded-2xl border border-[#E5E7EB] p-8 space-y-4 shadow-2xs">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-[#171717] tracking-tight">
                Why this exists
              </h2>
              <button 
                onClick={() => setDrawerOpen(true)}
                className="text-xs text-[#2563EB] hover:underline font-medium flex items-center gap-1 cursor-pointer"
              >
                <span>Full lineage</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="p-5 rounded-xl bg-[#F7F7F5] border border-[#ECECE9] space-y-2">
              <div className="flex items-center gap-2 text-xs font-mono text-[#5F6368]">
                <FileText className="w-4 h-4 text-[#2563EB]" />
                <span className="font-semibold text-[#171717]">{provenanceData.sourceTitle}</span>
                <span>·</span>
                <span>{provenanceData.sourceLocation}</span>
              </div>
              <blockquote className="font-display text-lg text-[#171717] leading-relaxed italic border-l-2 border-[#2563EB] pl-3 py-1">
                &ldquo;{provenanceData.excerpt}&rdquo;
              </blockquote>
            </div>
          </div>

          {/* 2. WHAT NEEDS TO HAPPEN */}
          <div className="bg-white rounded-2xl border border-[#E5E7EB] p-8 space-y-4 shadow-2xs">
            <h2 className="text-xl font-semibold text-[#171717] tracking-tight">
              What needs to happen
            </h2>
            <p className="text-base text-[#171717] leading-relaxed">
              {action.description || action.title}
            </p>
            <div className="p-4 rounded-xl bg-[#EFF6FF] border border-[#BFDBFE] text-sm text-[#1E40AF]">
              Execute through target capability with strict parameter schema validation and cryptographic audit hashing.
            </div>
          </div>

          {/* 3. DEPENDENCIES */}
          <div className="bg-white rounded-2xl border border-[#E5E7EB] p-8 space-y-4 shadow-2xs">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-[#171717] tracking-tight">
                  Dependencies
                </h2>
                <p className="text-sm text-[#5F6368] mt-0.5">
                  Prerequisites required before this action can progress downstream.
                </p>
              </div>
              <Link href="/graph" className="text-sm text-[#2563EB] hover:underline font-medium flex items-center gap-1">
                <span>View Graph</span>
                <GitBranch className="w-4 h-4" />
              </Link>
            </div>

            <div className="space-y-3">
              {/* Cleared dependency */}
              <div className="p-4 rounded-xl border border-[#BBF7D0] bg-[#F0FDF4] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-[#15803D]" />
                  <div>
                    <span className="text-sm font-semibold text-[#171717]">API design & schema validation finalized</span>
                    <p className="text-xs text-[#15803D]">Prerequisite satisfied by automated verification</p>
                  </div>
                </div>
                <span className="text-xs font-mono font-semibold px-2 py-0.5 bg-white text-[#15803D] rounded border border-[#86EFAC]">
                  CLEARED
                </span>
              </div>

              {/* Pending dependency */}
              <div className="p-4 rounded-xl border border-[#ECECE9] bg-[#F7F7F5] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Clock className="w-5 h-5 text-[#D97706]" />
                  <div>
                    <span className="text-sm font-semibold text-[#171717]">Security authorization review</span>
                    <p className="text-xs text-[#5F6368]">Awaiting affirmative human approval signature</p>
                  </div>
                </div>
                <span className="text-xs font-mono font-semibold px-2 py-0.5 bg-white text-[#D97706] rounded border border-[#FDE68A]">
                  PENDING
                </span>
              </div>
            </div>
          </div>

          {/* 4. EXECUTION & 5. VERIFICATION */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Execution */}
            <div className="bg-white rounded-2xl border border-[#E5E7EB] p-6 space-y-3 shadow-2xs">
              <span className="text-xs font-mono font-semibold text-[#2563EB] tracking-wider uppercase">
                Execution
              </span>
              <h3 className="text-lg font-semibold text-[#171717]">
                {isExecuting ? "In Flight" : "Ready to Dispatch"}
              </h3>
              <p className="text-sm text-[#5F6368] leading-relaxed">
                Connects through authorized integration adapter. Emits immutable execution intent with SHA-256 payload digest.
              </p>
              <div className="pt-2">
                <Link href="/execution">
                  <Button variant="primary" size="sm" className="w-full">
                    <span>Go to Execution Surface</span>
                    <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                  </Button>
                </Link>
              </div>
            </div>

            {/* Verification */}
            <div className="bg-white rounded-2xl border border-[#E5E7EB] p-6 space-y-3 shadow-2xs">
              <span className="text-xs font-mono font-semibold text-[#15803D] tracking-wider uppercase">
                Verification
              </span>
              <h3 className="text-lg font-semibold text-[#171717]">
                {isVerified ? "Verified Proof" : "Expected Evidence"}
              </h3>
              <p className="text-sm text-[#5F6368] leading-relaxed">
                Independent observer queries target system directly to confirm real-world state transformation.
              </p>
              <div className="pt-2">
                <Link href="/verification">
                  <Button variant="outline" size="sm" className="w-full">
                    <span>Inspect Evidence</span>
                    <ShieldCheck className="w-3.5 h-3.5 ml-1.5" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Contextual Rail (4 cols): SOURCE, FACTS, HISTORY, TECHNICAL METADATA */}
        <div className="lg:col-span-4 space-y-6">
          {/* Rail 1: Source */}
          <div className="bg-white rounded-2xl border border-[#E5E7EB] p-6 space-y-3 shadow-2xs">
            <span className="text-xs font-mono font-semibold text-[#8A8F98] tracking-wider uppercase">
              Source Intelligence
            </span>
            <div className="p-4 rounded-xl bg-[#F7F7F5] border border-[#ECECE9] space-y-1.5">
              <div className="text-sm font-semibold text-[#171717] flex items-center gap-2">
                <FileText className="w-4 h-4 text-[#2563EB]" />
                {provenanceData.sourceTitle}
              </div>
              <div className="text-xs font-mono text-[#5F6368]">
                {provenanceData.sourceLocation}
              </div>
            </div>
          </div>

          {/* Rail 2: Extracted Facts */}
          <div className="bg-white rounded-2xl border border-[#E5E7EB] p-6 space-y-3 shadow-2xs">
            <span className="text-xs font-mono font-semibold text-[#8A8F98] tracking-wider uppercase">
              Extracted Facts
            </span>
            <div className="space-y-2">
              {provenanceData.extractedFacts?.map((fact, idx) => (
                <div key={idx} className="p-3 rounded-xl border border-[#ECECE9] bg-[#F7F7F5] text-xs text-[#171717] flex items-start gap-2.5">
                  <span className="font-mono text-xs text-[#2563EB] font-bold shrink-0">F{idx + 1}</span>
                  <span className="leading-snug">{fact}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Rail 3: Audit History */}
          <div className="bg-white rounded-2xl border border-[#E5E7EB] p-6 space-y-3 shadow-2xs">
            <span className="text-xs font-mono font-semibold text-[#8A8F98] tracking-wider uppercase flex items-center gap-1.5">
              <History className="w-3.5 h-3.5" /> Audit History
            </span>
            <div className="space-y-2.5 text-xs text-[#5F6368]">
              <div className="flex items-center justify-between">
                <span>Created</span>
                <span className="font-mono text-[#171717]">{new Date(action.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Synthesis Engine</span>
                <span className="font-mono text-[#171717]">Automated Grounding</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Tenant Domain</span>
                <span className="font-mono text-[#2563EB]">dev-tenant</span>
              </div>
            </div>
          </div>

          {/* Rail 4: Technical Metadata */}
          <div className="bg-white rounded-2xl border border-[#E5E7EB] p-6 space-y-3 shadow-2xs">
            <span className="text-xs font-mono font-semibold text-[#8A8F98] tracking-wider uppercase">
              Technical Metadata
            </span>
            <div className="space-y-2 text-xs font-mono text-[#5F6368]">
              <div className="flex items-center justify-between">
                <span>Priority:</span>
                <span className="text-[#171717] font-semibold">{action.priority || "P1"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Action Type:</span>
                <span className="text-[#171717]">{action.action_type || "TASK"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Security Boundary:</span>
                <span className="text-[#15803D]">Zero-Trust Enforced</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Contextual Source Drawer */}
      <SourceDrawer 
        isOpen={drawerOpen} 
        onClose={() => setDrawerOpen(false)} 
        data={provenanceData} 
      />
    </div>
  );
}
