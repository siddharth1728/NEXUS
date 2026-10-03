"use client";

import React, { useState } from "react";
import { 
  GitBranch, 
  Calendar, 
  Server, 
  RefreshCw,
  Plus
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { AddConnectionDialog } from "@/components/ui/AddConnectionDialog";

interface Connector {
  id: string;
  name: string;
  provider: string;
  status: "connected" | "disconnected" | "degraded";
  health: "Healthy" | "Degraded" | "Offline";
  lastChecked: string;
  icon: React.ComponentType<{ className?: string }>;
  capabilities: { name: string; type: "READ" | "WRITE"; policy: "Permissive" | "Approval Required" }[];
  targetAccount: string;
  rateLimit: string;
}

export default function ConnectionsPage() {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [connectors, setConnectors] = useState<Connector[]>([
    {
      id: "github",
      name: "GitHub",
      provider: "github",
      status: "connected",
      health: "Healthy",
      lastChecked: "Just now · HTTP 200 OK",
      icon: GitBranch,
      targetAccount: "acme / nexus",
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
      lastChecked: "2 min ago · OAuth2 Active",
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
      name: "Simulator Engine",
      provider: "simulator",
      status: "connected",
      health: "Healthy",
      lastChecked: "Internal IPC loopback active",
      icon: Server,
      targetAccount: "Deterministic Local Sandbox",
      rateLimit: "In-memory isolated",
      capabilities: [
        { name: "Deterministic Dry Run", type: "READ", policy: "Permissive" },
        { name: "Synthetic State Mutation", type: "WRITE", policy: "Permissive" },
      ],
    },
  ]);

  const handleRefreshAll = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
    }, 800);
  };

  const handleConnected = (newConn: { name: string; provider: string }) => {
    const exists = connectors.some(c => c.provider === newConn.provider);
    if (!exists) {
      setConnectors(prev => [
        ...prev,
        {
          id: newConn.provider,
          name: newConn.name,
          provider: newConn.provider,
          status: "connected",
          health: "Healthy",
          lastChecked: "Just now · Authenticated & Healthy",
          icon: Server,
          targetAccount: "authorized-tenant-scope",
          rateLimit: "Standard Tier Active",
          capabilities: [
            { name: "Resource Read", type: "READ", policy: "Permissive" },
            { name: "Resource Mutate", type: "WRITE", policy: "Approval Required" }
          ]
        }
      ]);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Editorial Header */}
      <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-4 border-b border-[#ECECE9] pb-6">
        <div>
          <span className="text-xs font-mono font-medium text-[#2563EB] tracking-wider uppercase">
            Trusted Systems
          </span>
          <h1 className="font-display text-4xl sm:text-5xl text-[#171717] mt-1.5">
            Connections
          </h1>
          <p className="text-base text-[#5F6368] mt-2">
            Authorized external SaaS integrations for independent observation, controlled dispatch, and verification.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button 
            variant="secondary" 
            size="md" 
            onClick={handleRefreshAll}
            disabled={isRefreshing}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
            <span>{isRefreshing ? "Checking..." : "Probe Health"}</span>
          </Button>

          <Button 
            variant="primary" 
            size="md" 
            onClick={() => setIsAddDialogOpen(true)}
          >
            <Plus className="w-4 h-4 mr-1.5" />
            <span>Connect System</span>
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
              className="bg-white rounded-2xl border border-[#E5E7EB] hover:border-[#D1D5DB] transition-all p-7 shadow-2xs flex flex-col justify-between space-y-6"
            >
              {/* Header */}
              <div className="space-y-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3.5">
                    <div className="w-12 h-12 rounded-xl bg-[#F7F7F5] border border-[#ECECE9] flex items-center justify-center text-[#2563EB]">
                      <Icon className="w-6 h-6" />
                    </div>
                    <div>
                      <h2 className="font-display text-2xl text-[#171717]">
                        {c.name}
                      </h2>
                      <span className="font-mono text-xs text-[#5F6368]">
                        {c.targetAccount}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#F0FDF4] border border-[#BBF7D0] text-xs font-mono text-[#15803D]">
                    <span className="w-2 h-2 rounded-full bg-[#15803D] animate-pulse" />
                    <span>{c.health}</span>
                  </div>
                </div>

                {/* Telemetry info */}
                <div className="p-3.5 rounded-xl bg-[#F7F7F5] border border-[#ECECE9] text-xs font-mono space-y-1 text-[#5F6368]">
                  <div className="flex justify-between">
                    <span>Status:</span>
                    <span className="text-[#171717]">{c.lastChecked}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Capacity:</span>
                    <span className="text-[#171717]">{c.rateLimit}</span>
                  </div>
                </div>

                {/* Capabilities list */}
                <div className="space-y-2 pt-2">
                  <span className="text-xs font-mono font-semibold tracking-wider text-[#8A8F98] uppercase block">
                    Authorized Capabilities
                  </span>
                  <div className="space-y-2">
                    {c.capabilities.map((cap, idx) => (
                      <div 
                        key={idx} 
                        className="p-3 rounded-xl bg-[#F7F7F5] border border-[#ECECE9] text-xs flex items-center justify-between"
                      >
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                            cap.type === "READ" 
                              ? "bg-[#EFF6FF] text-[#2563EB]" 
                              : "bg-[#FFFBEB] text-[#D97706]"
                          }`}>
                            {cap.type}
                          </span>
                          <span className="text-[#171717] font-medium text-xs">{cap.name}</span>
                        </div>
                        <span className="text-[11px] font-mono text-[#5F6368]">
                          {cap.policy}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="pt-4 border-t border-[#ECECE9] flex items-center justify-between text-xs font-mono text-[#5F6368]">
                <span>Zero-Trust Enforced</span>
                <span className="text-[#15803D] font-medium">Ready</span>
              </div>
            </div>
          );
        })}
      </div>

      <AddConnectionDialog 
        isOpen={isAddDialogOpen}
        onClose={() => setIsAddDialogOpen(false)}
        onConnected={handleConnected}
      />
    </div>
  );
}
