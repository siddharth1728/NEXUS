"use client";

import React, { useState } from "react";
import { Sidebar } from "./Sidebar";
import { CommandPalette } from "@/components/ui/CommandPalette";
import { NotificationPopover } from "@/components/ui/NotificationPopover";
import { Search, Menu } from "lucide-react";
import { usePathname } from "next/navigation";

export function Shell({ children }: { children: React.ReactNode }) {
  const [searchOpen, setSearchOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
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
      {/* Desktop Sidebar (persistent) */}
      <div className="hidden md:flex h-full">
        <Sidebar onOpenSearch={() => setSearchOpen(true)} />
      </div>

      {/* Mobile Sidebar Overlay Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex animate-in fade-in duration-150">
          <div className="relative w-64 bg-white h-full shadow-2xl z-10">
            <Sidebar 
              isMobile={true} 
              onClose={() => setMobileMenuOpen(false)} 
              onOpenSearch={() => {
                setMobileMenuOpen(false);
                setSearchOpen(true);
              }} 
            />
          </div>
          <div 
            className="fixed inset-0 bg-black/30 backdrop-blur-xs" 
            onClick={() => setMobileMenuOpen(false)} 
          />
        </div>
      )}
      
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Header */}
        <header className="h-16 shrink-0 border-b border-[#E5E7EB] bg-white px-6 sm:px-8 flex items-center justify-between select-none">
          <div className="flex items-center gap-4">
            {/* Mobile Hamburger Button */}
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden p-2 rounded-lg text-[#5F6368] hover:text-[#171717] hover:bg-[#F2F2F0] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2563EB]"
              aria-label="Open navigation menu"
            >
              <Menu className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-[#171717]">
                {getBreadcrumb()}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Quick search input */}
            <button
              onClick={() => setSearchOpen(true)}
              className="flex items-center gap-2.5 px-3 py-1.5 text-sm text-[#5F6368] bg-[#F7F7F5] border border-[#E5E7EB] rounded-lg hover:border-[#D1D5DB] hover:text-[#171717] transition-all cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2563EB]"
              aria-label="Search actions, documents, and executions"
            >
              <Search className="w-4 h-4 text-[#8A8F98]" />
              <span className="hidden sm:inline">Search anything...</span>
              <kbd className="font-mono text-xs text-[#5F6368] bg-white border border-[#E5E7EB] px-1.5 py-0.5 rounded shadow-2xs">
                ⌘K
              </kbd>
            </button>

            {/* Notification Popover */}
            <NotificationPopover />

            {/* Engine Status Pill */}
            <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#F0FDF4] border border-[#BBF7D0] text-xs font-mono text-[#15803D]">
              <span className="w-2 h-2 rounded-full bg-[#15803D] animate-pulse" />
              <span>Engine Active</span>
            </div>
          </div>
        </header>

        {/* Expansive Content Area */}
        <main className="flex-1 overflow-y-auto p-6 sm:p-8 md:p-10">
          <div className="max-w-[1440px] mx-auto w-full">
            {children}
          </div>
        </main>
      </div>

      <CommandPalette open={searchOpen} onOpenChange={setSearchOpen} />
    </div>
  );
}
