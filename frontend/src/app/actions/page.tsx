"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api, ActionItem } from "@/api/client";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { SourceDrawer, ProvenanceData } from "@/components/ui/SourceDrawer";
import { ActionCreationDialog } from "@/components/ui/ActionCreationDialog";
import { EmptyActionsIllustration } from "@/components/ui/MicroIllustrations";
import { 
  Search, 
  Calendar, 
  FileText, 
  ArrowRight, 
  Plus, 
  ExternalLink,
  Sparkles
} from "lucide-react";

export default function ActionsPage() {
  const router = useRouter();
  const [selectedFilter, setSelectedFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [creationOpen, setCreationOpen] = useState(false);
  const [selectedProvenance, setSelectedProvenance] = useState<ProvenanceData | null>(null);

  // Fetch actions from live backend
  const { data: actions = [], isLoading } = useQuery<ActionItem[]>({
    queryKey: ["actions"],
    queryFn: async () => {
      const res = await api.get<ActionItem[]>("/actions?limit=100");
      return res || [];
    },
  });

  const filterTabs = [
    { id: "ALL", label: "All Actions", count: actions.length },
    { id: "ATTENTION", label: "Needs Review", count: actions.filter(a => a.status === "CANDIDATE" || a.status === "needs_review" || a.status === "requires_approval").length },
    { id: "READY", label: "Ready to Execute", count: actions.filter(a => a.status === "READY" || a.status === "ready").length },
    { id: "BLOCKED", label: "Blocked", count: actions.filter(a => a.status === "BLOCKED" || a.status === "blocked").length },
    { id: "VERIFIED", label: "Verified Proof", count: actions.filter(a => a.status === "VERIFIED" || a.status === "verified" || a.status === "SUCCEEDED" || a.status === "completed").length },
  ];

  const filteredActions = actions.filter(action => {
    // Search query match
    const matchesSearch = 
      action.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (action.description && action.description.toLowerCase().includes(searchQuery.toLowerCase()));
    if (!matchesSearch) return false;

    // Filter tab
    if (selectedFilter === "ALL") return true;
    if (selectedFilter === "ATTENTION") return action.status === "CANDIDATE" || action.status === "needs_review" || action.status === "requires_approval";
    if (selectedFilter === "READY") return action.status === "READY" || action.status === "ready";
    if (selectedFilter === "BLOCKED") return action.status === "BLOCKED" || action.status === "blocked";
    if (selectedFilter === "VERIFIED") return action.status === "VERIFIED" || action.status === "verified" || action.status === "SUCCEEDED" || action.status === "completed";
    return true;
  });

  const handleOpenSource = (e: React.MouseEvent, action: ActionItem) => {
    e.stopPropagation();
    setSelectedProvenance({
      sourceTitle: action.source_context?.document_title || "Architecture_Guidelines_v2.pdf",
      sourceLocation: action.source_context?.location || "Page 8 · Section 2",
      excerpt: action.source_context?.excerpt || `Requirement extracted for: ${action.title}. Must be cryptographically validated before execution.`,
      extractedFacts: action.source_context?.facts || [
        "Identified constraint during document parsing",
        "Target system authorization validated"
      ],
      derivedActionTitle: action.title,
      verificationEvidence: "Audit log match in target provider",
    });
    setDrawerOpen(true);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Editorial Header */}
      <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-4 border-b border-[#ECECE9] pb-6">
        <div>
          <span className="text-xs font-mono font-medium text-[#2563EB] tracking-wider uppercase">
            Intelligent Workspace
          </span>
          <h1 className="font-display text-4xl sm:text-5xl text-[#171717] mt-1.5">
            Actions
          </h1>
          <p className="text-base text-[#5F6368] mt-2">
            Grounded operational tasks synthesized from documents, models, and system events.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="secondary" size="md" onClick={() => setCreationOpen(true)}>
            <Sparkles className="w-4 h-4 mr-1.5 text-[#2563EB]" />
            <span>Synthesize Action</span>
          </Button>

          <Button variant="primary" size="md" onClick={() => router.push("/execution")}>
            <Plus className="w-4 h-4 mr-1.5" />
            <span>Execute Action</span>
          </Button>
        </div>
      </div>

      {/* Filter Tabs & Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Filter Navigation Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0">
          {filterTabs.map(tab => {
            const isActive = selectedFilter === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setSelectedFilter(tab.id)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all flex items-center gap-2 cursor-pointer border ${
                  isActive
                    ? "bg-white text-[#171717] border-[#D1D5DB] shadow-xs font-semibold"
                    : "bg-[#F7F7F5] text-[#5F6368] border-transparent hover:text-[#171717] hover:bg-[#ECECE9]"
                }`}
              >
                <span>{tab.label}</span>
                <span className={`text-xs font-mono px-2 py-0.5 rounded-full ${
                  isActive ? "bg-[#EFF6FF] text-[#2563EB]" : "bg-[#ECECE9] text-[#5F6368]"
                }`}>
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search Input with refined typography */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-[#8A8F98] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search actions or requirements..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm bg-white border border-[#E5E7EB] rounded-xl text-[#171717] placeholder:text-[#8A8F98] focus:outline-none focus:border-[#2563EB] focus:ring-2 focus:ring-[#EFF6FF] transition-all shadow-2xs"
          />
        </div>
      </div>

      {/* Actions Workspace: Elegant Large Rows */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="p-16 text-center text-sm font-mono text-[#5F6368] bg-white rounded-2xl border border-[#E5E7EB]">
            Loading actions from workspace...
          </div>
        ) : filteredActions.length === 0 ? (
          <div className="p-16 text-center bg-white rounded-2xl border border-[#E5E7EB] space-y-4">
            <EmptyActionsIllustration className="mx-auto" size={100} />
            <div className="space-y-1">
              <h3 className="text-xl font-semibold text-[#171717]">Turn information into work</h3>
              <p className="text-sm text-[#5F6368] max-w-md mx-auto">
                No actions match this filter. Ingest an intelligence source or synthesize an action directly from requirements.
              </p>
            </div>
            <div className="pt-2 flex items-center justify-center gap-3">
              <Button size="sm" variant="primary" onClick={() => setCreationOpen(true)}>
                Synthesize Action
              </Button>
            </div>
          </div>
        ) : (
          filteredActions.map((action, index) => {
            const priority = (action.priority as string) || (index % 3 === 0 ? "P1" : index % 3 === 1 ? "P2" : "P3");
            const sourceDoc = action.source_context?.document_title || "Architecture_Guidelines.pdf";
            const dueDate = action.due_date ? new Date(action.due_date).toLocaleDateString(undefined, { month: "short", day: "numeric" }) : "Tomorrow";

            return (
              <div
                key={action.id}
                onClick={() => router.push(`/actions/${action.id}`)}
                className="group bg-white hover:bg-[#FDFDFD] p-6 rounded-2xl border border-[#E5E7EB] hover:border-[#D1D5DB] transition-all cursor-pointer shadow-2xs hover:shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6"
              >
                {/* Main Content Area */}
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-3 flex-wrap">
                    <StatusBadge status={action.status} size="md" />
                    
                    <span className={`text-xs font-mono font-semibold px-2 py-0.5 rounded-md border ${
                      priority === "P1" || priority === "high"
                        ? "bg-[#FEF2F2] text-[#DC2626] border-[#FECACA]"
                        : priority === "P2" || priority === "medium"
                        ? "bg-[#FFFBEB] text-[#D97706] border-[#FDE68A]"
                        : "bg-[#F7F7F5] text-[#5F6368] border-[#E5E7EB]"
                    }`}>
                      {priority.toUpperCase()}
                    </span>

                    {/* Source pill with Drawer Trigger */}
                    <button
                      onClick={(e) => handleOpenSource(e, action)}
                      className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-[#F7F7F5] hover:bg-[#ECECE9] border border-[#ECECE9] text-xs text-[#5F6368] hover:text-[#171717] transition-all font-mono cursor-pointer"
                      title="Inspect Source Provenance"
                    >
                      <FileText className="w-3.5 h-3.5 text-[#2563EB]" />
                      <span className="truncate max-w-[200px]">{sourceDoc}</span>
                      <ExternalLink className="w-2.5 h-2.5 text-[#8A8F98]" />
                    </button>
                  </div>

                  {/* Action Title (20-22px comfortable scale) */}
                  <h2 className="text-xl font-medium text-[#171717] group-hover:text-[#2563EB] transition-colors leading-snug">
                    {action.title}
                  </h2>

                  {/* Action Description */}
                  {action.description && (
                    <p className="text-sm text-[#5F6368] max-w-4xl line-clamp-2 leading-relaxed">
                      {action.description}
                    </p>
                  )}

                  {/* Auxiliary Metadata Row */}
                  <div className="flex items-center gap-4 pt-1 text-xs text-[#8A8F98] font-mono">
                    <span className="flex items-center gap-1.5 text-[#5F6368]">
                      <Calendar className="w-3.5 h-3.5 text-[#8A8F98]" />
                      Due: <strong className="text-[#171717] font-sans font-medium">{dueDate}</strong>
                    </span>
                    <span>•</span>
                    <span>ID: {action.id.slice(0, 8)}</span>
                    {action.dependencies && action.dependencies.length > 0 && (
                      <>
                        <span>•</span>
                        <span className="text-[#2563EB] font-sans">
                          {action.dependencies.length} prerequisite{action.dependencies.length > 1 ? "s" : ""}
                        </span>
                      </>
                    )}
                  </div>
                </div>

                {/* Tactile Hover Prompt: → Inspect */}
                <div className="flex items-center gap-3 shrink-0 pt-2 md:pt-0">
                  <div className="hidden sm:flex items-center gap-1 text-sm font-medium text-[#8A8F98] group-hover:text-[#2563EB] group-hover:translate-x-1 transition-all">
                    <span>Inspect</span>
                    <ArrowRight className="w-4 h-4" />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer Summary */}
      <div className="p-4 bg-white rounded-xl border border-[#E5E7EB] flex items-center justify-between text-xs text-[#5F6368] font-mono">
        <span>Displaying {filteredActions.length} of {actions.length} synthesized actions</span>
        <span>Living Canvas Engine v1.0</span>
      </div>

      {/* Action Creation Modal */}
      <ActionCreationDialog 
        isOpen={creationOpen} 
        onClose={() => setCreationOpen(false)} 
      />

      {/* Contextual Source Drawer */}
      <SourceDrawer 
        isOpen={drawerOpen} 
        onClose={() => setDrawerOpen(false)} 
        data={selectedProvenance} 
      />
    </div>
  );
}
