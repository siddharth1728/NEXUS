import React from "react";
import { cn } from "@/lib/utils";
import { CheckCircle2, AlertCircle, Clock, AlertTriangle, ShieldCheck, PlayCircle, Lock } from "lucide-react";

export type StatusType = 
  | "ready" 
  | "pending" 
  | "in_progress" 
  | "running" 
  | "executing"
  | "succeeded" 
  | "completed" 
  | "verified" 
  | "failed" 
  | "blocked" 
  | "needs_review" 
  | "requires_approval"
  | "connected"
  | "disconnected"
  | "degraded";

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
  className?: string;
  showIcon?: boolean;
}

export function StatusBadge({ status, size = "md", className, showIcon = true }: StatusBadgeProps) {
  const norm = status?.toLowerCase().replace(/[\s-]/g, "_") as StatusType;

  const config: Record<string, { label: string; text: string; bg: string; border: string; icon: React.ReactNode; dot?: string }> = {
    ready: {
      label: "Ready",
      text: "text-[#2563EB]",
      bg: "bg-[#EFF6FF]",
      border: "border-[#BFDBFE]",
      icon: <PlayCircle className="w-3 h-3 text-[#2563EB]" />,
    },
    pending: {
      label: "Pending",
      text: "text-[#5F6368]",
      bg: "bg-[#F2F2F0]",
      border: "border-[#E5E7EB]",
      icon: <Clock className="w-3 h-3 text-[#5F6368]" />,
    },
    in_progress: {
      label: "In Progress",
      text: "text-[#A65F00]",
      bg: "bg-[#FFFBEB]",
      border: "border-[#FDE68A]",
      icon: <Clock className="w-3 h-3 text-[#A65F00] animate-spin" />,
    },
    running: {
      label: "Running",
      text: "text-[#A65F00]",
      bg: "bg-[#FFFBEB]",
      border: "border-[#FDE68A]",
      icon: <Clock className="w-3 h-3 text-[#A65F00] animate-spin" />,
    },
    executing: {
      label: "Executing",
      text: "text-[#2563EB]",
      bg: "bg-[#EFF6FF]",
      border: "border-[#BFDBFE]",
      icon: <Clock className="w-3 h-3 text-[#2563EB] animate-spin" />,
    },
    succeeded: {
      label: "Succeeded",
      text: "text-[#17803D]",
      bg: "bg-[#F0FDF4]",
      border: "border-[#BBF7D0]",
      icon: <CheckCircle2 className="w-3 h-3 text-[#17803D]" />,
    },
    completed: {
      label: "Completed",
      text: "text-[#17803D]",
      bg: "bg-[#F0FDF4]",
      border: "border-[#BBF7D0]",
      icon: <CheckCircle2 className="w-3 h-3 text-[#17803D]" />,
    },
    verified: {
      label: "Verified",
      text: "text-[#17803D]",
      bg: "bg-[#F0FDF4]",
      border: "border-[#86EFAC]",
      icon: <ShieldCheck className="w-3 h-3 text-[#17803D]" />,
    },
    failed: {
      label: "Failed",
      text: "text-[#C62828]",
      bg: "bg-[#FEF2F2]",
      border: "border-[#FECACA]",
      icon: <AlertCircle className="w-3 h-3 text-[#C62828]" />,
    },
    blocked: {
      label: "Blocked",
      text: "text-[#78350F]",
      bg: "bg-[#FEF3C7]",
      border: "border-[#FDE68A]",
      icon: <Lock className="w-3 h-3 text-[#78350F]" />,
    },
    needs_review: {
      label: "Review Required",
      text: "text-[#7C3AED]",
      bg: "bg-[#FAF5FF]",
      border: "border-[#E9D5FF]",
      icon: <AlertTriangle className="w-3 h-3 text-[#7C3AED]" />,
    },
    requires_approval: {
      label: "Awaiting Approval",
      text: "text-[#7C3AED]",
      bg: "bg-[#FAF5FF]",
      border: "border-[#E9D5FF]",
      icon: <AlertTriangle className="w-3 h-3 text-[#7C3AED]" />,
    },
    connected: {
      label: "Connected",
      text: "text-[#17803D]",
      bg: "bg-[#F0FDF4]",
      border: "border-[#BBF7D0]",
      icon: <span className="w-1.5 h-1.5 rounded-full bg-[#17803D]" />,
    },
    disconnected: {
      label: "Disconnected",
      text: "text-[#5F6368]",
      bg: "bg-[#F2F2F0]",
      border: "border-[#E5E7EB]",
      icon: <span className="w-1.5 h-1.5 rounded-full bg-[#9CA3AF]" />,
    },
    degraded: {
      label: "Degraded",
      text: "text-[#A65F00]",
      bg: "bg-[#FFFBEB]",
      border: "border-[#FDE68A]",
      icon: <span className="w-1.5 h-1.5 rounded-full bg-[#A65F00]" />,
    },
  };

  const item = config[norm] || {
    label: status?.toUpperCase() || "UNKNOWN",
    text: "text-[#5F6368]",
    bg: "bg-[#F2F2F0]",
    border: "border-[#E5E7EB]",
    icon: <Clock className="w-3 h-3 text-[#5F6368]" />,
  };

  const sizeClasses = size === "sm" ? "px-1.5 py-0.5 text-[11px] gap-1" : "px-2 py-0.5 text-[12px] gap-1.5";

  return (
    <span
      className={cn(
        "inline-flex items-center font-medium rounded-[4px] border font-mono tracking-tight select-none",
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
