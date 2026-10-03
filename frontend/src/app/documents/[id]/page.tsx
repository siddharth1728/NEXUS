"use client";

import React, { use } from "react";
import Link from "next/link";
import { 
  ArrowLeft, 
  HardDrive, 
  Quote, 
  CheckSquare,
  ArrowRight
} from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function DocumentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  const document = {
    id,
    filename: "Architecture_Guidelines_v2.pdf",
    mime_type: "application/pdf",
    size_bytes: 425980,
    content_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    storage_path: "artifacts/tenants/00000000-0000-4000-8000-000000000001/Architecture_Guidelines_v2.pdf",
    created_at: "2026-10-02T12:00:00.000Z",
    chunks: [
      {
        index: 0,
        section: "Section 1: Service Mesh Architecture",
        content: "NEXUS operates as an autonomous context-to-action engine. Ingress traffic is strictly partitioned by tenant ID."
      },
      {
        index: 1,
        section: "Section 3.2: Edge Gateway Security",
        content: "All client tokens must enforce JWKS signature validation before request dispatch. Keys rotate automatically every 24 hours."
      }
    ],
    facts: [
      "JWKS key rotation interval set to 24h",
      "Perimeter gateway rejects unverified bearer tokens",
      "Multi-tenant data partitioning enforced in database schema"
    ]
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div>
        <Link 
          href="/documents" 
          className="inline-flex items-center text-sm font-medium text-[#5F6368] hover:text-[#171717] transition-colors gap-2"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Intelligence Sources
        </Link>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-4 border-b border-[#ECECE9] pb-6">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono font-medium text-[#2563EB] tracking-wider uppercase">
              Source Record
            </span>
            <span className="text-xs font-mono text-[#8A8F98]">ID: {document.id}</span>
          </div>
          <h1 className="font-display text-4xl sm:text-5xl text-[#171717]">
            {document.filename}
          </h1>
          <p className="text-sm text-[#5F6368] font-mono">
            {document.mime_type.toUpperCase()} · {(document.size_bytes / 1024).toFixed(1)} KB · Ingested {new Date(document.created_at).toLocaleDateString()}
          </p>
        </div>

        <Link href="/actions">
          <Button variant="secondary" size="md">
            <CheckSquare className="w-4 h-4 mr-2 text-[#2563EB]" />
            <span>Derived Actions</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        {/* Chunks & Extracted Facts */}
        <div className="bg-white rounded-2xl border border-[#E5E7EB] p-8 space-y-6 shadow-2xs">
          <div className="flex items-center gap-2.5 pb-4 border-b border-[#ECECE9]">
            <Quote className="w-5 h-5 text-[#7C3AED]" />
            <h2 className="text-lg font-semibold text-[#171717]">
              Extracted Semantic Chunks
            </h2>
          </div>

          <div className="space-y-4">
            {document.chunks.map((chunk) => (
              <div key={chunk.index} className="p-5 rounded-xl bg-[#F7F7F5] border border-[#ECECE9] space-y-2">
                <span className="text-xs font-mono text-[#2563EB] font-semibold block">
                  CHUNK #{chunk.index + 1} · {chunk.section}
                </span>
                <p className="text-sm text-[#171717] leading-relaxed">{chunk.content}</p>
              </div>
            ))}
          </div>
        </div>

        {/* File Telemetry */}
        <div className="bg-white rounded-2xl border border-[#E5E7EB] p-8 space-y-6 shadow-2xs">
          <div className="flex items-center gap-2.5 pb-4 border-b border-[#ECECE9]">
            <HardDrive className="w-5 h-5 text-[#2563EB]" />
            <h2 className="text-lg font-semibold text-[#171717]">
              Storage & Provenance Integrity
            </h2>
          </div>

          <dl className="space-y-4 text-sm">
            <div className="flex justify-between py-2 border-b border-[#ECECE9]">
              <dt className="text-[#5F6368]">Payload Size</dt>
              <dd className="font-mono text-[#171717] font-medium">{(document.size_bytes / 1024).toFixed(1)} KB</dd>
            </div>
            <div className="flex flex-col gap-1 py-2 border-b border-[#ECECE9]">
              <dt className="text-[#5F6368]">SHA-256 Content Hash</dt>
              <dd className="font-mono text-xs text-[#171717] break-all">{document.content_hash}</dd>
            </div>
            <div className="flex justify-between py-2 border-b border-[#ECECE9]">
              <dt className="text-[#5F6368]">Tenant Storage Path</dt>
              <dd className="font-mono text-xs text-[#5F6368] truncate max-w-[240px]">{document.storage_path}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
