"use client";

import React, { useState } from "react";
import { 
  User, 
  Building, 
  Link2, 
  Shield, 
  Sliders, 
  Check, 
  Copy, 
  Save,
  CheckCircle2
} from "lucide-react";
import { Button } from "@/components/ui/Button";

type SettingsTab = "profile" | "workspace" | "connections" | "security" | "preferences";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>("workspace");
  const [copied, setCopied] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const tabs: { id: SettingsTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: "profile", label: "Profile", icon: User },
    { id: "workspace", label: "Workspace & Tenant", icon: Building },
    { id: "connections", label: "Connections", icon: Link2 },
    { id: "security", label: "Security & Policy", icon: Shield },
    { id: "preferences", label: "Preferences", icon: Sliders },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Editorial Header */}
      <div className="border-b border-[#ECECE9] pb-6">
        <span className="text-xs font-mono font-medium text-[#2563EB] tracking-wider uppercase">
          Engine Configuration
        </span>
        <h1 className="font-display text-4xl sm:text-5xl text-[#171717] mt-1.5">
          Settings
        </h1>
        <p className="text-base text-[#5F6368] mt-2">
          Tenant identity, zero-trust execution bounds, and system configuration.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
        {/* Navigation Sidebar */}
        <div className="md:col-span-3 space-y-1.5">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all text-left cursor-pointer border ${
                  isActive
                    ? "bg-white text-[#171717] border-[#D1D5DB] font-semibold shadow-2xs"
                    : "bg-transparent text-[#5F6368] border-transparent hover:text-[#171717] hover:bg-[#F7F7F5]"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-[#2563EB]" : "text-[#8A8F98]"}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Content Area */}
        <div className="md:col-span-9 space-y-6">
          {activeTab === "workspace" && (
            <div className="bg-white rounded-2xl border border-[#E5E7EB] p-8 space-y-6 shadow-2xs">
              <div>
                <h2 className="text-xl font-semibold text-[#171717]">Workspace & Tenant Partitioning</h2>
                <p className="text-sm text-[#5F6368] mt-1">
                  Multi-tenant isolation bounds enforced cryptographically across all services.
                </p>
              </div>

              <div className="space-y-5 text-sm">
                <div className="space-y-1.5">
                  <label className="block text-xs font-mono font-semibold tracking-wider text-[#8A8F98] uppercase">
                    Active Tenant ID
                  </label>
                  <div className="flex items-center gap-3">
                    <input
                      type="text"
                      readOnly
                      value="00000000-0000-4000-8000-000000000001"
                      className="w-full max-w-md bg-[#F7F7F5] border border-[#ECECE9] rounded-xl px-4 py-2.5 font-mono text-sm text-[#171717] focus:outline-none"
                    />
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => handleCopy("00000000-0000-4000-8000-000000000001")}
                    >
                      {copied ? <Check className="w-4 h-4 text-[#15803D]" /> : <Copy className="w-4 h-4" />}
                    </Button>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-mono font-semibold tracking-wider text-[#8A8F98] uppercase">
                    Tenant Slug
                  </label>
                  <input
                    type="text"
                    defaultValue="dev-tenant"
                    className="w-full max-w-md bg-white border border-[#E5E7EB] rounded-xl px-4 py-2.5 text-sm text-[#171717] focus:outline-none focus:border-[#2563EB]"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-mono font-semibold tracking-wider text-[#8A8F98] uppercase">
                    Backend Engine Base URL
                  </label>
                  <input
                    type="text"
                    defaultValue="http://localhost:8000/api/v1"
                    className="w-full max-w-md bg-white border border-[#E5E7EB] rounded-xl px-4 py-2.5 font-mono text-sm text-[#171717] focus:outline-none focus:border-[#2563EB]"
                  />
                </div>
              </div>

              <div className="pt-6 border-t border-[#ECECE9] flex items-center justify-between">
                <span className="text-xs text-[#5F6368]">
                  {saved ? "Settings saved successfully." : "Changes apply across all active tenant connections."}
                </span>
                <Button size="md" variant="primary" onClick={handleSave}>
                  <Save className="w-4 h-4 mr-2" />
                  Save Workspace
                </Button>
              </div>
            </div>
          )}

          {activeTab === "security" && (
            <div className="bg-white rounded-2xl border border-[#E5E7EB] p-8 space-y-6 shadow-2xs">
              <div>
                <h2 className="text-xl font-semibold text-[#171717]">Zero-Trust Security & Policy Boundaries</h2>
                <p className="text-sm text-[#5F6368] mt-1">
                  Autonomous execution safeguards, require-approval rules, and cryptographic nonce validation.
                </p>
              </div>

              <div className="space-y-5 text-sm">
                <div className="p-4 rounded-xl bg-[#F0FDF4] border border-[#BBF7D0] flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-[#15803D] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-[#15803D] block">Zero-Trust Perimeter Active</span>
                    <span className="text-xs text-[#5F6368]">Every execution request requires capability policy verification before tool invocation.</span>
                  </div>
                </div>

                <div className="space-y-3.5 pt-2">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded border-[#D1D5DB] text-[#2563EB] w-4 h-4" />
                    <span className="text-[#171717] font-medium">Require manual human approval for external write actions</span>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded border-[#D1D5DB] text-[#2563EB] w-4 h-4" />
                    <span className="text-[#171717] font-medium">Perform post-execution observation and cryptographic evidence verification</span>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded border-[#D1D5DB] text-[#2563EB] w-4 h-4" />
                    <span className="text-[#171717] font-medium">Enforce tenant database isolation with strict foreign key constraints</span>
                  </label>
                </div>
              </div>

              <div className="pt-6 border-t border-[#ECECE9]">
                <Button size="md" variant="primary" onClick={handleSave}>
                  Update Security Policies
                </Button>
              </div>
            </div>
          )}

          {activeTab === "profile" && (
            <div className="bg-white rounded-2xl border border-[#E5E7EB] p-8 space-y-6 shadow-2xs">
              <div>
                <h2 className="text-xl font-semibold text-[#171717]">Operator Profile</h2>
                <p className="text-sm text-[#5F6368] mt-1">Primary engineer identity and RBAC role.</p>
              </div>

              <div className="space-y-5 text-sm max-w-md">
                <div className="space-y-1.5">
                  <label className="block text-xs font-mono font-semibold tracking-wider text-[#8A8F98] uppercase">
                    Display Name
                  </label>
                  <input
                    type="text"
                    defaultValue="Lead Systems Engineer"
                    className="w-full bg-white border border-[#E5E7EB] rounded-xl px-4 py-2.5 text-sm text-[#171717] focus:outline-none focus:border-[#2563EB]"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-mono font-semibold tracking-wider text-[#8A8F98] uppercase">
                    Email
                  </label>
                  <input
                    type="email"
                    defaultValue="engineer@acme.corp"
                    className="w-full bg-white border border-[#E5E7EB] rounded-xl px-4 py-2.5 text-sm text-[#171717] focus:outline-none focus:border-[#2563EB]"
                  />
                </div>
              </div>

              <div className="pt-6 border-t border-[#ECECE9]">
                <Button size="md" variant="primary" onClick={handleSave}>
                  Save Profile
                </Button>
              </div>
            </div>
          )}

          {activeTab === "connections" && (
            <div className="bg-white rounded-2xl border border-[#E5E7EB] p-8 space-y-6 shadow-2xs">
              <div>
                <h2 className="text-xl font-semibold text-[#171717]">Connector Defaults</h2>
                <p className="text-sm text-[#5F6368] mt-1">Manage workspace repository targets and webhook configurations.</p>
              </div>

              <div className="space-y-5 text-sm max-w-md">
                <div className="space-y-1.5">
                  <label className="block text-xs font-mono font-semibold tracking-wider text-[#8A8F98] uppercase">
                    Default GitHub Repository
                  </label>
                  <input
                    type="text"
                    defaultValue="acme/nexus"
                    className="w-full bg-white border border-[#E5E7EB] rounded-xl px-4 py-2.5 font-mono text-sm text-[#171717] focus:outline-none focus:border-[#2563EB]"
                  />
                </div>
              </div>

              <div className="pt-6 border-t border-[#ECECE9]">
                <Button size="md" variant="primary" onClick={handleSave}>
                  Save Connector Settings
                </Button>
              </div>
            </div>
          )}

          {activeTab === "preferences" && (
            <div className="bg-white rounded-2xl border border-[#E5E7EB] p-8 space-y-6 shadow-2xs">
              <div>
                <h2 className="text-xl font-semibold text-[#171717]">Interface Preferences</h2>
                <p className="text-sm text-[#5F6368] mt-1">Visual theme and layout density settings.</p>
              </div>

              <div className="space-y-5 text-sm">
                <div>
                  <span className="text-xs font-mono font-semibold tracking-wider text-[#8A8F98] uppercase block mb-3">
                    Theme Selection
                  </span>
                  <div className="flex items-center gap-3">
                    <button className="px-4 py-2.5 rounded-xl border border-[#2563EB] bg-[#EFF6FF] text-[#2563EB] font-semibold text-sm flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#2563EB]" />
                      Living Canvas Warm Light
                    </button>
                    <button className="px-4 py-2.5 rounded-xl border border-[#E5E7EB] text-[#8A8F98] text-sm flex items-center gap-2 opacity-50 cursor-not-allowed">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#8A8F98]" />
                      Dark (Coming Soon)
                    </button>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-[#ECECE9]">
                <Button size="md" variant="primary" onClick={handleSave}>
                  Save Preferences
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
