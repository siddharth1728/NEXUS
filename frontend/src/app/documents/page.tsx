"use client";
import { useEffect, useState } from "react";
import { documentsApi, Document } from "@/api";
import Link from "next/link";
import { FileText, Search, Database, Filter } from "lucide-react";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        const data = await documentsApi.getDocuments();
        setDocuments(data);
      } catch (err: any) {
        setError(err.message || "Failed to load documents");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const filteredDocs = documents.filter(d => 
    d.filename.toLowerCase().includes(searchQuery.toLowerCase()) || 
    d.mime_type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  function formatBytes(bytes: number, decimals = 2) {
    if (!+bytes) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
  }

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="flex justify-between items-end shrink-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">Knowledge Vault</h1>
          <p className="text-[13px] text-muted mt-1.5 font-medium">Ingested documents and extraction sources.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 text-[12px] font-medium text-muted bg-surface border border-border px-3 py-1.5 rounded-md hover:bg-surface-hover hover:text-text transition-colors">
            <Filter className="w-3.5 h-3.5" /> Filter
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3 bg-surface/50 p-1.5 rounded-lg border border-border/60 shrink-0 focus-within:border-border focus-within:bg-surface transition-colors">
        <div className="flex items-center pl-3 text-muted">
          <Search className="w-4 h-4" />
        </div>
        <input 
          type="text" 
          placeholder="Search documents by name or type..." 
          className="bg-transparent border-none outline-none flex-1 py-1.5 text-[13px] text-text placeholder:text-muted/70"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <div className="pr-3 text-[10px] font-mono text-muted/50 hidden sm:block">
          {filteredDocs.length} files
        </div>
      </div>

      <div className="flex-1 overflow-hidden flex flex-col border border-border/60 rounded-xl bg-surface/30 shadow-sm">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted gap-4">
            <div className="w-5 h-5 rounded-full border-2 border-muted/30 border-t-accent animate-spin"></div>
            <div className="text-[13px] font-medium">Loading knowledge graph...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-64 text-danger bg-danger-bg/10 text-[13px] font-medium">
            {error}
          </div>
        ) : filteredDocs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted">
            <div className="w-12 h-12 rounded-full bg-surface border border-border flex items-center justify-center mb-4">
              <Database className="w-5 h-5 text-muted/50" />
            </div>
            <p className="text-[14px] font-medium text-text">No documents found</p>
            <p className="text-[12px] mt-1">Upload documents via the API to provide context.</p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-left text-[13px] whitespace-nowrap">
              <thead className="bg-surface/80 border-b border-border/60 sticky top-0 backdrop-blur-md z-10">
                <tr>
                  <th className="px-5 py-3 font-semibold text-muted text-[11px] uppercase tracking-wider w-[40%]">Filename</th>
                  <th className="px-5 py-3 font-semibold text-muted text-[11px] uppercase tracking-wider">Type</th>
                  <th className="px-5 py-3 font-semibold text-muted text-[11px] uppercase tracking-wider text-right">Size</th>
                  <th className="px-5 py-3 font-semibold text-muted text-[11px] uppercase tracking-wider text-right">Ingested</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-surface-hover/80 transition-colors group cursor-pointer">
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className="p-1.5 bg-accent/10 rounded border border-accent/20 shrink-0 group-hover:bg-accent/20 transition-colors">
                          <FileText className="w-4 h-4 text-accent" />
                        </div>
                        <div className="flex flex-col">
                          <Link href={`/documents/${doc.id}`} className="font-medium text-text group-hover:text-accent transition-colors truncate max-w-[300px]">
                            {doc.filename}
                          </Link>
                          <span className="font-mono text-[10px] text-muted/70 truncate max-w-[300px] mt-0.5">{doc.id}</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="font-mono text-[11px] text-muted bg-background border border-border/60 px-1.5 py-0.5 rounded">
                        {doc.mime_type}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono text-[12px] text-muted">
                      {formatBytes(doc.size_bytes)}
                    </td>
                    <td className="px-5 py-3.5 text-right text-[12px] text-muted">
                      {new Date(doc.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
