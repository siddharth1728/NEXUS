"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  AlertTriangle, 
  ShieldCheck, 
  PlayCircle, 
  Lock,
  Sparkles,
  HelpCircle,
  Flame,
  Check
} from "lucide-react";

export type StatusType = 
  | "ready" 
  | "pending" 
  | "in_progress" 
  | "running" 
  | "executing"
  | "succeeded" 
  | "completed" 
  | "verified" 
  | "not_verified"
  | "failed" 
  | "blocked" 
  | "needs_review" 
  | "requires_approval"
  | "connected"
  | "disconnected"
  | "degraded"
  // Epistemic Uncertainty states:
  | "confirmed"
  | "inferred"
  | "unknown"
  | "conflict";

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
  className?: string;
  showIcon?: boolean;
}

export function StatusBadge({ status, size = "md", className, showIcon = true }: StatusBadgeProps) {
  const norm = status?.toLowerCase().replace(/[\s-]/g, "_") as StatusType;

  const config: Record<string, { label: string; text: string; bg: string; border: string; icon: React.ReactNode }> = {
    // 1. Ready to execute
    ready: {
      label: "Ready",
      text: "text-[#2563EB]",
      bg: "bg-[#EFF6FF]",
      border: "border-[#BFDBFE]",
      icon: <PlayCircle className="w-3.5 h-3.5 text-[#2563EB]" />,
    },
    // 2. Pending prerequisites
    pending: {
      label: "Pending",
      text: "text-[#5F6368]",
      bg: "bg-[#F7F7F5]",
      border: "border-[#ECECE9]",
      icon: <Clock className="w-3.5 h-3.5 text-[#8A8F98]" />,
    },
    // 3. In Progress / Running
    in_progress: {
      label: "In Progress",
      text: "text-[#D97706]",
      bg: "bg-[#FFFBEB]",
      border: "border-[#FDE68A]",
      icon: <Clock className="w-3.5 h-3.5 text-[#D97706] animate-spin" />,
    },
    running: {
      label: "Running",
      text: "text-[#D97706]",
      bg: "bg-[#FFFBEB]",
      border: "border-[#FDE68A]",
      icon: <Clock className="w-3.5 h-3.5 text-[#D97706] animate-spin" />,
    },
    executing: {
      label: "Executing",
      text: "text-[#2563EB]",
      bg: "bg-[#EFF6FF]",
      border: "border-[#BFDBFE]",
      icon: <Clock className="w-3.5 h-3.5 text-[#2563EB] animate-spin" />,
    },
    // 4. Completed / Succeeded
    succeeded: {
      label: "Succeeded",
      text: "text-[#15803D]",
      bg: "bg-[#F0FDF4]",
      border: "border-[#BBF7D0]",
      icon: <CheckCircle2 className="w-3.5 h-3.5 text-[#15803D]" />,
    },
    completed: {
      label: "Completed",
      text: "text-[#15803D]",
      bg: "bg-[#F0FDF4]",
      border: "border-[#BBF7D0]",
      icon: <CheckCircle2 className="w-3.5 h-3.5 text-[#15803D]" />,
    },
    // 5. Verification States
    verified: {
      label: "Verified Proof",
      text: "text-[#15803D]",
      bg: "bg-[#F0FDF4]",
      border: "border-[#86EFAC]",
      icon: <ShieldCheck className="w-3.5 h-3.5 text-[#15803D]" />,
    },
    not_verified: {
      label: "Not Verified",
      text: "text-[#DC2626]",
      bg: "bg-[#FEF2F2]",
      border: "border-[#FECACA]",
      icon: <AlertCircle className="w-3.5 h-3.5 text-[#DC2626]" />,
    },
    failed: {
      label: "Failed",
      text: "text-[#DC2626]",
      bg: "bg-[#FEF2F2]",
      border: "border-[#FECACA]",
      icon: <AlertCircle className="w-3.5 h-3.5 text-[#DC2626]" />,
    },
    blocked: {
      label: "Blocked",
      text: "text-[#D97706]",
      bg: "bg-[#FFFBEB]",
      border: "border-[#FDE68A]",
      icon: <Lock className="w-3.5 h-3.5 text-[#D97706]" />,
    },
    needs_review: {
      label: "Review Required",
      text: "text-[#7C3AED]",
      bg: "bg-[#FAF5FF]",
      border: "border-[#E9D5FF]",
      icon: <AlertTriangle className="w-3.5 h-3.5 text-[#7C3AED]" />,
    },
    requires_approval: {
      label: "Awaiting Approval",
      text: "text-[#7C3AED]",
      bg: "bg-[#FAF5FF]",
      border: "border-[#E9D5FF]",
      icon: <AlertTriangle className="w-3.5 h-3.5 text-[#7C3AED]" />,
    },
    // Epistemic Uncertainty Representations (Section 44)
    confirmed: {
      label: "Confirmed Fact",
      text: "text-[#15803D]",
      bg: "bg-[#F0FDF4]",
      border: "border-[#BBF7D0]",
      icon: <Check className="w-3.5 h-3.5 text-[#15803D]" />,
    },
    inferred: {
      label: "AI Inferred",
      text: "text-[#2563EB]",
      bg: "bg-[#EFF6FF]",
      border: "border-[#BFDBFE]",
      icon: <Sparkles className="w-3.5 h-3.5 text-[#2563EB]" />,
    },
    unknown: {
      label: "Unknown / Unobserved",
      text: "text-[#5F6368]",
      bg: "bg-[#F7F7F5]",
      border: "border-[#ECECE9]",
      icon: <HelpCircle className="w-3.5 h-3.5 text-[#8A8F98]" />,
    },
    conflict: {
      label: "Constraint Conflict",
      text: "text-[#DC2626]",
      bg: "bg-[#FEF2F2]",
      border: "border-[#FECACA]",
      icon: <Flame className="w-3.5 h-3.5 text-[#DC2626]" />,
    },
    connected: {
      label: "Connected",
      text: "text-[#15803D]",
      bg: "bg-[#F0FDF4]",
      border: "border-[#BBF7D0]",
      icon: <span className="w-2 h-2 rounded-full bg-[#15803D]" />,
    },
    disconnected: {
      label: "Disconnected",
      text: "text-[#5F6368]",
      bg: "bg-[#F7F7F5]",
      border: "border-[#ECECE9]",
      icon: <span className="w-2 h-2 rounded-full bg-[#8A8F98]" />,
    },
    degraded: {
      label: "Degraded",
      text: "text-[#D97706]",
      bg: "bg-[#FFFBEB]",
      border: "border-[#FDE68A]",
      icon: <span className="w-2 h-2 rounded-full bg-[#D97706]" />,
    },
  };

  const item = config[norm] || {
    label: status?.replace(/_/g, " ").toUpperCase() || "UNKNOWN",
    text: "text-[#5F6368]",
    bg: "bg-[#F7F7F5]",
    border: "border-[#ECECE9]",
    icon: <Clock className="w-3.5 h-3.5 text-[#8A8F98]" />,
  };

  const sizeClasses = size === "sm" 
    ? "px-2 py-0.5 text-xs gap-1.5" 
    : "px-2.5 py-1 text-xs gap-2";

  return (
    <span
      className={cn(
        "inline-flex items-center font-medium rounded-lg border font-mono tracking-tight select-none transition-all",
        item.bg,
        item.border,
        item.text,
        sizeClasses,
        className
      )}
    >
      {showIcon && item.icon}
      <span>{item.label}</span>
    </span>
  );
}
