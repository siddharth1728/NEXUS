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
  GitBranch, 
  CheckCircle2, 
  Clock, 
  Lock, 
  PlayCircle, 
  FileText, 
  ArrowRight, 
  X,
  ExternalLink,
  ShieldCheck,
  Info
} from "lucide-react";
import Link from "next/link";

interface ActionNodeData {
  title: string;
  status: string;
  priority: string;
  sourceDoc: string;
  sourceLocation: string;
  description: string;
  [key: string]: unknown;
}

// Custom restrained React Flow node component
function CustomActionNode({ data, selected }: NodeProps) {
  const nodeData = data as unknown as ActionNodeData;
  return (
    <div
      className={`w-64 bg-white rounded-lg border text-left p-3.5 shadow-xs transition-all cursor-pointer ${
        selected ? "border-[#2563EB] ring-2 ring-[#2563EB]/20 shadow-md" : "border-[#E5E7EB] hover:border-[#D1D5DB]"
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-[#9CA3AF] !w-2 !h-2" />
      
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-mono text-[#5F6368] font-bold">
          {nodeData.priority}
        </span>
        <StatusBadge status={nodeData.status} size="sm" />
      </div>

      <div className="text-xs font-semibold text-[#171717] line-clamp-2 leading-snug mb-2">
        {nodeData.title}
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-[#E5E7EB] text-[10px] text-[#5F6368]">
        <div className="flex items-center gap-1 font-mono truncate max-w-[150px]">
          <FileText className="w-3 h-3 text-[#2563EB] shrink-0" />
          <span className="truncate">{nodeData.sourceDoc}</span>
        </div>
        <span className="font-mono">spec</span>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-[#2563EB] !w-2 !h-2" />
    </div>
  );
}

export default function ActionGraphPage() {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [provenanceData, setProvenanceData] = useState<ProvenanceData | null>(null);

  const initialNodes: Node[] = [
    {
      id: "node-1",
      type: "actionNode",
      position: { x: 300, y: 50 },
      data: {
        title: "Finish Architecture & Schema Specification",
        status: "verified",
        priority: "P1",
        sourceDoc: "Architecture_Guidelines.pdf",
        sourceLocation: "Page 4 / Section 1",
        description: "Validate database schemas, API schemas, and tenant isolation parameters."
      },
    },
    {
      id: "node-2",
      type: "actionNode",
      position: { x: 100, y: 220 },
      data: {
        title: "Security Perimeter & JWKS Token Audit",
        status: "ready",
        priority: "P1",
        sourceDoc: "Security_Specs.docx",
        sourceLocation: "Page 14 / Section 3.2",
        description: "Review JWT signature check and cryptographic key rotation policy."
      },
    },
    {
      id: "node-3",
      type: "actionNode",
      position: { x: 500, y: 220 },
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
      position: { x: 300, y: 390 },
      data: {
        title: "Deploy Production Release Gateway",
        status: "blocked",
        priority: "P1",
        sourceDoc: "Deployment_Runbook.pdf",
        sourceLocation: "Page 22",
        description: "Promote production services after security audit signoff."
      },
    },
  ];

  const initialEdges: Edge[] = [
    {
      id: "e1-2",
      source: "node-1",
      target: "node-2",
      animated: false,
      style: { stroke: "#17803D", strokeWidth: 1.5 },
    },
    {
      id: "e1-3",
      source: "node-1",
      target: "node-3",
      animated: false,
      style: { stroke: "#17803D", strokeWidth: 1.5 },
    },
    {
      id: "e2-4",
      source: "node-2",
      target: "node-4",
      animated: true,
      style: { stroke: "#A65F00", strokeWidth: 1.5, strokeDasharray: "4 4" },
    },
    {
      id: "e3-4",
      source: "node-3",
      target: "node-4",
      animated: true,
      style: { stroke: "#2563EB", strokeWidth: 1.5 },
    },
  ];

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const nodeTypes = useMemo(() => ({ actionNode: CustomActionNode }), []);

  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedNode(node);
  }, []);

  const handleOpenProvenance = (nodeData: ActionNodeData) => {
    setProvenanceData({
      sourceTitle: nodeData.sourceDoc,
      sourceLocation: nodeData.sourceLocation,
      excerpt: `Identified graph prerequisite for: ${nodeData.title}. System cannot proceed without satisfying parent edges.`,
      extractedFacts: [
        "Upstream node state must transition to VERIFIED before child execution",
        "Zero-trust execution policy enforces topological ordering"
      ],
      derivedActionTitle: nodeData.title,
      verificationEvidence: "Verified edge condition in graph ledger",
    });
    setDrawerOpen(true);
  };

  const selectedData = selectedNode?.data as unknown as ActionNodeData | undefined;

  return (
    <div className="space-y-6 h-[calc(100vh-140px)] flex flex-col animate-in fade-in duration-150">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#E5E7EB] pb-4 shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-[#171717]">
              Interactive Action Graph
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#EFF6FF] text-[#2563EB] font-semibold border border-[#BFDBFE]">
              Dependency Topology
            </span>
          </div>
          <p className="text-xs text-[#5F6368] mt-1">
            Visual map of work: topological dependency order, blocked pathways, and verified nodes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/actions">
            <Button variant="secondary" size="sm">
              List View
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Canvas + Contextual Inspector Panel */}
      <div className="flex-1 rounded-lg border border-[#E5E7EB] bg-[#F7F7F5] overflow-hidden relative flex">
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
            <Background color="#D1D5DB" gap={20} size={1} />
            <Controls className="!bg-white !border !border-[#E5E7EB] !shadow-xs !rounded-md" />
            <MiniMap 
              nodeColor="#E5E7EB" 
              maskColor="rgba(247, 247, 245, 0.7)"
              className="!bg-white !border !border-[#E5E7EB] !rounded-md"
            />
          </ReactFlow>
        </div>

        {/* Contextual Side Inspector Panel (opens when node selected) */}
        {selectedNode && selectedData && (
          <div className="w-80 bg-white border-l border-[#E5E7EB] p-5 flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-150 z-10 shadow-lg">
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-[#E5E7EB] pb-3">
                <span className="text-[10px] font-mono uppercase font-bold text-[#5F6368]">
                  Node Inspector
                </span>
                <button 
                  onClick={() => setSelectedNode(null)}
                  className="p-1 rounded text-[#5F6368] hover:text-[#171717] hover:bg-[#F2F2F0]"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              <div>
                <StatusBadge status={selectedData.status} size="sm" />
                <h3 className="text-sm font-bold text-[#171717] mt-2">
                  {selectedData.title}
                </h3>
                <p className="text-xs text-[#5F6368] mt-1 leading-relaxed">
                  {selectedData.description}
                </p>
              </div>

              <div className="space-y-2 pt-2 border-t border-[#E5E7EB] text-xs">
                <span className="text-[10px] font-mono uppercase tracking-wider text-[#5F6368] block">
                  SOURCE GROUNDING
                </span>
                <div className="p-2.5 rounded bg-[#F7F7F5] border border-[#E5E7EB] text-xs">
                  <div className="font-medium text-[#171717] flex items-center gap-1.5">
                    <FileText className="w-3 h-3 text-[#2563EB]" />
                    {selectedData.sourceDoc}
                  </div>
                  <div className="text-[11px] font-mono text-[#5F6368] mt-0.5">
                    {selectedData.sourceLocation}
                  </div>
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-[#E5E7EB] text-xs">
                <span className="text-[10px] font-mono uppercase tracking-wider text-[#5F6368] block">
                  GRAPH LINKAGE
                </span>
                <div className="flex items-center justify-between text-xs text-[#5F6368]">
                  <span>Status in Pipeline:</span>
                  <span className="font-mono font-semibold uppercase text-[#171717]">
                    {selectedData.status}
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-[#E5E7EB] space-y-2">
              <Button 
                variant="outline" 
                size="sm" 
                className="w-full justify-center"
                onClick={() => handleOpenProvenance(selectedData)}
              >
                Inspect Provenance Drawer
                <ExternalLink className="w-3 h-3 ml-1" />
              </Button>

              <Link href="/execution" className="block">
                <Button 
                  variant="primary" 
                  size="sm" 
                  className="w-full justify-center"
                >
                  <PlayCircle className="w-3.5 h-3.5 mr-1" />
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
