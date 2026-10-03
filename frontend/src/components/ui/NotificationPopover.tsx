"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  Bell, 
  AlertTriangle, 
  ShieldCheck, 
  AlertCircle, 
  PlayCircle, 
  Lock, 
  X,
  ChevronRight
} from "lucide-react";

export interface SystemNotification {
  id: string;
  type: "approval_required" | "verification_failed" | "action_ready" | "workflow_blocked";
  title: string;
  description: string;
  timestamp: string;
  actionHref: string;
  actionLabel: string;
}

export function NotificationPopover() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<SystemNotification[]>([
    {
      id: "notif-1",
      type: "approval_required",
      title: "Action Requires Approval",
      description: "Create GitHub Issue in acme/nexus requires manual authorization before dispatch.",
      timestamp: "10m ago",
      actionHref: "/execution",
      actionLabel: "Authorize",
    },
    {
      id: "notif-2",
      type: "verification_failed",
      title: "Verification Discrepancy",
      description: "Sync Security Policy to Webhook Gateway diverged from external observed state.",
      timestamp: "1h ago",
      actionHref: "/verification",
      actionLabel: "Audit Evidence",
    },
    {
      id: "notif-3",
      type: "action_ready",
      title: "Action Unlocked & Ready",
      description: "Review security configuration dependencies cleared by upstream specification.",
      timestamp: "2h ago",
      actionHref: "/actions",
      actionLabel: "Review",
    },
  ]);

  const dismissNotification = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const getIcon = (type: SystemNotification["type"]) => {
    switch (type) {
      case "approval_required":
        return <AlertTriangle className="w-4 h-4 text-[#7C3AED]" />;
      case "verification_failed":
        return <AlertCircle className="w-4 h-4 text-[#DC2626]" />;
      case "action_ready":
        return <PlayCircle className="w-4 h-4 text-[#2563EB]" />;
      case "workflow_blocked":
        return <Lock className="w-4 h-4 text-[#D97706]" />;
    }
  };

  return (
    <div className="relative">
      {/* Bell Trigger */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg text-[#5F6368] hover:text-[#171717] hover:bg-[#F7F7F5] transition-all cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2563EB]"
        aria-label="System notifications"
      >
        <Bell className="w-5 h-5" />
        {notifications.length > 0 && (
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#2563EB] ring-2 ring-white animate-pulse" />
        )}
      </button>

      {/* Popover Card */}
      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)} 
          />
          <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-2xl border border-[#E5E7EB] shadow-2xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150">
            {/* Popover Header */}
            <div className="px-5 py-3.5 border-b border-[#ECECE9] bg-[#F7F7F5] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-semibold tracking-wider text-[#171717] uppercase">
                  Actionable Notifications
                </span>
                <span className="text-[11px] font-mono px-2 py-0.2 rounded-full bg-white text-[#2563EB] border border-[#BFDBFE]">
                  {notifications.length}
                </span>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-[#8A8F98] hover:text-[#171717] p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Notification Stream */}
            <div className="max-h-80 overflow-y-auto divide-y divide-[#ECECE9]">
              {notifications.length === 0 ? (
                <div className="p-8 text-center text-xs text-[#5F6368] space-y-1">
                  <ShieldCheck className="w-6 h-6 text-[#15803D] mx-auto mb-2" />
                  <p className="font-semibold text-[#171717]">All operational gates clear</p>
                  <p>No actions require approval or review.</p>
                </div>
              ) : (
                notifications.map((n) => (
                  <div 
                    key={n.id}
                    className="p-4 hover:bg-[#FDFDFD] transition-colors space-y-2 group"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        {getIcon(n.type)}
                        <span className="text-xs font-semibold text-[#171717]">{n.title}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] font-mono text-[#8A8F98]">{n.timestamp}</span>
                        <button
                          onClick={(e) => dismissNotification(n.id, e)}
                          className="opacity-0 group-hover:opacity-100 p-0.5 text-[#8A8F98] hover:text-[#171717] transition-opacity"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    </div>

                    <p className="text-xs text-[#5F6368] leading-relaxed">
                      {n.description}
                    </p>

                    <div className="pt-1">
                      <Link 
                        href={n.actionHref}
                        onClick={() => setIsOpen(false)}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-[#2563EB] hover:text-[#1D4ED8]"
                      >
                        <span>{n.actionLabel}</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Footer */}
            <div className="p-3 bg-[#F7F7F5] border-t border-[#ECECE9] text-center text-[11px] text-[#8A8F98] font-mono">
              Zero-noise operational telemetry
            </div>
          </div>
        </>
      )}
    </div>
  );
}
