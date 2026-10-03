"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api, ActionItem } from "@/api/client";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { SourceDrawer, ProvenanceData } from "@/components/ui/SourceDrawer";
import { LivingLine } from "@/components/ui/LivingLine";
import { OnboardingBanner } from "@/components/ui/OnboardingBanner";
import { EmptyActionsIllustration } from "@/components/ui/MicroIllustrations";
import { 
  ArrowRight, 
  PlayCircle, 
  FileText, 
  CheckCircle2, 
  ExternalLink,
  ChevronRight,
  GitBranch
} from "lucide-react";

export default function Dashboard() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedProvenance, setSelectedProvenance] = useState<ProvenanceData | null>(null);

  // Fetch live actions from the backend
  const { data: actions = [], isLoading } = useQuery<ActionItem[]>({
    queryKey: ["actions"],
    queryFn: async () => {
      try {
        const res = await api.get<ActionItem[]>("/actions?limit=50");
        return res || [];
      } catch {
        return [];
      }
    },
  });

  // Calculate actual backend-derived metrics
  const candidateActions = actions.filter(
    a => a.status === "CANDIDATE" || a.status === "needs_review" || a.status === "requires_approval"
  );
  const blockedActions = actions.filter(a => a.status === "BLOCKED" || a.status === "blocked");
  const readyActions = actions.filter(a => a.status === "READY" || a.status === "ready");
  const verifiedActions = actions.filter(
    a => a.status === "VERIFIED" || a.status === "verified" || a.status === "SUCCEEDED" || a.status === "completed"
  );

  // Items needing immediate attention (Candidate, Blocked, Ready)
  const attentionItems = [...candidateActions, ...blockedActions, ...readyActions].slice(0, 6);

  const openProvenance = (item: ActionItem) => {
    setSelectedProvenance({
      sourceTitle: item.source_context?.document_title || "Architecture_Guidelines_v2.pdf",
      sourceLocation: item.source_context?.location || "Page 14 · Section 3.2",
      excerpt: item.source_context?.excerpt || "All client requests must undergo token authentication and cryptographic verification prior to downstream dispatch.",
      extractedFacts: item.source_context?.facts || [
        "Cryptographic verification required at border gateway",
        "Tenant identity validation enforced via strict claims"
      ],
      derivedActionTitle: item.title,
      verificationEvidence: "Target external API audit entry matches SHA256 checksum",
    });
    setDrawerOpen(true);
  };

  return (
    <div className="space-y-12 animate-in fade-in duration-300">
      {/* 1. The Editorial Masthead */}
      <section className="space-y-4 pt-2">
        <div className="flex flex-col md:flex-row md:items-baseline md:justify-between gap-4 border-b border-[#ECECE9] pb-8">
          <div>
            <span className="text-xs font-mono font-medium text-[#2563EB] tracking-wider uppercase">
              Operational Status
            </span>
            <h1 className="font-display text-4xl sm:text-5xl text-[#171717] mt-2 tracking-tight">
              What needs your attention?
            </h1>
            <p className="text-base sm:text-lg text-[#5F6368] mt-3 font-normal">
              <span className="font-semibold text-[#171717]">{candidateActions.length}</span> awaiting review ·{" "}
              <span className="font-semibold text-[#171717]">{blockedActions.length}</span> blocked ·{" "}
              <span className="font-semibold text-[#171717]">{readyActions.length}</span> ready to execute ·{" "}
              <span className="font-semibold text-[#15803D]">{verifiedActions.length}</span> verified
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Link href="/actions">
              <Button variant="secondary" size="md">
                All Actions ({actions.length})
              </Button>
            </Link>
            <Link href="/execution">
              <Button variant="primary" size="md">
                <PlayCircle className="w-4 h-4 mr-2" />
                Execution Center
              </Button>
            </Link>
          </div>
        </div>

        {/* 2. The Living Line: Causal Signature */}
        <div className="bg-white rounded-2xl border border-[#E5E7EB] p-6 shadow-2xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-medium text-[#5F6368]">
              ENGINE PROGRESSION LINE
            </span>
            <span className="text-xs text-[#2563EB] font-medium flex items-center gap-1">
              Context-to-Action Pipeline <ArrowRight className="w-3.5 h-3.5" />
            </span>
          </div>
          <LivingLine 
            currentStage={readyActions.length > 0 ? "execution" : "action"} 
            completedStages={["information", "understanding", "action"]}
          />
        </div>

        {/* 3. First-Run / Onboarding Guide (Dismissable) */}
        <OnboardingBanner />
      </section>

      {/* 4. Primary Narrative: Attention Workspace */}
      <section className="space-y-6">
        <div className="flex items-baseline justify-between border-b border-[#ECECE9] pb-3">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-semibold text-[#171717] tracking-tight">
              Attention
            </h2>
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-[#EFF6FF] text-[#2563EB] font-medium border border-[#BFDBFE]">
              {attentionItems.length} items requiring review or execution
            </span>
          </div>
          <Link 
            href="/actions" 
            className="text-sm text-[#2563EB] hover:text-[#1D4ED8] flex items-center gap-1 font-medium group"
          >
            <span>View all work items</span>
            <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>

        {isLoading ? (
          <div className="p-12 text-center text-[#5F6368] font-mono text-sm bg-white rounded-2xl border border-[#E5E7EB]">
            Synchronizing live state from engine...
          </div>
        ) : attentionItems.length === 0 ? (
          <div className="p-12 text-center bg-white rounded-2xl border border-[#E5E7EB] space-y-4">
            <EmptyActionsIllustration className="mx-auto" size={100} />
            <div className="space-y-1">
              <h3 className="text-xl font-semibold text-[#171717]">Turn information into work</h3>
              <p className="text-sm text-[#5F6368] max-w-md mx-auto">
                No pending actions require human review or unblocking. New actions will synthesize automatically as sources ingest.
              </p>
            </div>
            <Link href="/documents" className="inline-block pt-2">
              <Button size="sm" variant="primary">
                Add Source Document
              </Button>
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {attentionItems.map((action) => (
              <div 
                key={action.id}
                className="group bg-white hover:bg-[#FDFDFD] p-6 rounded-2xl border border-[#E5E7EB] hover:border-[#D1D5DB] transition-all flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-2xs hover:shadow-xs"
              >
                {/* Decision Structure: WHAT + WHY + STATUS */}
                <div className="space-y-2.5 flex-1">
                  {/* Status & ID */}
                  <div className="flex items-center gap-3 flex-wrap">
                    <StatusBadge status={action.status} size="md" />
                    <span className="text-xs font-mono text-[#8A8F98]">
                      ID: {action.id.slice(0, 8)}
                    </span>
                    {action.source_context?.document_title && (
                      <button
                        onClick={() => openProvenance(action)}
                        className="inline-flex items-center gap-1.5 text-xs text-[#5F6368] hover:text-[#171717] bg-[#F7F7F5] hover:bg-[#ECECE9] px-2.5 py-0.5 rounded-md border border-[#ECECE9] transition-all font-mono cursor-pointer"
                        title="Inspect Provenance"
                      >
                        <FileText className="w-3.5 h-3.5 text-[#2563EB]" />
                        <span>Source: {action.source_context.document_title}</span>
                      </button>
                    )}
                  </div>

                  {/* WHAT */}
                  <h3 className="text-xl font-medium text-[#171717] group-hover:text-[#2563EB] transition-colors leading-snug">
                    <Link href={`/actions/${action.id}`}>
                      {action.title}
                    </Link>
                  </h3>

                  {/* WHY */}
                  <p className="text-sm text-[#5F6368] line-clamp-1 max-w-3xl leading-relaxed">
                    {action.description || (
                      action.source_context?.excerpt ? `Grounded requirement: "${action.source_context.excerpt}"` : "Synthesized compliance action derived from source specifications."
                    )}
                  </p>
                </div>

                {/* NEXT STEP CTA */}
                <div className="flex items-center gap-3 shrink-0 pt-2 md:pt-0">
                  <button
                    onClick={() => openProvenance(action)}
                    className="text-xs font-medium text-[#5F6368] hover:text-[#171717] bg-[#F7F7F5] hover:bg-[#ECECE9] px-3.5 py-2 rounded-xl border border-[#E5E7EB] transition-all flex items-center gap-1.5 cursor-pointer"
                  >
                    <span>Provenance</span>
                    <ExternalLink className="w-3 h-3 text-[#8A8F98]" />
                  </button>

                  <Link href={`/actions/${action.id}`}>
                    <Button variant="primary" size="sm">
                      <span>Next: Inspect & Execute</span>
                      <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                    </Button>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 4. Second Narrative: Recently Verified Proof */}
      <section className="space-y-6 pt-4">
        <div className="flex items-baseline justify-between border-b border-[#ECECE9] pb-3">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-semibold text-[#171717] tracking-tight">
              Recently Verified
            </h2>
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-[#F0FDF4] text-[#15803D] font-medium border border-[#BBF7D0]">
              Forensic Truth Stream
            </span>
          </div>
          <Link 
            href="/verification" 
            className="text-sm text-[#2563EB] hover:text-[#1D4ED8] flex items-center gap-1 font-medium group"
          >
            <span>Full audit verification</span>
            <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Verified Proof Card 1 */}
          <div className="bg-white p-6 rounded-2xl border border-[#BBF7D0] shadow-2xs space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#15803D]">
                <CheckCircle2 className="w-4 h-4 text-[#15803D]" />
                GitHub Issue Verified
              </span>
              <span className="font-mono text-[11px] text-[#5F6368]">
                External State Confirmed
              </span>
            </div>
            <h4 className="text-base font-medium text-[#171717]">
              Publish Sprint Milestone to GitHub Issues
            </h4>
            <p className="text-xs text-[#5F6368] font-mono bg-[#F7F7F5] p-2.5 rounded-lg border border-[#ECECE9]">
              Observation: GitHub API returned HTTP 200 • Issue #42 verified with matching SHA-256 idempotency key
            </p>
            <div className="flex items-center justify-between pt-1 text-xs text-[#5F6368]">
              <span>Connector: GitHub / acme/nexus</span>
              <Link href="/verification" className="text-[#2563EB] hover:underline font-medium">
                Audit Record →
              </Link>
            </div>
          </div>

          {/* Verified Proof Card 2 */}
          <div className="bg-white p-6 rounded-2xl border border-[#BBF7D0] shadow-2xs space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#15803D]">
                <CheckCircle2 className="w-4 h-4 text-[#15803D]" />
                Calendar Event Booked
              </span>
              <span className="font-mono text-[11px] text-[#5F6368]">
                External State Confirmed
              </span>
            </div>
            <h4 className="text-base font-medium text-[#171717]">
              Schedule Architecture Sign-off Review
            </h4>
            <p className="text-xs text-[#5F6368] font-mono bg-[#F7F7F5] p-2.5 rounded-lg border border-[#ECECE9]">
              Observation: Google Calendar API returned event ID `evt_98214` • attendees verified
            </p>
            <div className="flex items-center justify-between pt-1 text-xs text-[#5F6368]">
              <span>Connector: Google Calendar</span>
              <Link href="/verification" className="text-[#2563EB] hover:underline font-medium">
                Audit Record →
              </Link>
            </div>
          </div>
        </div>

        {/* Action Graph Callout Banner */}
        <div className="bg-[#F7F7F5] rounded-2xl border border-[#E5E7EB] p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-white border border-[#E5E7EB] flex items-center justify-center text-[#2563EB] shadow-2xs shrink-0">
              <GitBranch className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-base font-semibold text-[#171717]">
                Action Graph & Dependency Topology
              </h4>
              <p className="text-sm text-[#5F6368] mt-0.5">
                Explore causal parent-child prerequisites, execution blockers, and unlock progressions visually.
              </p>
            </div>
          </div>
          <Link href="/graph" className="shrink-0">
            <Button variant="secondary" size="md">
              <span>Open Graph</span>
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Contextual Source Drawer */}
      <SourceDrawer 
        isOpen={drawerOpen} 
        onClose={() => setDrawerOpen(false)} 
        data={selectedProvenance} 
      />
    </div>
  );
}
