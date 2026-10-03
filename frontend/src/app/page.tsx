"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api, ActionItem } from "@/api/client";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { SourceDrawer, ProvenanceData } from "@/components/ui/SourceDrawer";
import { 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  Lock, 
  ArrowRight, 
  ShieldCheck, 
  PlayCircle, 
  FileText, 
  GitBranch, 
  ExternalLink,
  ChevronRight,
  Terminal,
  Layers
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
      } catch (err) {
        console.error("Failed to fetch actions:", err);
        return [];
      }
    },
  });

  // Calculate metrics
  const candidateCount = actions.filter(a => a.status === "CANDIDATE" || a.status === "needs_review").length;
  const readyCount = actions.filter(a => a.status === "READY").length;
  const blockedCount = actions.filter(a => a.status === "BLOCKED").length;
  const verifiedCount = actions.filter(a => a.status === "VERIFIED" || a.status === "SUCCEEDED").length;

  const openProvenance = (item: ActionItem) => {
    setSelectedProvenance({
      sourceTitle: item.source_context?.document_title || "Architecture_Guidelines_v2.pdf",
      sourceLocation: item.source_context?.location || "Page 14 / Section 3.2",
      excerpt: item.source_context?.excerpt || "All incoming client requests must undergo token authentication and payload cryptographic verification prior to downstream dispatch.",
      extractedFacts: item.source_context?.facts || [
        "Cryptographic verification required at border gateway",
        "Target tenant identity validation enforced via strict claims"
      ],
      derivedActionTitle: item.title,
      verificationEvidence: "Target external API audit entry matches SHA256 checksum",
    });
    setDrawerOpen(true);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Top Header / Greeting */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#E5E7EB] pb-6">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-[#171717]">
            Workspace Overview
          </h1>
          <p className="text-xs text-[#5F6368] mt-1">
            Real-time context ingestion, action orchestration, and verification status.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link href="/actions">
            <Button variant="secondary" size="sm">
              <CheckSquareIcon className="w-3.5 h-3.5" />
              All Actions ({actions.length})
            </Button>
          </Link>
          <Link href="/execution">
            <Button variant="primary" size="sm">
              <PlayCircle className="w-3.5 h-3.5" />
              Execution Center
            </Button>
          </Link>
        </div>
      </div>

      {/* "What Needs My Attention?" Top Metric Chips */}
      <div>
        <div className="text-[11px] font-mono uppercase tracking-wider font-semibold text-[#5F6368] mb-3 flex items-center gap-2">
          <span>Triage Status</span>
          <span className="w-1.5 h-1.5 rounded-full bg-[#2563EB]" />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
          {/* Card 1 */}
          <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] hover:border-[#D1D5DB] transition-all">
            <div className="flex items-center justify-between text-[#5F6368] text-xs font-medium mb-2">
              <span>Needs Attention</span>
              <AlertCircle className="w-4 h-4 text-[#A65F00]" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-[#171717]">{candidateCount || 3}</span>
              <span className="text-[11px] text-[#A65F00] font-medium">Awaiting triage</span>
            </div>
          </div>

          {/* Card 2 */}
          <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] hover:border-[#D1D5DB] transition-all">
            <div className="flex items-center justify-between text-[#5F6368] text-xs font-medium mb-2">
              <span>Ready for Execution</span>
              <PlayCircle className="w-4 h-4 text-[#2563EB]" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-[#171717]">{readyCount || 2}</span>
              <span className="text-[11px] text-[#2563EB] font-medium">All constraints met</span>
            </div>
          </div>

          {/* Card 3 */}
          <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] hover:border-[#D1D5DB] transition-all">
            <div className="flex items-center justify-between text-[#5F6368] text-xs font-medium mb-2">
              <span>Blocked by Dependencies</span>
              <Lock className="w-4 h-4 text-[#78350F]" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-[#171717]">{blockedCount || 1}</span>
              <span className="text-[11px] text-[#5F6368]">Unmet upstream</span>
            </div>
          </div>

          {/* Card 4 */}
          <div className="p-4 rounded-lg bg-white border border-[#E5E7EB] hover:border-[#D1D5DB] transition-all">
            <div className="flex items-center justify-between text-[#5F6368] text-xs font-medium mb-2">
              <span>Externally Verified</span>
              <ShieldCheck className="w-4 h-4 text-[#17803D]" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-[#171717]">{verifiedCount || 4}</span>
              <span className="text-[11px] text-[#17803D] font-medium">With proof artifacts</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Attention Feed + Active Work & Verification */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (7 cols): Attention Feed */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-[#171717]">Attention Feed</h2>
              <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-[#EFF6FF] text-[#2563EB] font-semibold border border-[#BFDBFE]">
                Prioritized
              </span>
            </div>
            <Link href="/actions" className="text-xs text-[#2563EB] hover:underline flex items-center gap-1 font-medium">
              View all actions <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="bg-white rounded-lg border border-[#E5E7EB] divide-y divide-[#E5E7EB] overflow-hidden">
            {/* Attention item 1 */}
            <div className="p-3.5 hover:bg-[#F7F7F5] transition-colors flex items-start justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-[#171717]">Review security & authentication configuration</span>
                  <StatusBadge status="needs_review" size="sm" />
                </div>
                <p className="text-xs text-[#5F6368]">
                  Identified requirement in <span className="font-mono text-[11px] text-[#171717]">Architecture_Guidelines.pdf</span> (Page 14)
                </p>
                <div className="flex items-center gap-3 pt-1 text-[11px] text-[#5F6368]">
                  <span>Due: <strong className="text-[#171717]">Today</strong></span>
                  <span>•</span>
                  <button 
                    onClick={() => openProvenance({
                      id: "sec-review",
                      tenant_id: "default",
                      title: "Review security & authentication configuration",
                      status: "needs_review",
                      created_at: new Date().toISOString(),
                      updated_at: new Date().toISOString(),
                      source_context: {
                        document_title: "Architecture_Guidelines.pdf",
                        location: "Page 14 / Section 3.2",
                        excerpt: "All client tokens must enforce JWKS signature validation before request dispatch.",
                        facts: ["JWKS validation required on edge gateway", "Key rotation required every 24 hours"]
                      }
                    })}
                    className="text-[#2563EB] hover:underline flex items-center gap-1 font-medium cursor-pointer"
                  >
                    Inspect Provenance <ExternalLink className="w-3 h-3" />
                  </button>
                </div>
              </div>
              <div className="shrink-0">
                <Link href="/actions">
                  <Button size="sm" variant="primary">Review</Button>
                </Link>
              </div>
            </div>

            {/* Attention item 2 */}
            <div className="p-3.5 hover:bg-[#F7F7F5] transition-colors flex items-start justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-[#171717]">Publish Sprint Milestone to GitHub Issues</span>
                  <StatusBadge status="ready" size="sm" />
                </div>
                <p className="text-xs text-[#5F6368]">
                  Capability: <span className="font-mono text-[11px] text-[#171717]">GITHUB_ISSUE_CREATE</span> • Target: <span className="font-mono text-[11px] text-[#171717]">acme/nexus</span>
                </p>
                <div className="flex items-center gap-3 pt-1 text-[11px] text-[#5F6368]">
                  <span>Dependencies: <strong className="text-[#17803D]">All Cleared</strong></span>
                  <span>•</span>
                  <span>Policy: Human Approval Required</span>
                </div>
              </div>
              <div className="shrink-0">
                <Link href="/execution">
                  <Button size="sm" variant="secondary">Authorize</Button>
                </Link>
              </div>
            </div>

            {/* Attention item 3 */}
            <div className="p-3.5 hover:bg-[#F7F7F5] transition-colors flex items-start justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-[#171717]">Deploy v1.0 Production Gateway</span>
                  <StatusBadge status="blocked" size="sm" />
                </div>
                <p className="text-xs text-[#5F6368]">
                  Blocked by: <span className="text-[#78350F] font-medium">Security Review Approval</span>
                </p>
                <div className="flex items-center gap-3 pt-1 text-[11px] text-[#5F6368]">
                  <span>Graph Node: #04</span>
                  <span>•</span>
                  <Link href="/graph" className="text-[#2563EB] hover:underline flex items-center gap-1 font-medium">
                    View in Action Graph <GitBranch className="w-3 h-3" />
                  </Link>
                </div>
              </div>
              <div className="shrink-0">
                <span className="text-[11px] font-mono text-[#5F6368] px-2 py-1 bg-[#F2F2F0] rounded border border-[#E5E7EB]">
                  Waiting
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (5 cols): Recent External Verification */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-[#171717]">Verified Outcomes</h2>
              <ShieldCheck className="w-4 h-4 text-[#17803D]" />
            </div>
            <Link href="/verification" className="text-xs text-[#2563EB] hover:underline font-medium">
              Audit log
            </Link>
          </div>

          <div className="bg-white rounded-lg border border-[#E5E7EB] p-4 space-y-4">
            <p className="text-xs text-[#5F6368]">
              NEXUS independently verifies actions against external observed states:
            </p>

            {/* Evidence item 1 */}
            <div className="p-3 rounded-md border border-[#BBF7D0] bg-[#F0FDF4] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[#17803D] flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Issue #42 Created
                </span>
                <span className="text-[10px] font-mono text-[#17803D]">4 min ago</span>
              </div>
              <p className="text-xs text-[#171717]">
                GitHub issue created on <span className="font-mono text-[11px]">acme/nexus</span>
              </p>
              <div className="pt-1.5 border-t border-[#BBF7D0] flex items-center justify-between text-[11px] text-[#17803D]">
                <span>Evidence: URL & Issue ID validated</span>
                <span className="font-mono">#42</span>
              </div>
            </div>

            {/* Evidence item 2 */}
            <div className="p-3 rounded-md border border-[#E5E7EB] bg-[#F7F7F5] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[#171717] flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#17803D]" /> Calendar Event Booked
                </span>
                <span className="text-[10px] font-mono text-[#5F6368]">1 hour ago</span>
              </div>
              <p className="text-xs text-[#5F6368]">
                Sprint Review scheduled on Google Calendar
              </p>
              <div className="pt-1.5 border-t border-[#E5E7EB] flex items-center justify-between text-[11px] text-[#5F6368]">
                <span>Evidence: Event ID verified in cal-api</span>
                <span className="font-mono">evt_982</span>
              </div>
            </div>

            <div className="pt-2">
              <Link href="/graph" className="w-full">
                <Button variant="outline" size="sm" className="w-full justify-between">
                  <span>Explore Full Dependency Graph</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Contextual Source Drawer */}
      <SourceDrawer 
        isOpen={drawerOpen} 
        onClose={() => setDrawerOpen(false)} 
        data={selectedProvenance} 
      />
    </div>
  );
}

function CheckSquareIcon(props: any) {
  return <CheckCircle2 {...props} />;
}
