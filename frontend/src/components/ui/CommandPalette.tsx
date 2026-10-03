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
  const setIsOpen = React.useCallback((value: boolean) => {
    if (onOpenChange) onOpenChange(value);
    else setInternalOpen(value);
  }, [onOpenChange]);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setIsOpen(!isOpen);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [isOpen, setIsOpen]);

  const runCommand = (command: () => void) => {
    setIsOpen(false);
    command();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div 
        className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-[#E5E7EB] overflow-hidden flex flex-col transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        <Command className="flex flex-col w-full focus:outline-none">
          <div className="flex items-center border-b border-[#ECECE9] px-5 py-4 gap-3">
            <Search className="w-5 h-5 text-[#8A8F98] shrink-0" />
            <Command.Input
              autoFocus
              placeholder="Search actions, documents, executions, connections... (Type or navigate)"
              className="w-full text-base outline-none text-[#171717] placeholder:text-[#8A8F98] bg-transparent"
            />
            <kbd className="hidden sm:inline-flex items-center text-xs font-mono text-[#5F6368] bg-[#F7F7F5] border border-[#ECECE9] px-2 py-0.5 rounded-md">
              ESC
            </kbd>
          </div>

          <Command.List className="max-h-96 overflow-y-auto p-3 space-y-3 text-sm focus:outline-none">
            <Command.Empty className="py-8 text-center text-sm text-[#5F6368]">
              No matching items found in active workspace.
            </Command.Empty>

            {/* Group 1: Actions */}
            <Command.Group heading="Actions" className="text-xs font-mono font-semibold text-[#8A8F98] uppercase tracking-wider px-3 py-1">
              <Command.Item
                onSelect={() => runCommand(() => router.push("/actions"))}
                className="flex items-center justify-between px-3.5 py-2.5 rounded-xl cursor-pointer text-[#171717] hover:bg-[#F7F7F5] aria-selected:bg-[#EFF6FF] aria-selected:text-[#2563EB] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <CheckSquare className="w-4 h-4 text-[#2563EB]" />
                  <span className="font-medium">Review security & authentication configuration</span>
                </div>
                <span className="text-xs font-mono text-[#8A8F98]">READY</span>
              </Command.Item>

              <Command.Item
                onSelect={() => runCommand(() => router.push("/actions"))}
                className="flex items-center justify-between px-3.5 py-2.5 rounded-xl cursor-pointer text-[#171717] hover:bg-[#F7F7F5] aria-selected:bg-[#EFF6FF] aria-selected:text-[#2563EB] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <CheckSquare className="w-4 h-4 text-[#D97706]" />
                  <span className="font-medium">Publish Sprint Milestone to GitHub Issues</span>
                </div>
                <span className="text-xs font-mono text-[#8A8F98]">APPROVAL</span>
              </Command.Item>
            </Command.Group>

            {/* Group 2: Documents */}
            <Command.Group heading="Documents" className="text-xs font-mono font-semibold text-[#8A8F98] uppercase tracking-wider px-3 py-1">
              <Command.Item
                onSelect={() => runCommand(() => router.push("/documents"))}
                className="flex items-center justify-between px-3.5 py-2.5 rounded-xl cursor-pointer text-[#171717] hover:bg-[#F7F7F5] aria-selected:bg-[#EFF6FF] aria-selected:text-[#2563EB] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4 text-[#2563EB]" />
                  <span className="font-medium">Architecture Guidelines & Ingress Spec.pdf</span>
                </div>
                <span className="text-xs font-mono text-[#8A8F98]">18 facts</span>
              </Command.Item>

              <Command.Item
                onSelect={() => runCommand(() => router.push("/documents"))}
                className="flex items-center justify-between px-3.5 py-2.5 rounded-xl cursor-pointer text-[#171717] hover:bg-[#F7F7F5] aria-selected:bg-[#EFF6FF] aria-selected:text-[#2563EB] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4 text-[#2563EB]" />
                  <span className="font-medium">Zero-Trust Security & Token Perimeter.docx</span>
                </div>
                <span className="text-xs font-mono text-[#8A8F98]">24 facts</span>
              </Command.Item>
            </Command.Group>

            {/* Group 3: Executions */}
            <Command.Group heading="Executions" className="text-xs font-mono font-semibold text-[#8A8F98] uppercase tracking-wider px-3 py-1">
              <Command.Item
                onSelect={() => runCommand(() => router.push("/execution"))}
                className="flex items-center justify-between px-3.5 py-2.5 rounded-xl cursor-pointer text-[#171717] hover:bg-[#F7F7F5] aria-selected:bg-[#EFF6FF] aria-selected:text-[#2563EB] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <PlayCircle className="w-4 h-4 text-[#15803D]" />
                  <span className="font-medium">GitHub Issue #42 Created</span>
                </div>
                <span className="text-xs font-mono text-[#15803D]">VERIFIED</span>
              </Command.Item>
            </Command.Group>

            {/* Group 4: Navigation */}
            <Command.Group heading="Navigation" className="text-xs font-mono font-semibold text-[#8A8F98] uppercase tracking-wider px-3 py-1">
              <Command.Item
                onSelect={() => runCommand(() => router.push("/"))}
                className="flex items-center justify-between px-3.5 py-2.5 rounded-xl cursor-pointer text-[#171717] hover:bg-[#F7F7F5] aria-selected:bg-[#EFF6FF] aria-selected:text-[#2563EB] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Radio className="w-4 h-4 text-[#8A8F98]" />
                  <span>Overview</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[#8A8F98]" />
              </Command.Item>

              <Command.Item
                onSelect={() => runCommand(() => router.push("/graph"))}
                className="flex items-center justify-between px-3.5 py-2.5 rounded-xl cursor-pointer text-[#171717] hover:bg-[#F7F7F5] aria-selected:bg-[#EFF6FF] aria-selected:text-[#2563EB] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <GitBranch className="w-4 h-4 text-[#8A8F98]" />
                  <span>Action Graph</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[#8A8F98]" />
              </Command.Item>

              <Command.Item
                onSelect={() => runCommand(() => router.push("/settings"))}
                className="flex items-center justify-between px-3.5 py-2.5 rounded-xl cursor-pointer text-[#171717] hover:bg-[#F7F7F5] aria-selected:bg-[#EFF6FF] aria-selected:text-[#2563EB] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Settings className="w-4 h-4 text-[#8A8F98]" />
                  <span>Settings</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[#8A8F98]" />
              </Command.Item>
            </Command.Group>
          </Command.List>

          <div className="border-t border-[#ECECE9] bg-[#F7F7F5] px-5 py-3 flex items-center justify-between text-xs text-[#5F6368]">
            <div className="flex items-center gap-4">
              <span>Use <kbd className="font-mono bg-white border border-[#ECECE9] px-1.5 py-0.5 rounded shadow-2xs">↑</kbd> <kbd className="font-mono bg-white border border-[#ECECE9] px-1.5 py-0.5 rounded shadow-2xs">↓</kbd> to navigate</span>
              <span><kbd className="font-mono bg-white border border-[#ECECE9] px-1.5 py-0.5 rounded shadow-2xs">Enter</kbd> to open</span>
            </div>
            <span className="font-mono font-medium text-[#171717]">NEXUS Command</span>
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
