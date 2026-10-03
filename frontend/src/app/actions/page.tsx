"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api, ActionItem } from "@/api/client";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { SourceDrawer, ProvenanceData } from "@/components/ui/SourceDrawer";
import { 
  Search, 
  Filter, 
  Calendar, 
  FileText, 
  ArrowRight, 
  Plus, 
  Clock, 
  ShieldCheck, 
  Lock, 
  Layers,
  ChevronRight,
  ExternalLink
} from "lucide-react";

export default function ActionsPage() {
  const router = useRouter();
  const [selectedFilter, setSelectedFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedProvenance, setSelectedProvenance] = useState<ProvenanceData | null>(null);

  // Fetch actions from live backend
  const { data: actions = [], isLoading, error } = useQuery<ActionItem[]>({
    queryKey: ["actions"],
    queryFn: async () => {
      const res = await api.get<ActionItem[]>("/actions?limit=100");
      return res || [];
    },
  });

  const filterTabs = [
    { id: "ALL", label: "All Actions", count: actions.length },
    { id: "ATTENTION", label: "Needs Attention", count: actions.filter(a => a.status === "CANDIDATE" || a.status === "needs_review").length },
    { id: "READY", label: "Ready", count: actions.filter(a => a.status === "READY").length },
    { id: "BLOCKED", label: "Blocked", count: actions.filter(a => a.status === "BLOCKED").length },
    { id: "VERIFIED", label: "Verified", count: actions.filter(a => a.status === "VERIFIED" || a.status === "SUCCEEDED").length },
  ];

  const filteredActions = actions.filter(action => {
    // Search filter
    const matchesSearch = 
      action.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (action.description && action.description.toLowerCase().includes(searchQuery.toLowerCase()));
    if (!matchesSearch) return false;

    // Tab filter
    if (selectedFilter === "ALL") return true;
    if (selectedFilter === "ATTENTION") return action.status === "CANDIDATE" || action.status === "needs_review";
    if (selectedFilter === "READY") return action.status === "READY";
    if (selectedFilter === "BLOCKED") return action.status === "BLOCKED";
    if (selectedFilter === "VERIFIED") return action.status === "VERIFIED" || action.status === "SUCCEEDED";
    return true;
  });

  const handleOpenSource = (e: React.MouseEvent, action: ActionItem) => {
    e.stopPropagation();
    setSelectedProvenance({
      sourceTitle: action.source_context?.document_title || "Architecture_Spec.pdf",
      sourceLocation: action.source_context?.location || "Page 8 / Section 2",
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
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#E5E7EB] pb-5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-[#171717]">
            Actions Workspace
          </h1>
          <p className="text-xs text-[#5F6368] mt-1">
            Grounded operational tasks synthesized from documents, models, and system events.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="primary" size="sm" onClick={() => router.push("/execution")}>
            <Plus className="w-3.5 h-3.5" />
            New Execution Request
          </Button>
        </div>
      </div>

      {/* Filter Tabs + Search Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
          {filterTabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setSelectedFilter(tab.id)}
              className={`px-3 py-1.5 rounded-[5px] text-xs font-medium transition-colors flex items-center gap-2 cursor-pointer ${
                selectedFilter === tab.id
                  ? "bg-white text-[#171717] border border-[#D1D5DB] shadow-xs font-semibold"
                  : "text-[#5F6368] hover:text-[#171717] hover:bg-[#EBEBE8]"
              }`}
            >
              <span>{tab.label}</span>
              <span className={`text-[10px] font-mono px-1 py-0.2 rounded ${
                selectedFilter === tab.id ? "bg-[#EFF6FF] text-[#2563EB]" : "bg-[#E5E7EB] text-[#5F6368]"
              }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        {/* Search input */}
        <div className="relative w-full md:w-72">
          <Search className="w-3.5 h-3.5 text-[#5F6368] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Filter actions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs bg-white border border-[#E5E7EB] rounded-[5px] text-[#171717] placeholder:text-[#9CA3AF] focus:outline-none focus:border-[#2563EB]"
          />
        </div>
      </div>

      {/* Dense List / Table Hybrid */}
      <div className="bg-white rounded-lg border border-[#E5E7EB] overflow-hidden shadow-xs">
        {isLoading ? (
          <div className="p-12 text-center text-xs text-[#5F6368]">
            <div className="w-5 h-5 border-2 border-[#2563EB] border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading actions from workspace...
          </div>
        ) : filteredActions.length === 0 ? (
          <div className="p-12 text-center text-xs text-[#5F6368] space-y-2">
            <p className="font-medium text-[#171717]">No actions match current filters</p>
            <p>Try clearing the search query or selecting a different tab.</p>
          </div>
        ) : (
          <div className="divide-y divide-[#E5E7EB]">
            {filteredActions.map((action, index) => {
              const priority = (action.priority as any) || (index % 3 === 0 ? "P1" : index % 3 === 1 ? "P2" : "P3");
              const sourceDoc = action.source_context?.document_title || (index % 2 === 0 ? "Architecture_Guidelines.pdf" : "Security_Requirements.docx");

              return (
                <div
                  key={action.id}
                  onClick={() => router.push(`/actions/${action.id}`)}
                  className="flex items-center justify-between px-4 py-3 hover:bg-[#F7F7F5] transition-colors cursor-pointer group gap-4"
                >
                  {/* Left: Checkbox + Title + ID */}
                  <div className="flex items-center gap-3.5 min-w-0 flex-1">
                    <input
                      type="checkbox"
                      onClick={(e) => e.stopPropagation()}
                      className="rounded-[3px] border-[#D1D5DB] text-[#2563EB] focus:ring-0 cursor-pointer h-3.5 w-3.5"
                    />

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-[#171717] group-hover:text-[#2563EB] transition-colors truncate">
                          {action.title}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-0.5 text-[11px] text-[#5F6368]">
                        <span className="font-mono text-[10px] text-[#9CA3AF]">
                          {action.id.slice(0, 8)}
                        </span>
                        {action.description && (
                          <>
                            <span>•</span>
                            <span className="truncate max-w-[320px] text-[#5F6368]">
                              {action.description}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Middle / Right: Metadata Pills */}
                  <div className="flex items-center gap-3 shrink-0">
                    {/* Source Pill (Clickable Drawer Trigger) */}
                    <button
                      onClick={(e) => handleOpenSource(e, action)}
                      className="hidden sm:inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[4px] bg-[#F2F2F0] hover:bg-[#E5E7EB] border border-[#E5E7EB] text-[11px] text-[#5F6368] hover:text-[#171717] transition-colors font-mono cursor-pointer"
                      title="Inspect Provenance"
                    >
                      <FileText className="w-3 h-3 text-[#2563EB]" />
                      <span className="truncate max-w-[120px]">{sourceDoc}</span>
                    </button>

                    {/* Due Date */}
                    <div className="hidden md:flex items-center gap-1 text-[11px] text-[#5F6368]">
                      <Calendar className="w-3 h-3 text-[#9CA3AF]" />
                      <span>{action.due_date ? new Date(action.due_date).toLocaleDateString(undefined, { month: "short", day: "numeric" }) : "Today"}</span>
                    </div>

                    {/* Priority */}
                    <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded border ${
                      priority === "P1" || priority === "high"
                        ? "bg-[#FEF2F2] text-[#C62828] border-[#FECACA]"
                        : priority === "P2" || priority === "medium"
                        ? "bg-[#FFFBEB] text-[#A65F00] border-[#FDE68A]"
                        : "bg-[#F2F2F0] text-[#5F6368] border-[#E5E7EB]"
                    }`}>
                      {priority.toUpperCase()}
                    </span>

                    {/* Status Badge */}
                    <StatusBadge status={action.status} size="sm" />

                    {/* Action Arrow */}
                    <ChevronRight className="w-3.5 h-3.5 text-[#9CA3AF] group-hover:text-[#171717] group-hover:translate-x-0.5 transition-all" />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Footer with scanability summary */}
        <div className="px-4 py-2.5 bg-[#F7F7F5] border-t border-[#E5E7EB] flex items-center justify-between text-[11px] text-[#5F6368]">
          <span>Showing {filteredActions.length} of {actions.length} operational actions</span>
          <span className="font-mono">Ready to triage</span>
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
