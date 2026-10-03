"use client";

import React, { useState } from "react";
import { Sidebar } from "./Sidebar";
import { CommandPalette } from "@/components/ui/CommandPalette";
import { Search, Bell, Shield, Terminal, ArrowUpRight } from "lucide-react";
import { usePathname } from "next/navigation";

export function Shell({ children }: { children: React.ReactNode }) {
  const [searchOpen, setSearchOpen] = useState(false);
  const pathname = usePathname();

  const getBreadcrumb = () => {
    if (pathname === "/") return "Overview";
    if (pathname.startsWith("/actions")) return "Work / Actions";
    if (pathname.startsWith("/execution")) return "Work / Execution";
    if (pathname.startsWith("/verification")) return "Work / Verification";
    if (pathname.startsWith("/documents")) return "Knowledge / Documents";
    if (pathname.startsWith("/connections")) return "Systems / Connections";
    if (pathname.startsWith("/graph")) return "Explore / Action Graph";
    if (pathname.startsWith("/settings")) return "System / Settings";
    return "Workspace";
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#F7F7F5] text-[#171717]">
      <Sidebar onOpenSearch={() => setSearchOpen(true)} />
      
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Header */}
        <header className="h-13 shrink-0 border-b border-[#E5E7EB] bg-white px-6 flex items-center justify-between select-none">
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-[#5F6368] font-medium tracking-tight">
              {getBreadcrumb()}
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Quick search input */}
            <button
              onClick={() => setSearchOpen(true)}
              className="flex items-center gap-2 px-2.5 py-1 text-xs text-[#5F6368] bg-[#F7F7F5] border border-[#E5E7EB] rounded-[5px] hover:border-[#D1D5DB] hover:text-[#171717] transition-all cursor-pointer"
            >
              <Search className="w-3.5 h-3.5 text-[#5F6368]" />
              <span className="hidden sm:inline">Search actions, docs...</span>
              <kbd className="font-mono text-[10px] text-[#5F6368] bg-white border border-[#E5E7EB] px-1 py-0.2 rounded ml-1">
                ⌘K
              </kbd>
            </button>

            {/* System Status Pill */}
            <div className="hidden md:flex items-center gap-1.5 px-2 py-1 rounded-[5px] bg-[#F0FDF4] border border-[#BBF7D0] text-[11px] font-mono text-[#17803D]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#17803D] animate-pulse" />
              <span>Engine Ready</span>
            </div>
          </div>
        </header>

        {/* Expansive Content Area */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="max-w-[1440px] mx-auto w-full">
            {children}
          </div>
        </main>
      </div>

      <CommandPalette open={searchOpen} onOpenChange={setSearchOpen} />
    </div>
  );
}
