"use client";

import React, { useState } from "react";
import { 
  User, 
  Building, 
  Link2, 
  Shield, 
  Sliders, 
  Check, 
  Key, 
  Copy, 
  Save,
  CheckCircle2,
  Lock
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

  const tabs: { id: SettingsTab; label: string; icon: any }[] = [
    { id: "profile", label: "Profile", icon: User },
    { id: "workspace", label: "Workspace", icon: Building },
    { id: "connections", label: "Connections", icon: Link2 },
    { id: "security", label: "Security & Policy", icon: Shield },
    { id: "preferences", label: "Preferences", icon: Sliders },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-150">
      {/* Header */}
      <div className="border-b border-[#E5E7EB] pb-5">
        <h1 className="text-xl font-bold tracking-tight text-[#171717]">
          System Settings
        </h1>
        <p className="text-xs text-[#5F6368] mt-1">
          Tenant identity, zero-trust execution bounds, and system configuration.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* Navigation Sidebar */}
        <div className="md:col-span-3 space-y-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-[5px] text-xs font-medium transition-colors text-left cursor-pointer ${
                  isActive
                    ? "bg-white text-[#171717] border border-[#D1D5DB] font-semibold shadow-xs"
                    : "text-[#5F6368] hover:text-[#171717] hover:bg-[#F2F2F0]"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-[#2563EB]" : "text-[#5F6368]"}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Content Area */}
        <div className="md:col-span-9 space-y-6">
          {activeTab === "workspace" && (
            <div className="bg-white rounded-lg border border-[#E5E7EB] p-6 space-y-6 shadow-xs">
              <div>
                <h2 className="text-sm font-bold text-[#171717]">Workspace & Tenant Partitioning</h2>
                <p className="text-xs text-[#5F6368] mt-0.5">
                  Multi-tenant isolation bounds enforced cryptographically across all services.
                </p>
              </div>

              <div className="space-y-4 text-xs">
                <div>
                  <label className="block text-[11px] font-mono uppercase tracking-wider text-[#5F6368] mb-1.5">
                    ACTIVE TENANT ID
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      readOnly
                      value="00000000-0000-4000-8000-000000000001"
                      className="w-full max-w-md bg-[#F7F7F5] border border-[#E5E7EB] rounded-[5px] px-3 py-1.5 font-mono text-xs text-[#171717] focus:outline-none"
                    />
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => handleCopy("00000000-0000-4000-8000-000000000001")}
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-[#17803D]" /> : <Copy className="w-3.5 h-3.5" />}
                    </Button>
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-mono uppercase tracking-wider text-[#5F6368] mb-1.5">
                    TENANT SLUG
                  </label>
                  <input
                    type="text"
                    defaultValue="dev-tenant"
                    className="w-full max-w-md bg-white border border-[#E5E7EB] rounded-[5px] px-3 py-1.5 text-xs text-[#171717] focus:outline-none focus:border-[#2563EB]"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-mono uppercase tracking-wider text-[#5F6368] mb-1.5">
                    BACKEND ENGINE BASE URL
                  </label>
                  <input
                    type="text"
                    defaultValue="http://localhost:8000/api/v1"
                    className="w-full max-w-md bg-white border border-[#E5E7EB] rounded-[5px] px-3 py-1.5 font-mono text-xs text-[#171717] focus:outline-none focus:border-[#2563EB]"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-[#E5E7EB] flex items-center justify-between">
                <span className="text-[11px] text-[#5F6368]">
                  {saved ? "Settings saved successfully." : "Changes apply across all active tenant connections."}
                </span>
                <Button size="sm" variant="primary" onClick={handleSave}>
                  <Save className="w-3.5 h-3.5 mr-1" />
                  Save Workspace
                </Button>
              </div>
            </div>
          )}

          {activeTab === "security" && (
            <div className="bg-white rounded-lg border border-[#E5E7EB] p-6 space-y-6 shadow-xs">
              <div>
                <h2 className="text-sm font-bold text-[#171717]">Zero-Trust Security & Policy Boundaries</h2>
                <p className="text-xs text-[#5F6368] mt-0.5">
                  Autonomous execution safeguards, require-approval rules, and cryptographic nonce validation.
                </p>
              </div>

              <div className="space-y-4 text-xs">
                <div className="p-3 rounded-md bg-[#F0FDF4] border border-[#BBF7D0] flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-[#17803D] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-[#17803D] block">Zero-Trust Perimeter Active</span>
                    <span className="text-[#5F6368]">Every execution request requires capability policy verification before tool invocation.</span>
                  </div>
                </div>

                <div className="space-y-3">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded border-[#D1D5DB] text-[#2563EB]" />
                    <span className="text-[#171717] font-medium">Require manual human approval for external write actions</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded border-[#D1D5DB] text-[#2563EB]" />
                    <span className="text-[#171717] font-medium">Perform post-execution observation and cryptographic evidence verification</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded border-[#D1D5DB] text-[#2563EB]" />
                    <span className="text-[#171717] font-medium">Enforce tenant database isolation with strict foreign key constraints</span>
                  </label>
                </div>
              </div>

              <div className="pt-4 border-t border-[#E5E7EB]">
                <Button size="sm" variant="primary" onClick={handleSave}>
                  Update Security Policies
                </Button>
              </div>
            </div>
          )}

          {activeTab === "profile" && (
            <div className="bg-white rounded-lg border border-[#E5E7EB] p-6 space-y-6 shadow-xs">
              <div>
                <h2 className="text-sm font-bold text-[#171717]">Operator Profile</h2>
                <p className="text-xs text-[#5F6368] mt-0.5">Primary engineer identity and RBAC role.</p>
              </div>

              <div className="space-y-4 text-xs max-w-md">
                <div>
                  <label className="block text-[11px] font-mono uppercase tracking-wider text-[#5F6368] mb-1.5">
                    DISPLAY NAME
                  </label>
                  <input
                    type="text"
                    defaultValue="Lead Systems Engineer"
                    className="w-full bg-white border border-[#E5E7EB] rounded-[5px] px-3 py-1.5 text-xs text-[#171717] focus:outline-none focus:border-[#2563EB]"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-mono uppercase tracking-wider text-[#5F6368] mb-1.5">
                    EMAIL
                  </label>
                  <input
                    type="email"
                    defaultValue="engineer@acme.corp"
                    className="w-full bg-white border border-[#E5E7EB] rounded-[5px] px-3 py-1.5 text-xs text-[#171717] focus:outline-none focus:border-[#2563EB]"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-[#E5E7EB]">
                <Button size="sm" variant="primary" onClick={handleSave}>
                  Save Profile
                </Button>
              </div>
            </div>
          )}

          {activeTab === "connections" && (
            <div className="bg-white rounded-lg border border-[#E5E7EB] p-6 space-y-6 shadow-xs">
              <div>
                <h2 className="text-sm font-bold text-[#171717]">Connector Defaults</h2>
                <p className="text-xs text-[#5F6368] mt-0.5">Manage OAuth credentials and webhook configurations.</p>
              </div>

              <div className="space-y-4 text-xs max-w-md">
                <div>
                  <label className="block text-[11px] font-mono uppercase tracking-wider text-[#5F6368] mb-1.5">
                    DEFAULT GITHUB REPOSITORY
                  </label>
                  <input
                    type="text"
                    defaultValue="acme/nexus"
                    className="w-full bg-white border border-[#E5E7EB] rounded-[5px] px-3 py-1.5 font-mono text-xs text-[#171717] focus:outline-none focus:border-[#2563EB]"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-[#E5E7EB]">
                <Button size="sm" variant="primary" onClick={handleSave}>
                  Save Connector Settings
                </Button>
              </div>
            </div>
          )}

          {activeTab === "preferences" && (
            <div className="bg-white rounded-lg border border-[#E5E7EB] p-6 space-y-6 shadow-xs">
              <div>
                <h2 className="text-sm font-bold text-[#171717]">Interface Preferences</h2>
                <p className="text-xs text-[#5F6368] mt-0.5">Visual theme and layout density settings.</p>
              </div>

              <div className="space-y-4 text-xs">
                <div>
                  <span className="text-[11px] font-mono uppercase tracking-wider text-[#5F6368] block mb-2">
                    THEME
                  </span>
                  <div className="flex items-center gap-3">
                    <button className="px-3 py-2 rounded-[5px] border border-[#2563EB] bg-[#EFF6FF] text-[#2563EB] font-semibold text-xs flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-[#2563EB]" />
                      Warm Light (Primary)
                    </button>
                    <button className="px-3 py-2 rounded-[5px] border border-[#E5E7EB] text-[#5F6368] text-xs flex items-center gap-2 opacity-50 cursor-not-allowed">
                      <span className="w-2 h-2 rounded-full bg-[#5F6368]" />
                      Dark (Coming Soon)
                    </button>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-[#E5E7EB]">
                <Button size="sm" variant="primary" onClick={handleSave}>
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
