"use client";
import { useEffect, useState, use } from "react";
import { documentsApi, Document } from "@/api";
import Link from "next/link";
import { ArrowLeft, FileText, HardDrive, Hash, Calendar, FileJson } from "lucide-react";

export default function DocumentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await documentsApi.getDocument(resolvedParams.id);
        setDocument(data);
      } catch (err: any) {
        setError(err.message || "Failed to load document details");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [resolvedParams.id]);

  function formatBytes(bytes: number, decimals = 2) {
    if (!+bytes) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
  }

  if (loading) {
    return <div className="flex h-full items-center justify-center text-muted">Loading document details...</div>;
  }

  if (error || !document) {
    return <div className="flex h-full items-center justify-center text-danger">{error || "Document not found"}</div>;
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      <div>
        <Link href="/documents" className="inline-flex items-center text-sm text-muted hover:text-text mb-4 transition-colors">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back to Documents
        </Link>
        <div className="flex items-start gap-4">
          <div className="p-3 bg-accent/10 rounded-lg">
            <FileText className="w-8 h-8 text-accent" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{document.filename}</h1>
            <div className="flex items-center gap-4 mt-2">
              <span className="font-mono text-sm text-muted bg-surface px-2 py-1 rounded border border-border">
                {document.id}
              </span>
              <span className="text-sm font-medium text-text bg-border/50 px-2 py-1 rounded border border-border">
                {document.mime_type}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <section className="bg-surface border border-border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">File Information</h2>
          <dl className="space-y-4 text-sm">
            <div className="flex justify-between items-center">
              <dt className="text-muted flex items-center gap-2"><HardDrive className="w-4 h-4" /> Size</dt>
              <dd className="font-mono">{formatBytes(document.size_bytes)}</dd>
            </div>
            <div className="flex justify-between items-center">
              <dt className="text-muted flex items-center gap-2"><Hash className="w-4 h-4" /> SHA-256</dt>
              <dd className="font-mono text-xs truncate max-w-[200px]" title={document.content_hash}>{document.content_hash}</dd>
            </div>
            <div className="flex justify-between items-center">
              <dt className="text-muted flex items-center gap-2"><Calendar className="w-4 h-4" /> Uploaded</dt>
              <dd>{new Date(document.created_at).toLocaleString()}</dd>
            </div>
            <div className="flex justify-between items-center">
              <dt className="text-muted">Storage Path</dt>
              <dd className="font-mono text-xs truncate max-w-[200px]" title={document.storage_path}>{document.storage_path}</dd>
            </div>
          </dl>
        </section>

        <section className="bg-surface border border-border rounded-lg overflow-hidden flex flex-col">
          <div className="px-6 py-4 border-b border-border bg-background flex items-center gap-2">
            <FileJson className="w-4 h-4 text-muted" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">Metadata Payload</h2>
          </div>
          <div className="p-0 flex-1 overflow-auto">
            <pre className="p-6 text-xs font-mono text-text/90 bg-surface">
              {JSON.stringify(document.metadata_payload || {}, null, 2)}
            </pre>
          </div>
        </section>
      </div>
    </div>
  );
}
