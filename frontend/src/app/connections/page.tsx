"use client";

import React, { useState } from "react";
import { 
  GitBranch, 
  Calendar, 
  Server, 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle, 
  ExternalLink, 
  Radio, 
  Key, 
  Lock,
  RefreshCw,
  Sliders,
  ChevronRight
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";

interface Connector {
  id: string;
  name: string;
  provider: string;
  status: "connected" | "disconnected" | "degraded";
  health: "Healthy" | "Degraded" | "Offline";
  lastChecked: string;
  icon: any;
  capabilities: { name: string; type: "READ" | "WRITE"; policy: "Permissive" | "Approval Required" }[];
  targetAccount: string;
  rateLimit: string;
}

export default function ConnectionsPage() {
  const [connectors, setConnectors] = useState<Connector[]>([
    {
      id: "github",
      name: "GitHub Enterprise",
      provider: "github",
      status: "connected",
      health: "Healthy",
      lastChecked: "Just now (HTTP 200 OK)",
      icon: GitBranch,
      targetAccount: "org: acme / repo: nexus",
      rateLimit: "4,980 / 5,000 req/hr",
      capabilities: [
        { name: "Repository Read", type: "READ", policy: "Permissive" },
        { name: "Issue Read", type: "READ", policy: "Permissive" },
        { name: "Issue Create", type: "WRITE", policy: "Approval Required" },
        { name: "Comment Create", type: "WRITE", policy: "Approval Required" },
      ],
    },
    {
      id: "google_calendar",
      name: "Google Calendar",
      provider: "google_calendar",
      status: "connected",
      health: "Healthy",
      lastChecked: "2 min ago (OAuth2 Valid)",
      icon: Calendar,
      targetAccount: "service-lead@acme.corp",
      rateLimit: "Unlimited (Workspace Tier)",
      capabilities: [
        { name: "Calendar Events Read", type: "READ", policy: "Permissive" },
        { name: "Calendar Events Create", type: "WRITE", policy: "Approval Required" },
        { name: "Attendee Status Sync", type: "READ", policy: "Permissive" },
      ],
    },
    {
      id: "system_simulator",
      name: "Sandbox Simulator Engine",
      provider: "simulator",
      status: "connected",
      health: "Healthy",
      lastChecked: "Internal Bus Active",
      icon: Server,
      targetAccount: "Local IPC / in-memory isolated",
      rateLimit: "No rate limit",
      capabilities: [
        { name: "Deterministic Dry Run", type: "READ", policy: "Permissive" },
        { name: "Synthetic State Mutation", type: "WRITE", policy: "Permissive" },
      ],
    },
  ]);

  return (
    <div className="space-y-8 animate-in fade-in duration-150">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#E5E7EB] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-[#171717]">
              Infrastructure Connections
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#F0FDF4] text-[#17803D] font-semibold border border-[#86EFAC]">
              Controlled Ingress / Egress
            </span>
          </div>
          <p className="text-xs text-[#5F6368] mt-1">
            External SaaS systems authorized for NEXUS observation, action dispatch, and verification.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm">
            <RefreshCw className="w-3.5 h-3.5" />
            Check All Health
          </Button>
        </div>
      </div>

      {/* Integration Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {connectors.map((c) => {
          const Icon = c.icon;
          return (
            <div 
              key={c.id} 
              className="bg-white rounded-lg border border-[#E5E7EB] p-5 shadow-xs flex flex-col justify-between space-y-5 hover:border-[#D1D5DB] transition-all"
            >
              {/* Header */}
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-[5px] bg-[#F7F7F5] border border-[#E5E7EB] flex items-center justify-center text-[#171717]">
                      <Icon className="w-4 h-4 text-[#2563EB]" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-[#171717]">{c.name}</h3>
                      <span className="font-mono text-[10px] text-[#5F6368]">{c.targetAccount}</span>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-1">
                    <StatusBadge status="connected" size="sm" />
                    <span className="text-[10px] font-mono text-[#17803D] font-medium">
                      {c.health}
                    </span>
                  </div>
                </div>

                {/* Health & Rate telemetry */}
                <div className="p-2.5 rounded bg-[#F7F7F5] border border-[#E5E7EB] text-[11px] font-mono space-y-1 text-[#5F6368]">
                  <div className="flex justify-between">
                    <span>Telemetry:</span>
                    <span className="text-[#171717]">{c.lastChecked}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Capacity:</span>
                    <span className="text-[#171717]">{c.rateLimit}</span>
                  </div>
                </div>

                {/* Granular Capabilities Breakdown */}
                <div className="space-y-2 pt-2">
                  <span className="text-[10px] font-mono uppercase tracking-wider font-semibold text-[#5F6368]">
                    AUTHORIZED CAPABILITIES
                  </span>
                  <div className="space-y-1.5">
                    {c.capabilities.map((cap, idx) => (
                      <div 
                        key={idx} 
                        className="p-2 rounded bg-white border border-[#E5E7EB] text-xs flex items-center justify-between"
                      >
                        <div className="flex items-center gap-2">
                          <span className={`text-[9px] font-mono font-bold px-1 rounded ${
                            cap.type === "READ" 
                              ? "bg-[#EFF6FF] text-[#2563EB]" 
                              : "bg-[#FFFBEB] text-[#A65F00]"
                          }`}>
                            {cap.type}
                          </span>
                          <span className="text-[#171717] font-medium text-[11px]">{cap.name}</span>
                        </div>
                        <span className="text-[10px] font-mono text-[#5F6368]">
                          {cap.policy}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Card Footer: Action */}
              <div className="pt-3 border-t border-[#E5E7EB] flex items-center justify-between">
                <span className="text-[11px] text-[#5F6368] font-mono">Zero-Trust Sandbox</span>
                <Button size="sm" variant="secondary">
                  Manage Connector
                </Button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
