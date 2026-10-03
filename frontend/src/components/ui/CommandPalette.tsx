"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import { 
  Search, 
  CheckSquare, 
  FileText, 
  PlayCircle, 
  GitBranch, 
  Settings, 
  ArrowRight,
  ShieldCheck,
  Radio
} from "lucide-react";

interface CommandPaletteProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function CommandPalette({ open: controlledOpen, onOpenChange }: CommandPaletteProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const router = useRouter();

  const isOpen = controlledOpen !== undefined ? controlledOpen : internalOpen;
  const setIsOpen = (value: boolean) => {
    if (onOpenChange) onOpenChange(value);
    else setInternalOpen(value);
  };

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setIsOpen(!isOpen);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [isOpen]);

  const runCommand = (command: () => void) => {
    setIsOpen(false);
    command();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/30 backdrop-blur-xs p-4 animate-in fade-in duration-100">
      <div 
        className="w-full max-w-xl bg-white rounded-lg shadow-xl border border-[#E5E7EB] overflow-hidden flex flex-col transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        <Command className="flex flex-col w-full focus:outline-none">
          <div className="flex items-center border-b border-[#E5E7EB] px-3.5 py-2.5 gap-2.5">
            <Search className="w-4 h-4 text-[#5F6368] shrink-0" />
            <Command.Input
              autoFocus
              placeholder="Search actions, documents, executions, connections... (Type or navigate)"
              className="w-full text-sm outline-none text-[#171717] placeholder:text-[#9CA3AF] bg-transparent"
            />
            <kbd className="hidden sm:inline-flex items-center text-[10px] font-mono text-[#5F6368] bg-[#F2F2F0] border border-[#E5E7EB] px-1.5 py-0.5 rounded">
              ESC
            </kbd>
          </div>

          <Command.List className="max-h-80 overflow-y-auto p-2 space-y-1 text-sm focus:outline-none">
            <Command.Empty className="py-6 text-center text-xs text-[#5F6368]">
              No matching items found in workspace.
            </Command.Empty>

            <Command.Group heading="Navigation" className="text-[11px] font-semibold text-[#5F6368] uppercase tracking-wider px-2 py-1">
              <Command.Item
                onSelect={() => runCommand(() => router.push("/"))}
                className="flex items-center justify-between px-2.5 py-2 rounded-md cursor-pointer text-[#171717] hover:bg-[#F2F2F0] aria-selected:bg-[#EFF6FF] aria-selected:text-[#2563EB]"
              >
                <div className="flex items-center gap-2.5">
                  <Radio className="w-4 h-4 text-[#5F6368]" />
                  <span>Overview Dashboard</span>
                </div>
                <ArrowRight className="w-3 h-3 text-[#9CA3AF]" />
              </Command.Item>

              <Command.Item
                onSelect={() => runCommand(() => router.push("/actions"))}
                className="flex items-center justify-between px-2.5 py-2 rounded-md cursor-pointer text-[#171717] hover:bg-[#F2F2F0] aria-selected:bg-[#EFF6FF] aria-selected:text-[#2563EB]"
              >
                <div className="flex items-center gap-2.5">
                  <CheckSquare className="w-4 h-4 text-[#5F6368]" />
                  <span>Actions Workspace</span>
                </div>
                <ArrowRight className="w-3 h-3 text-[#9CA3AF]" />
              </Command.Item>

              <Command.Item
                onSelect={() => runCommand(() => router.push("/execution"))}
                className="flex items-center justify-between px-2.5 py-2 rounded-md cursor-pointer text-[#171717] hover:bg-[#F2F2F0] aria-selected:bg-[#EFF6FF] aria-selected:text-[#2563EB]"
              >
                <div className="flex items-center gap-2.5">
                  <PlayCircle className="w-4 h-4 text-[#5F6368]" />
                  <span>Execution Control Center</span>
                </div>
                <ArrowRight className="w-3 h-3 text-[#9CA3AF]" />
              </Command.Item>

              <Command.Item
                onSelect={() => runCommand(() => router.push("/verification"))}
                className="flex items-center justify-between px-2.5 py-2 rounded-md cursor-pointer text-[#171717] hover:bg-[#F2F2F0] aria-selected:bg-[#EFF6FF] aria-selected:text-[#2563EB]"
              >
                <div className="flex items-center gap-2.5">
                  <ShieldCheck className="w-4 h-4 text-[#5F6368]" />
                  <span>Verification Evidence Log</span>
                </div>
                <ArrowRight className="w-3 h-3 text-[#9CA3AF]" />
              </Command.Item>

              <Command.Item
                onSelect={() => runCommand(() => router.push("/graph"))}
                className="flex items-center justify-between px-2.5 py-2 rounded-md cursor-pointer text-[#171717] hover:bg-[#F2F2F0] aria-selected:bg-[#EFF6FF] aria-selected:text-[#2563EB]"
              >
                <div className="flex items-center gap-2.5">
                  <GitBranch className="w-4 h-4 text-[#5F6368]" />
                  <span>Interactive Action Graph</span>
                </div>
                <ArrowRight className="w-3 h-3 text-[#9CA3AF]" />
              </Command.Item>

              <Command.Item
                onSelect={() => runCommand(() => router.push("/documents"))}
                className="flex items-center justify-between px-2.5 py-2 rounded-md cursor-pointer text-[#171717] hover:bg-[#F2F2F0] aria-selected:bg-[#EFF6FF] aria-selected:text-[#2563EB]"
              >
                <div className="flex items-center gap-2.5">
                  <FileText className="w-4 h-4 text-[#5F6368]" />
                  <span>Ingested Documents & Chunks</span>
                </div>
                <ArrowRight className="w-3 h-3 text-[#9CA3AF]" />
              </Command.Item>

              <Command.Item
                onSelect={() => runCommand(() => router.push("/settings"))}
                className="flex items-center justify-between px-2.5 py-2 rounded-md cursor-pointer text-[#171717] hover:bg-[#F2F2F0] aria-selected:bg-[#EFF6FF] aria-selected:text-[#2563EB]"
              >
                <div className="flex items-center gap-2.5">
                  <Settings className="w-4 h-4 text-[#5F6368]" />
                  <span>System Settings & Tenant Config</span>
                </div>
                <ArrowRight className="w-3 h-3 text-[#9CA3AF]" />
              </Command.Item>
            </Command.Group>
          </Command.List>

          <div className="border-t border-[#E5E7EB] bg-[#F7F7F5] px-3.5 py-2 flex items-center justify-between text-[11px] text-[#5F6368]">
            <div className="flex items-center gap-3">
              <span>Use <kbd className="font-mono bg-white border border-[#E5E7EB] px-1 rounded">↑</kbd> <kbd className="font-mono bg-white border border-[#E5E7EB] px-1 rounded">↓</kbd> to navigate</span>
              <span><kbd className="font-mono bg-white border border-[#E5E7EB] px-1 rounded">Enter</kbd> to select</span>
            </div>
            <span className="font-medium text-[#171717]">NEXUS Command</span>
          </div>
        </Command>
      </div>
      <div 
        className="fixed inset-0 -z-10" 
        onClick={() => setIsOpen(false)}
      />
    </div>
  );
}
