"use client";

import React, { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api, ActionItem } from "@/api/client";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { LineOfTruth } from "@/components/ui/LineOfTruth";
import { SourceDrawer, ProvenanceData } from "@/components/ui/SourceDrawer";
import { 
  ArrowLeft, 
  FileText, 
  PlayCircle, 
  CheckCircle2, 
  Clock, 
  Lock, 
  GitBranch, 
  ExternalLink,
  ShieldCheck,
  ChevronRight,
  Terminal,
  Quote,
  History
} from "lucide-react";

export default function ActionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Fetch action details from live API
  const { data: action, isLoading, error } = useQuery<ActionItem>({
    queryKey: ["action", id],
    queryFn: async () => {
      try {
        return await api.get<ActionItem>(`/actions/${id}`);
      } catch (e) {
        // Fallback for demo ID or mock inspection
        return {
          id,
          tenant_id: "00000000-0000-4000-8000-000000000001",
          title: "Review security and authentication configuration",
          description: "Inspect JWT bearer token validation rules, cryptographic key rotation policy, and CORS header enforcement on the edge proxy.",
          status: "READY",
          action_type: "SECURITY_REVIEW",
          priority: "high",
          due_date: new Date().toISOString(),
          created_at: new Date(Date.now() - 3600000 * 24).toISOString(),
          updated_at: new Date(Date.now() - 3600000 * 4).toISOString(),
          source_context: {
            document_id: "doc-arch-01",
            document_title: "Architecture_Guidelines_v2.pdf",
            location: "Page 14 / Section 3: Authentication",
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
    sourceLocation: action?.source_context?.location || "Page 14 / Section 3: Authentication",
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
      <div className="p-16 text-center text-xs text-[#5F6368]">
        <div className="w-5 h-5 border-2 border-[#2563EB] border-t-transparent rounded-full animate-spin mx-auto mb-2" />
        Loading action investigation workspace...
      </div>
    );
  }

  if (!action) {
    return (
      <div className="p-12 text-center text-xs text-[#5F6368] space-y-3">
        <p className="font-semibold text-sm text-[#171717]">Action Not Found</p>
        <p>The requested action item could not be retrieved from the active tenant.</p>
        <Link href="/actions">
          <Button size="sm">Back to Actions Workspace</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Back Link */}
      <Link 
        href="/actions" 
        className="inline-flex items-center text-xs font-medium text-[#5F6368] hover:text-[#171717] transition-colors gap-1.5"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Actions Workspace
      </Link>

      {/* Signature "Line of Truth" Progression Header */}
      <div className="p-4 rounded-lg bg-white border border-[#E5E7EB]">
        <LineOfTruth 
          currentStep={action.status === "VERIFIED" ? "verification" : action.status === "READY" ? "action" : "execution"} 
          completedSteps={["source", "action"]}
        />
      </div>

      {/* Main Narrative Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E5E7EB] pb-5">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <h1 className="text-xl font-bold tracking-tight text-[#171717]">
              {action.title}
            </h1>
            <StatusBadge status={action.status} />
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-[#5F6368]">
            <span>ID: {action.id}</span>
            <span>•</span>
            <span className="uppercase text-[#2563EB] font-semibold">{action.action_type || "TASK"}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setDrawerOpen(true)}
          >
            <FileText className="w-3.5 h-3.5 text-[#2563EB]" />
            Inspect Provenance
          </Button>

          <Button 
            variant="primary" 
            size="sm"
            onClick={() => router.push("/execution")}
          >
            <PlayCircle className="w-3.5 h-3.5" />
            Dispatch Execution
          </Button>
        </div>
      </div>

      {/* Signature "Why This Exists" Grounding Callout */}
      <div className="p-4 rounded-lg border border-[#E5E7EB] bg-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <span className="text-[10px] font-mono uppercase tracking-wider font-semibold text-[#5F6368] flex items-center gap-1.5">
            <Quote className="w-3.5 h-3.5 text-[#2563EB]" /> Why This Exists
          </span>
          <p className="text-xs text-[#171717]">
            NEXUS extracted this operational requirement directly from:
          </p>
          <div className="flex items-center gap-2 font-mono text-xs text-[#2563EB] font-medium">
            <FileText className="w-3.5 h-3.5" />
            <span>{provenanceData.sourceTitle}</span>
            <span className="text-[#5F6368]">({provenanceData.sourceLocation})</span>
          </div>
        </div>

        <Button 
          variant="secondary" 
          size="sm"
          onClick={() => setDrawerOpen(true)}
          className="self-start md:self-auto shrink-0"
        >
          View Source Context
          <ExternalLink className="w-3 h-3 ml-1" />
        </Button>
      </div>

      {/* Narrative Workspace: Two Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): Core Investigation Elements */}
        <div className="lg:col-span-8 space-y-6">
          {/* Section: WHAT & WHY */}
          <div className="bg-white rounded-lg border border-[#E5E7EB] p-5 space-y-4 shadow-xs">
            <div>
              <h2 className="text-[11px] font-mono uppercase tracking-wider font-semibold text-[#5F6368] mb-2">
                WHAT
              </h2>
              <p className="text-xs text-[#171717] leading-relaxed">
                {action.description || action.title}
              </p>
            </div>

            <div className="pt-4 border-t border-[#E5E7EB]">
              <h2 className="text-[11px] font-mono uppercase tracking-wider font-semibold text-[#5F6368] mb-2">
                WHY
              </h2>
              <p className="text-xs text-[#5F6368] leading-relaxed">
                Mandatory operational policy constraint detected during automated ingestion and knowledge synthesis. Required to guarantee compliance and safe system execution.
              </p>
            </div>
          </div>

          {/* Section: DEPENDENCIES */}
          <div className="bg-white rounded-lg border border-[#E5E7EB] p-5 space-y-4 shadow-xs">
            <div className="flex items-center justify-between">
              <h2 className="text-[11px] font-mono uppercase tracking-wider font-semibold text-[#5F6368] flex items-center gap-1.5">
                <GitBranch className="w-3.5 h-3.5 text-[#2563EB]" /> Dependencies & Graph Linkage
              </h2>
              <Link href="/graph" className="text-xs text-[#2563EB] hover:underline font-medium">
                View in Action Graph
              </Link>
            </div>

            <div className="space-y-2">
              <div className="p-3 rounded-md border border-[#BBF7D0] bg-[#F0FDF4] flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-[#17803D]" />
                  <span className="text-xs font-medium text-[#171717]">API design & schema validation finalized</span>
                </div>
                <span className="text-[11px] font-mono text-[#17803D]">CLEARED</span>
              </div>

              <div className="p-3 rounded-md border border-[#E5E7EB] bg-[#F7F7F5] flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <Clock className="w-4 h-4 text-[#A65F00]" />
                  <span className="text-xs font-medium text-[#171717]">Security peer review authorization</span>
                </div>
                <span className="text-[11px] font-mono text-[#A65F00]">PENDING</span>
              </div>
            </div>
          </div>

          {/* Section: EXECUTION & VERIFICATION PROJECTION */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Execution */}
            <div className="bg-white rounded-lg border border-[#E5E7EB] p-4 space-y-2">
              <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-[#5F6368] flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5 text-[#2563EB]" /> Execution Status
              </span>
              <p className="text-xs text-[#171717] font-medium">No execution run yet</p>
              <p className="text-[11px] text-[#5F6368]">
                Action is staged in READY state. Ready to dispatch to target connector.
              </p>
            </div>

            {/* Expected Verification */}
            <div className="bg-white rounded-lg border border-[#E5E7EB] p-4 space-y-2">
              <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-[#5F6368] flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-[#17803D]" /> Expected Verification
              </span>
              <p className="text-xs text-[#171717] font-medium">Review completion evidence</p>
              <p className="text-[11px] text-[#5F6368]">
                Independent proof check via webhook / external observer signature.
              </p>
            </div>
          </div>
        </div>

        {/* Right Column (4 cols): Contextual Rail (Source, Facts, History) */}
        <div className="lg:col-span-4 space-y-4">
          {/* Rail 1: Source */}
          <div className="bg-white rounded-lg border border-[#E5E7EB] p-4 space-y-3">
            <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-[#5F6368]">
              SOURCE
            </span>
            <div className="p-3 rounded-md bg-[#F7F7F5] border border-[#E5E7EB] space-y-1">
              <div className="text-xs font-semibold text-[#171717] flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-[#2563EB]" />
                {provenanceData.sourceTitle}
              </div>
              <div className="text-[11px] font-mono text-[#5F6368]">
                {provenanceData.sourceLocation}
              </div>
            </div>
          </div>

          {/* Rail 2: Facts */}
          <div className="bg-white rounded-lg border border-[#E5E7EB] p-4 space-y-3">
            <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-[#5F6368]">
              EXTRACTED FACTS
            </span>
            <div className="space-y-2">
              {provenanceData.extractedFacts?.map((fact, idx) => (
                <div key={idx} className="p-2.5 rounded-md border border-[#E5E7EB] bg-[#F7F7F5] text-[11px] text-[#171717] flex items-start gap-2">
                  <span className="font-mono text-[10px] text-[#2563EB] font-bold">F{idx + 1}</span>
                  <span>{fact}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Rail 3: History */}
          <div className="bg-white rounded-lg border border-[#E5E7EB] p-4 space-y-3">
            <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-[#5F6368] flex items-center gap-1.5">
              <History className="w-3.5 h-3.5" /> AUDIT HISTORY
            </span>
            <div className="space-y-2 text-[11px] text-[#5F6368]">
              <div className="flex items-center justify-between">
                <span>Created</span>
                <span className="font-mono text-[#171717]">{new Date(action.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Synthesized</span>
                <span className="font-mono text-[#171717]">Automated Pipeline</span>
              </div>
              <div className="flex items-center justify-between">
                <span>State Transition</span>
                <span className="font-mono text-[#17803D]">CANDIDATE → READY</span>
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
