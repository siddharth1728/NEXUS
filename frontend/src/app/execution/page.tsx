"use client";
import { useEffect, useState } from "react";
import { executionsApi, ExecutionRequest } from "@/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import Link from "next/link";
import { AlertCircle, CheckCircle2, Shield, Search, Filter, TerminalSquare } from "lucide-react";

export default function ExecutionPage() {
  const [executions, setExecutions] = useState<ExecutionRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        const data = await executionsApi.getExecutions();
        setExecutions(data);
      } catch (err: any) {
        setError(err.message || "Failed to load executions");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const filteredExecutions = executions.filter(e => 
    e.id.toLowerCase().includes(searchQuery.toLowerCase()) || 
    e.tool_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    e.connector_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="flex justify-between items-end shrink-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">Execution Center</h1>
          <p className="text-[13px] text-muted mt-1.5 font-medium">Monitor and authorize execution requests to external systems.</p>
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
          placeholder="Search executions by id, tool, or connector..." 
          className="bg-transparent border-none outline-none flex-1 py-1.5 text-[13px] text-text placeholder:text-muted/70"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <div className="pr-3 text-[10px] font-mono text-muted/50 hidden sm:block">
          {filteredExecutions.length} results
        </div>
      </div>

      <div className="flex-1 overflow-hidden flex flex-col border border-border/60 rounded-xl bg-surface/30 shadow-sm">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted gap-4">
            <div className="w-5 h-5 rounded-full border-2 border-muted/30 border-t-info animate-spin"></div>
            <div className="text-[13px] font-medium">Loading execution stream...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-64 text-danger bg-danger-bg/10 text-[13px] font-medium">
            {error}
          </div>
        ) : filteredExecutions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted">
            <div className="w-12 h-12 rounded-full bg-surface border border-border flex items-center justify-center mb-4">
              <TerminalSquare className="w-5 h-5 text-muted/50" />
            </div>
            <p className="text-[14px] font-medium text-text">No executions found</p>
            <p className="text-[12px] mt-1">System is idle.</p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-left text-[13px] whitespace-nowrap">
              <thead className="bg-surface/80 border-b border-border/60 sticky top-0 backdrop-blur-md z-10">
                <tr>
                  <th className="px-5 py-3 font-semibold text-muted text-[11px] uppercase tracking-wider w-[25%]">Execution ID</th>
                  <th className="px-5 py-3 font-semibold text-muted text-[11px] uppercase tracking-wider">Connector</th>
                  <th className="px-5 py-3 font-semibold text-muted text-[11px] uppercase tracking-wider">Tool</th>
                  <th className="px-5 py-3 font-semibold text-muted text-[11px] uppercase tracking-wider">State</th>
                  <th className="px-5 py-3 font-semibold text-muted text-[11px] uppercase tracking-wider text-right">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {filteredExecutions.map((exec) => (
                  <tr key={exec.id} className="hover:bg-surface-hover/80 transition-colors group cursor-pointer">
                    <td className="px-5 py-3.5">
                      <div className="flex flex-col gap-1">
                        <Link href={`/execution/${exec.id}`} className="font-mono text-[12px] text-text hover:text-info transition-colors truncate">
                          {exec.id}
                        </Link>
                        <div className="flex items-center gap-1.5 text-[11px] text-muted/70 font-mono">
                          <span className="bg-border/50 px-1 rounded text-muted">ACTION</span>
                          <Link href={`/actions/${exec.action_id}`} className="hover:text-text transition-colors truncate max-w-[150px]">
                            {exec.action_id.split('-')[0]}...
                          </Link>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="font-mono text-[12px] text-text bg-surface border border-border px-1.5 py-0.5 rounded">
                        {exec.connector_name}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="font-mono text-[12px] text-text bg-surface border border-border px-1.5 py-0.5 rounded">
                        {exec.tool_name}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex flex-col gap-2 items-start">
                        <StatusBadge status={exec.state} type="execution" />
                        {exec.state === 'AWAITING_APPROVAL' && (
                           <Link href={`/execution/${exec.id}`} className="text-[10px] uppercase font-bold tracking-wider bg-warning/20 text-warning border border-warning/30 px-2 py-0.5 rounded hover:bg-warning/30 transition-colors">
                             Review Required
                           </Link>
                        )}
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-right text-muted text-[12px]">
                      {new Date(exec.updated_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })}
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
