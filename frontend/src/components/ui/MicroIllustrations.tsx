"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface IllustrationProps {
  className?: string;
  size?: number;
}

/**
 * 2D SVG Micro-illustration for Empty Actions / Work
 * Motif: A living causal line waiting for work to synthesize
 */
export function EmptyActionsIllustration({ className, size = 120 }: IllustrationProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("text-[#2563EB]", className)}
      aria-label="No actions illustration"
    >
      {/* Background soft circular pad */}
      <circle cx="60" cy="60" r="48" fill="#F7F7F5" stroke="#ECECE9" strokeWidth="1.5" />
      
      {/* Horizontal Living Line track */}
      <line x1="28" y1="60" x2="92" y2="60" stroke="#E5E7EB" strokeWidth="2" strokeLinecap="round" />
      <line 
        x1="28" 
        y1="60" 
        x2="92" 
        y2="60" 
        stroke="currentColor" 
        strokeWidth="2" 
        strokeLinecap="round"
        className="living-line-flow opacity-70" 
      />

      {/* Origin Node: Ingested Source */}
      <circle cx="38" cy="60" r="7" fill="white" stroke="#2563EB" strokeWidth="2" />
      <circle cx="38" cy="60" r="2.5" fill="#2563EB" />

      {/* Target Node: Synthesized Action waiting */}
      <rect 
        x="72" 
        y="50" 
        width="20" 
        height="20" 
        rx="5" 
        fill="white" 
        stroke="#8A8F98" 
        strokeWidth="1.5" 
        strokeDasharray="3 3"
      />
      <circle cx="82" cy="60" r="2" fill="#8A8F98" />
    </svg>
  );
}

/**
 * 2D SVG Micro-illustration for Documents / Intelligence Sources
 * Motif: Semantic layers / document pages assembling
 */
export function EmptyDocumentsIllustration({ className, size = 120 }: IllustrationProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("text-[#2563EB]", className)}
      aria-label="No documents illustration"
    >
      <circle cx="60" cy="60" r="48" fill="#F7F7F5" stroke="#ECECE9" strokeWidth="1.5" />

      {/* Back Document Sheet */}
      <rect 
        x="42" 
        y="32" 
        width="44" 
        height="56" 
        rx="6" 
        fill="white" 
        stroke="#E5E7EB" 
        strokeWidth="1.5"
        transform="rotate(6 42 32)"
      />

      {/* Front Document Sheet */}
      <rect 
        x="36" 
        y="30" 
        width="44" 
        height="56" 
        rx="6" 
        fill="white" 
        stroke="#D1D5DB" 
        strokeWidth="1.5" 
      />

      {/* Extracted text lines */}
      <line x1="44" y1="42" x2="68" y2="42" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" />
      <line x1="44" y1="50" x2="72" y2="50" stroke="#E5E7EB" strokeWidth="2" strokeLinecap="round" />
      <line x1="44" y1="58" x2="62" y2="58" stroke="#E5E7EB" strokeWidth="2" strokeLinecap="round" />
      <line x1="44" y1="66" x2="70" y2="66" stroke="#ECECE9" strokeWidth="2" strokeLinecap="round" />

      {/* Extraction Pulse Point */}
      <circle cx="70" cy="74" r="9" fill="#EFF6FF" stroke="#2563EB" strokeWidth="1.5" />
      <path d="M67 74L69.5 76.5L73.5 71.5" stroke="#2563EB" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/**
 * 2D SVG Micro-illustration for Verification Pending / Active Proof Checking
 * Motif: Independent observer focusing on external state
 */
export function VerificationPendingIllustration({ className, size = 120 }: IllustrationProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("text-[#15803D]", className)}
      aria-label="Verification illustration"
    >
      <circle cx="60" cy="60" r="48" fill="#F7F7F5" stroke="#ECECE9" strokeWidth="1.5" />

      {/* Shield Contour */}
      <path 
        d="M60 34L76 40V58C76 68.5 69.2 78.3 60 81C50.8 78.3 44 68.5 44 58V40L60 34Z" 
        fill="white" 
        stroke="#15803D" 
        strokeWidth="2" 
        strokeLinejoin="round"
      />

      {/* Concentric Proof Target */}
      <circle cx="60" cy="57" r="10" stroke="#86EFAC" strokeWidth="1.5" strokeDasharray="3 3" />
      <circle cx="60" cy="57" r="4" fill="#15803D" />
    </svg>
  );
}

/**
 * 2D SVG Micro-illustration for Verified Outcome
 * Motif: Complete closed causal loop
 */
export function VerifiedProofIllustration({ className, size = 120 }: IllustrationProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("text-[#15803D]", className)}
      aria-label="Verified outcome illustration"
    >
      <circle cx="60" cy="60" r="48" fill="#F0FDF4" stroke="#BBF7D0" strokeWidth="1.5" />
      <circle cx="60" cy="60" r="28" fill="white" stroke="#15803D" strokeWidth="2" />
      <path 
        d="M51 60L57 66L69 54" 
        stroke="#15803D" 
        strokeWidth="2.5" 
        strokeLinecap="round" 
        strokeLinejoin="round" 
      />
    </svg>
  );
}
