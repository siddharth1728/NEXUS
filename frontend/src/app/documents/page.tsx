"use client";
import { useEffect, useState } from "react";
import { documentsApi, Document } from "@/api";
import Link from "next/link";
import { FileText, Search, Database } from "lucide-react";

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
    <div className="space-y-6 max-w-7xl mx-auto h-full flex flex-col">
      <div className="flex justify-between items-center shrink-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Documents</h1>
          <p className="text-muted mt-1">Ingested knowledge and extraction sources.</p>
        </div>
      </div>

      <div className="flex items-center gap-4 bg-surface p-1 rounded-md border border-border shrink-0">
        <div className="flex items-center pl-3 text-muted">
          <Search className="w-4 h-4" />
        </div>
        <input 
          type="text" 
          placeholder="Search documents by name or type..." 
          className="bg-transparent border-none outline-none flex-1 py-2 text-sm text-text placeholder:text-muted"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="flex-1 overflow-hidden flex flex-col border border-border rounded-lg bg-surface">
        {loading ? (
          <div className="flex items-center justify-center h-64 text-muted">Loading documents...</div>
        ) : error ? (
          <div className="flex items-center justify-center h-64 text-danger">{error}</div>
        ) : filteredDocs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted">
            <Database className="w-12 h-12 mb-4 opacity-50" />
            <p>No documents found in the vault.</p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-background border-b border-border sticky top-0">
                <tr>
                  <th className="px-6 py-3 font-medium text-muted">Filename</th>
                  <th className="px-6 py-3 font-medium text-muted">Type</th>
                  <th className="px-6 py-3 font-medium text-muted">Size</th>
                  <th className="px-6 py-3 font-medium text-muted">Ingested Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-border/50 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-accent shrink-0" />
                        <Link href={`/documents/${doc.id}`} className="font-medium text-text group-hover:text-accent transition-colors truncate max-w-[300px]">
                          {doc.filename}
                        </Link>
                      </div>
                    </td>
                    <td className="px-6 py-4 font-mono text-muted text-xs">
                      {doc.mime_type}
                    </td>
                    <td className="px-6 py-4 font-mono">
                      {formatBytes(doc.size_bytes)}
                    </td>
                    <td className="px-6 py-4 text-muted">
                      {new Date(doc.created_at).toLocaleString()}
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
