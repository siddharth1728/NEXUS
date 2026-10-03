"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Radio, 
  CheckSquare, 
  PlayCircle, 
  ShieldCheck, 
  FileText, 
  Search, 
  Link2, 
  GitBranch, 
  Settings, 
  X
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  action?: () => void;
  badge?: string;
}

interface NavSection {
  title?: string;
  items: NavItem[];
}

export function Sidebar({ 
  onOpenSearch, 
  isMobile = false, 
  onClose 
}: { 
  onOpenSearch?: () => void;
  isMobile?: boolean;
  onClose?: () => void;
}) {
  const pathname = usePathname();

  const sections: NavSection[] = [
    {
      items: [
        { name: "Overview", href: "/", icon: Radio },
      ],
    },
    {
      title: "Work",
      items: [
        { name: "Actions", href: "/actions", icon: CheckSquare },
        { name: "Execution", href: "/execution", icon: PlayCircle },
        { name: "Verification", href: "/verification", icon: ShieldCheck },
      ],
    },
    {
      title: "Knowledge",
      items: [
        { name: "Documents", href: "/documents", icon: FileText },
        { 
          name: "Search", 
          href: "#", 
          icon: Search, 
          action: () => {
            if (onOpenSearch) onOpenSearch();
            if (onClose) onClose();
          },
          badge: "⌘K"
        },
      ],
    },
    {
      title: "Systems",
      items: [
        { name: "Connections", href: "/connections", icon: Link2 },
        { name: "Action Graph", href: "/graph", icon: GitBranch },
      ],
    },
    {
      title: "Preferences",
      items: [
        { name: "Settings", href: "/settings", icon: Settings },
      ],
    },
  ];

  return (
    <aside className={cn(
      "w-64 flex-shrink-0 bg-white border-r border-[#E5E7EB] flex flex-col justify-between select-none h-full",
      isMobile && "border-r-0"
    )}>
      {/* Brand Header */}
      <div className="h-16 px-5 border-b border-[#ECECE9] flex items-center justify-between">
        <Link 
          href="/" 
          onClick={onClose}
          className="flex items-center gap-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2563EB] rounded-md"
        >
          <div className="w-8 h-8 rounded-lg bg-[#171717] flex items-center justify-center text-white font-mono text-sm font-bold shadow-xs">
            N
          </div>
          <div className="flex flex-col">
            <span className="font-display text-xl text-[#171717] leading-none tracking-tight">
              NEXUS
            </span>
            <span className="text-[11px] font-mono text-[#5F6368] mt-0.5 tracking-wider">
              LIVING CANVAS
            </span>
          </div>
        </Link>
        
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-[#F0FDF4] border border-[#BBF7D0] text-[11px] font-mono font-medium text-[#15803D]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#15803D] animate-pulse" />
            <span>Ready</span>
          </div>
          {isMobile && (
            <button 
              onClick={onClose}
              className="p-1 rounded-md text-[#5F6368] hover:text-[#171717] hover:bg-[#F2F2F0]"
              aria-label="Close navigation"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto py-5 px-3 space-y-6">
        {sections.map((section, idx) => (
          <div key={idx} className="space-y-1">
            {section.title && (
              <div className="px-3 pb-1 text-xs font-mono font-semibold tracking-wider text-[#8A8F98]">
                {section.title}
              </div>
            )}
            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive = item.href !== "#" && (pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href)));

              if (item.action) {
                return (
                  <button
                    key={item.name}
                    onClick={item.action}
                    className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium text-[#5F6368] hover:text-[#171717] hover:bg-[#F7F7F5] transition-all text-left cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2563EB]"
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="w-4 h-4 shrink-0 text-[#8A8F98]" />
                      <span>{item.name}</span>
                    </div>
                    {item.badge && (
                      <kbd className="font-mono text-xs text-[#5F6368] bg-[#F7F7F5] border border-[#E5E7EB] px-1.5 py-0.5 rounded">
                        {item.badge}
                      </kbd>
                    )}
                  </button>
                );
              }

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={onClose}
                  className={cn(
                    "flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2563EB]",
                    isActive
                      ? "bg-[#EFF6FF] text-[#2563EB] font-semibold shadow-xs"
                      : "text-[#5F6368] hover:text-[#171717] hover:bg-[#F7F7F5]"
                  )}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={cn("w-4 h-4 shrink-0", isActive ? "text-[#2563EB]" : "text-[#8A8F98]")} />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-[#ECECE9] text-[#5F6368]">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </div>

      {/* Tenant / Context Workspace Footer */}
      <div className="p-4 border-t border-[#ECECE9] bg-[#F7F7F5]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-white border border-[#E5E7EB] flex items-center justify-center text-xs font-bold text-[#171717] shadow-xs">
              DT
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-semibold text-[#171717] leading-none">dev-tenant</span>
              <span className="text-[11px] text-[#5F6368] leading-tight font-mono mt-0.5">Zero-Trust Active</span>
            </div>
          </div>
          <Link 
            href="/settings" 
            onClick={onClose}
            className="p-1.5 rounded-md text-[#5F6368] hover:text-[#171717] hover:bg-white border border-transparent hover:border-[#E5E7EB] transition-all"
            aria-label="Settings"
          >
            <Settings className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </aside>
  );
}
