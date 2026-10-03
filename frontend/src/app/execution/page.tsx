"use client";
import { useEffect, useState } from "react";
import { executionsApi, ExecutionRequest } from "@/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import Link from "next/link";
import { AlertCircle, CheckCircle2, Shield, Search } from "lucide-react";

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
    <div className="space-y-6 max-w-7xl mx-auto h-full flex flex-col">
      <div className="flex justify-between items-center shrink-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Execution Center</h1>
          <p className="text-muted mt-1">Monitor and authorize execution requests to external systems.</p>
        </div>
      </div>

      <div className="flex items-center gap-4 bg-surface p-1 rounded-md border border-border shrink-0">
        <div className="flex items-center pl-3 text-muted">
          <Search className="w-4 h-4" />
        </div>
        <input 
          type="text" 
          placeholder="Search executions (id, tool, connector)..." 
          className="bg-transparent border-none outline-none flex-1 py-2 text-sm text-text placeholder:text-muted"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="flex-1 overflow-hidden flex flex-col border border-border rounded-lg bg-surface">
        {loading ? (
          <div className="flex items-center justify-center h-64 text-muted">Loading executions...</div>
        ) : error ? (
          <div className="flex items-center justify-center h-64 text-danger">{error}</div>
        ) : filteredExecutions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted">
            <Shield className="w-12 h-12 mb-4 opacity-50" />
            <p>No executions found.</p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-background border-b border-border sticky top-0">
                <tr>
                  <th className="px-6 py-3 font-medium text-muted">ID / Action</th>
                  <th className="px-6 py-3 font-medium text-muted">Connector</th>
                  <th className="px-6 py-3 font-medium text-muted">Tool</th>
                  <th className="px-6 py-3 font-medium text-muted">State</th>
                  <th className="px-6 py-3 font-medium text-muted">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredExecutions.map((exec) => (
                  <tr key={exec.id} className="hover:bg-border/50 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex flex-col">
                        <Link href={`/execution/${exec.id}`} className="font-mono text-text hover:text-accent font-medium truncate max-w-[200px] mb-1">
                          {exec.id}
                        </Link>
                        <Link href={`/actions/${exec.action_id}`} className="text-xs text-muted hover:underline font-mono truncate max-w-[200px]">
                          Action: {exec.action_id.split('-')[0]}...
                        </Link>
                      </div>
                    </td>
                    <td className="px-6 py-4 font-mono text-muted">
                      {exec.connector_name}
                    </td>
                    <td className="px-6 py-4 font-mono">
                      {exec.tool_name}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={exec.state} type="execution" />
                      {exec.state === 'AWAITING_APPROVAL' && (
                         <div className="mt-2">
                           <Link href={`/execution/${exec.id}`} className="text-xs bg-warning text-warning-foreground px-2 py-1 rounded hover:opacity-80 transition-opacity">
                             Review Required
                           </Link>
                         </div>
                      )}
                    </td>
                    <td className="px-6 py-4 text-muted">
                      {new Date(exec.updated_at).toLocaleString()}
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
