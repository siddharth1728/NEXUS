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
  Layers
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  name: string;
  href: string;
  icon: any;
  action?: () => void;
  badge?: string;
}

interface NavSection {
  title?: string;
  items: NavItem[];
}

export function Sidebar({ onOpenSearch }: { onOpenSearch?: () => void }) {
  const pathname = usePathname();

  const sections: NavSection[] = [
    {
      items: [
        { name: "Overview", href: "/", icon: Radio },
      ],
    },
    {
      title: "WORK",
      items: [
        { name: "Actions", href: "/actions", icon: CheckSquare },
        { name: "Execution", href: "/execution", icon: PlayCircle },
        { name: "Verification", href: "/verification", icon: ShieldCheck },
      ],
    },
    {
      title: "KNOWLEDGE",
      items: [
        { name: "Documents", href: "/documents", icon: FileText },
        { 
          name: "Search", 
          href: "#", 
          icon: Search, 
          action: onOpenSearch,
          badge: "⌘K"
        },
      ],
    },
    {
      title: "SYSTEMS",
      items: [
        { name: "Connections", href: "/connections", icon: Link2 },
      ],
    },
    {
      title: "EXPLORE",
      items: [
        { name: "Action Graph", href: "/graph", icon: GitBranch },
      ],
    },
    {
      title: "SYSTEM",
      items: [
        { name: "Settings", href: "/settings", icon: Settings },
      ],
    },
  ];

  return (
    <aside className="w-60 flex-shrink-0 bg-[#FFFFFF] border-r border-[#E5E7EB] flex flex-col justify-between select-none">
      {/* Brand Header */}
      <div className="h-13 px-4 border-b border-[#E5E7EB] flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-[5px] bg-[#171717] flex items-center justify-center text-white font-mono text-[11px] font-bold">
            N
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-xs tracking-wider text-[#171717]">NEXUS</span>
            <span className="text-[10px] text-[#5F6368] font-mono leading-none">ENGINE v1.0</span>
          </div>
        </Link>
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-[#F0FDF4] text-[#17803D] border border-[#BBF7D0]">
          LIVE
        </span>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto py-3 px-2 space-y-5">
        {sections.map((section, idx) => (
          <div key={idx} className="space-y-0.5">
            {section.title && (
              <div className="px-2.5 pb-1.5 text-[10px] font-mono font-semibold tracking-wider text-[#5F6368]">
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
                    className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-[5px] text-xs font-medium text-[#5F6368] hover:text-[#171717] hover:bg-[#F2F2F0] transition-colors text-left"
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-3.5 h-3.5 shrink-0 text-[#5F6368]" />
                      <span>{item.name}</span>
                    </div>
                    {item.badge && (
                      <kbd className="font-mono text-[10px] text-[#5F6368] bg-[#F2F2F0] border border-[#E5E7EB] px-1 py-0.2 rounded">
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
                  className={cn(
                    "flex items-center justify-between px-2.5 py-1.5 rounded-[5px] text-xs font-medium transition-colors",
                    isActive
                      ? "bg-[#EFF6FF] text-[#2563EB] font-semibold"
                      : "text-[#5F6368] hover:text-[#171717] hover:bg-[#F2F2F0]"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={cn("w-3.5 h-3.5 shrink-0", isActive ? "text-[#2563EB]" : "text-[#5F6368]")} />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[10px] font-mono px-1 py-0.2 rounded bg-[#E5E7EB] text-[#5F6368]">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </div>

      {/* Tenant / User Footer */}
      <div className="p-3 border-t border-[#E5E7EB] bg-[#F7F7F5]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-white border border-[#E5E7EB] flex items-center justify-center text-[10px] font-bold text-[#171717]">
              DT
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-medium text-[#171717] leading-none">dev-tenant</span>
              <span className="text-[10px] text-[#5F6368] leading-tight">Zero-Trust Active</span>
            </div>
          </div>
          <Link href="/settings" className="p-1 rounded text-[#5F6368] hover:text-[#171717] hover:bg-[#E5E7EB]">
            <Settings className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </aside>
  );
}
