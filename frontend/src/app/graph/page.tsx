"use client";

import React, { useState, useCallback, useMemo } from "react";
import { 
  ReactFlow, 
  Background, 
  Controls, 
  MiniMap, 
  useNodesState, 
  useEdgesState, 
  Node, 
  Edge,
  Handle,
  Position,
  NodeProps
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { SourceDrawer, ProvenanceData } from "@/components/ui/SourceDrawer";
import { 
  PlayCircle, 
  FileText, 
  X
} from "lucide-react";
import Link from "next/link";

interface ActionNodeData {
  title: string;
  status: string;
  priority: string;
  sourceDoc: string;
  sourceLocation: string;
  description: string;
  isFaded?: boolean;
  [key: string]: unknown;
}

// Redesigned large readable React Flow node
function CustomActionNode({ data, selected }: NodeProps) {
  const nodeData = data as unknown as ActionNodeData;
  const isFaded = nodeData.isFaded;

  return (
    <div
      className={`w-72 sm:w-80 bg-white rounded-2xl border text-left p-5 shadow-2xs transition-all duration-200 cursor-pointer ${
        selected 
          ? "border-[#2563EB] ring-4 ring-[#EFF6FF] shadow-md scale-102" 
          : isFaded
          ? "border-[#ECECE9] opacity-40"
          : "border-[#E5E7EB] hover:border-[#D1D5DB]"
      }`}
    >
      <Handle 
        type="target" 
        position={Position.Top} 
        className="!bg-[#8A8F98] !w-2.5 !h-2.5 !border-2 !border-white" 
      />
      
      {/* 1. Status & Priority */}
      <div className="flex items-center justify-between mb-3">
        <StatusBadge status={nodeData.status} size="md" />
        <span className="text-xs font-mono font-semibold text-[#8A8F98] bg-[#F7F7F5] px-2 py-0.5 rounded border border-[#ECECE9]">
          {nodeData.priority}
        </span>
      </div>

      {/* 2. Action Title (Readable 16px) */}
      <h3 className="text-base font-semibold text-[#171717] leading-snug mb-3">
        {nodeData.title}
      </h3>

      {/* 3. Source Grounding Pill */}
      <div className="flex items-center justify-between pt-3 border-t border-[#ECECE9] text-xs text-[#5F6368]">
        <div className="flex items-center gap-1.5 font-mono truncate max-w-[200px]">
          <FileText className="w-3.5 h-3.5 text-[#2563EB] shrink-0" />
          <span className="truncate">{nodeData.sourceDoc}</span>
        </div>
        <span className="font-mono text-[11px] text-[#8A8F98]">spec</span>
      </div>

      <Handle 
        type="source" 
        position={Position.Bottom} 
        className="!bg-[#2563EB] !w-2.5 !h-2.5 !border-2 !border-white" 
      />
    </div>
  );
}

export default function ActionGraphPage() {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [provenanceData, setProvenanceData] = useState<ProvenanceData | null>(null);

  const rawNodes = useMemo(() => [
    {
      id: "node-1",
      type: "actionNode",
      position: { x: 320, y: 40 },
      data: {
        title: "Finish Architecture & Schema Specification",
        status: "verified",
        priority: "P1",
        sourceDoc: "Architecture_Guidelines.pdf",
        sourceLocation: "Page 4 · Section 1",
        description: "Validate database schemas, API schemas, and tenant isolation parameters."
      },
    },
    {
      id: "node-2",
      type: "actionNode",
      position: { x: 80, y: 240 },
      data: {
        title: "Security Perimeter & JWKS Token Audit",
        status: "ready",
        priority: "P1",
        sourceDoc: "Security_Specs.docx",
        sourceLocation: "Page 14 · Section 3.2",
        description: "Review JWT signature check and cryptographic key rotation policy."
      },
    },
    {
      id: "node-3",
      type: "actionNode",
      position: { x: 560, y: 240 },
      data: {
        title: "Connector Ingress & Egress Tooling",
        status: "ready",
        priority: "P2",
        sourceDoc: "Connectors_Plan.md",
        sourceLocation: "Section 2.1",
        description: "Establish safe capability permissions for GitHub and Google Calendar."
      },
    },
    {
      id: "node-4",
      type: "actionNode",
      position: { x: 320, y: 440 },
      data: {
        title: "Deploy Production Release Gateway",
        status: "blocked",
        priority: "P1",
        sourceDoc: "Deployment_Runbook.pdf",
        sourceLocation: "Page 22",
        description: "Promote production services after security audit signoff."
      },
    },
  ], []);

  const initialEdges: Edge[] = [
    {
      id: "e1-2",
      source: "node-1",
      target: "node-2",
      animated: false,
      style: { stroke: "#15803D", strokeWidth: 2 },
    },
    {
      id: "e1-3",
      source: "node-1",
      target: "node-3",
      animated: false,
      style: { stroke: "#15803D", strokeWidth: 2 },
    },
    {
      id: "e2-4",
      source: "node-2",
      target: "node-4",
      animated: true,
      style: { stroke: "#D97706", strokeWidth: 2, strokeDasharray: "5 5" },
    },
    {
      id: "e3-4",
      source: "node-3",
      target: "node-4",
      animated: true,
      style: { stroke: "#2563EB", strokeWidth: 2 },
    },
  ];

  // Apply focus / subtle reduction to unrelated nodes
  const processedNodes = useMemo(() => {
    return rawNodes.map((n) => ({
      ...n,
      data: {
        ...n.data,
        isFaded: selectedNodeId ? selectedNodeId !== n.id : false,
      },
    }));
  }, [rawNodes, selectedNodeId]);

  const [nodes, setNodes, onNodesChange] = useNodesState(processedNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  // Sync node fade states
  React.useEffect(() => {
    setNodes(processedNodes);
  }, [processedNodes, setNodes]);

  const nodeTypes = useMemo(() => ({ actionNode: CustomActionNode }), []);

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNodeId(node.id);
  }, []);

  const selectedNode = rawNodes.find(n => n.id === selectedNodeId);
  const selectedData = selectedNode?.data as ActionNodeData | undefined;

  const handleOpenProvenance = (nodeData: ActionNodeData) => {
    setProvenanceData({
      sourceTitle: nodeData.sourceDoc,
      sourceLocation: nodeData.sourceLocation,
      excerpt: `Identified graph prerequisite for: ${nodeData.title}. Topological ordering requires upstream nodes to be satisfied before child execution.`,
      extractedFacts: [
        "Upstream node state must transition to VERIFIED before child execution",
        "Zero-trust execution policy enforces topological ordering"
      ],
      derivedActionTitle: nodeData.title,
      verificationEvidence: "Verified edge condition in graph ledger",
    });
    setDrawerOpen(true);
  };

  return (
    <div className="space-y-6 h-[calc(100vh-140px)] flex flex-col animate-in fade-in duration-300">
      {/* Editorial Header */}
      <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-4 border-b border-[#ECECE9] pb-4 shrink-0">
        <div>
          <span className="text-xs font-mono font-medium text-[#2563EB] tracking-wider uppercase">
            Dependency Topology
          </span>
          <h1 className="font-display text-4xl text-[#171717] mt-1">
            Action Graph
          </h1>
          <p className="text-sm text-[#5F6368] mt-1">
            Visual map of work: topological ordering, blocked pathways, and verified prerequisites.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/actions">
            <Button variant="secondary" size="md">
              Switch to List View
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Canvas + Contextual Inspector Panel */}
      <div className="flex-1 rounded-2xl border border-[#E5E7EB] bg-[#F7F7F5] overflow-hidden relative flex shadow-2xs">
        {/* Canvas Area */}
        <div className="flex-1 h-full">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            onNodeClick={onNodeClick}
            fitView
            className="bg-[#F7F7F5]"
          >
            <Background color="#D1D5DB" gap={24} size={1} />
            <Controls className="!bg-white !border !border-[#E5E7EB] !shadow-xs !rounded-xl" />
            <MiniMap 
              nodeColor="#E5E7EB" 
              maskColor="rgba(247, 247, 245, 0.7)"
              className="!bg-white !border !border-[#E5E7EB] !rounded-xl"
            />
          </ReactFlow>
        </div>

        {/* Contextual Side Inspector Panel */}
        {selectedNode && selectedData && (
          <div className="w-96 bg-white border-l border-[#E5E7EB] p-6 flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-200 z-10 shadow-lg">
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-[#ECECE9] pb-4">
                <span className="text-xs font-mono font-semibold tracking-wider text-[#8A8F98] uppercase">
                  Node Inspector
                </span>
                <button 
                  onClick={() => setSelectedNodeId(null)}
                  className="p-1 rounded-lg text-[#5F6368] hover:text-[#171717] hover:bg-[#F2F2F0]"
                  aria-label="Close inspector"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2">
                <StatusBadge status={selectedData.status} size="md" />
                <h3 className="font-display text-2xl text-[#171717] mt-2">
                  {selectedData.title}
                </h3>
                <p className="text-sm text-[#5F6368] leading-relaxed">
                  {selectedData.description}
                </p>
              </div>

              {/* Source Provenance Info */}
              <div className="space-y-2 pt-3 border-t border-[#ECECE9]">
                <span className="text-xs font-mono font-semibold text-[#8A8F98] uppercase tracking-wider block">
                  Source Grounding
                </span>
                <div className="p-3.5 rounded-xl bg-[#F7F7F5] border border-[#ECECE9] space-y-1">
                  <div className="text-sm font-semibold text-[#171717] flex items-center gap-2">
                    <FileText className="w-4 h-4 text-[#2563EB]" />
                    {selectedData.sourceDoc}
                  </div>
                  <div className="text-xs font-mono text-[#5F6368]">
                    {selectedData.sourceLocation}
                  </div>
                </div>
              </div>

              {/* Graph Linkage State */}
              <div className="space-y-2 pt-3 border-t border-[#ECECE9] text-xs">
                <span className="text-xs font-mono font-semibold text-[#8A8F98] uppercase tracking-wider block">
                  Topological Status
                </span>
                <div className="p-3 rounded-xl bg-[#F7F7F5] border border-[#ECECE9] flex items-center justify-between">
                  <span className="text-sm text-[#5F6368]">Prerequisites:</span>
                  <span className="font-mono text-xs font-semibold text-[#15803D]">
                    Topologically Validated
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-6 border-t border-[#ECECE9] space-y-3">
              <Button 
                variant="outline" 
                size="md" 
                className="w-full justify-center"
                onClick={() => handleOpenProvenance(selectedData)}
              >
                <FileText className="w-4 h-4 mr-2 text-[#2563EB]" />
                Inspect Provenance
              </Button>

              <Link href="/execution" className="block">
                <Button 
                  variant="primary" 
                  size="md" 
                  className="w-full justify-center"
                >
                  <PlayCircle className="w-4 h-4 mr-2" />
                  Dispatch Execution
                </Button>
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Source Context Drawer */}
      <SourceDrawer 
        isOpen={drawerOpen} 
        onClose={() => setDrawerOpen(false)} 
        data={provenanceData} 
      />
    </div>
  );
}
