"use client";
import { useEffect, useState } from "react";
import { actionsApi, Action } from "@/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import Link from "next/link";
import { Calendar, Search, Filter, ArrowDownUp } from "lucide-react";

export default function ActionsPage() {
  const [actions, setActions] = useState<Action[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    async function loadActions() {
      try {
        const data = await actionsApi.getActions();
        setActions(data);
      } catch (err: any) {
        setError(err.message || "Failed to load actions");
      } finally {
        setLoading(false);
      }
    }
    loadActions();
  }, []);

  const filteredActions = actions.filter(a => 
    a.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
    a.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="flex justify-between items-end shrink-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">Action Center</h1>
          <p className="text-[13px] text-muted mt-1.5 font-medium">Manage, approve, and monitor context-driven tasks.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 text-[12px] font-medium text-muted bg-surface border border-border px-3 py-1.5 rounded-md hover:bg-surface-hover hover:text-text transition-colors">
            <Filter className="w-3.5 h-3.5" /> Filter
          </button>
          <button className="flex items-center gap-2 text-[12px] font-medium text-muted bg-surface border border-border px-3 py-1.5 rounded-md hover:bg-surface-hover hover:text-text transition-colors">
            <ArrowDownUp className="w-3.5 h-3.5" /> Sort
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3 bg-surface/50 p-1.5 rounded-lg border border-border/60 shrink-0 focus-within:border-border focus-within:bg-surface transition-colors">
        <div className="flex items-center pl-3 text-muted">
          <Search className="w-4 h-4" />
        </div>
        <input 
          type="text" 
          placeholder="Search actions by title or description..." 
          className="bg-transparent border-none outline-none flex-1 py-1.5 text-[13px] text-text placeholder:text-muted/70"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <div className="pr-3 text-[10px] font-mono text-muted/50 hidden sm:block">
          {filteredActions.length} results
        </div>
      </div>

      <div className="flex-1 overflow-hidden flex flex-col border border-border/60 rounded-xl bg-surface/30 shadow-sm">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted gap-4">
            <div className="w-5 h-5 rounded-full border-2 border-muted/30 border-t-accent animate-spin"></div>
            <div className="text-[13px] font-medium">Loading action graph...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-64 text-danger bg-danger-bg/10 text-[13px] font-medium">
            {error}
          </div>
        ) : filteredActions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted">
            <div className="w-12 h-12 rounded-full bg-surface border border-border flex items-center justify-center mb-4">
              <CheckSquareIcon className="w-5 h-5 text-muted/50" />
            </div>
            <p className="text-[14px] font-medium text-text">No actions found</p>
            <p className="text-[12px] mt-1">Try adjusting your search query.</p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-left text-[13px] whitespace-nowrap">
              <thead className="bg-surface/80 border-b border-border/60 sticky top-0 backdrop-blur-md z-10">
                <tr>
                  <th className="px-5 py-3 font-semibold text-muted text-[11px] uppercase tracking-wider w-[40%]">Action</th>
                  <th className="px-5 py-3 font-semibold text-muted text-[11px] uppercase tracking-wider">Status</th>
                  <th className="px-5 py-3 font-semibold text-muted text-[11px] uppercase tracking-wider">Priority</th>
                  <th className="px-5 py-3 font-semibold text-muted text-[11px] uppercase tracking-wider">Confidence</th>
                  <th className="px-5 py-3 font-semibold text-muted text-[11px] uppercase tracking-wider text-right">Due Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {filteredActions.map((action) => (
                  <tr key={action.id} className="hover:bg-surface-hover/80 transition-colors group cursor-pointer">
                    <td className="px-5 py-3.5">
                      <Link href={`/actions/${action.id}`} className="block">
                        <div className="font-semibold text-text group-hover:text-info transition-colors truncate max-w-[400px]">
                          {action.title}
                        </div>
                        <div className="font-mono text-[10px] text-muted/70 mt-1 truncate max-w-[400px]">
                          {action.id}
                        </div>
                      </Link>
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={action.status} />
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-1.5">
                        <div className={`w-1.5 h-1.5 rounded-full ${action.priority === 1 ? 'bg-danger' : action.priority === 2 ? 'bg-warning' : 'bg-muted'}`}></div>
                        <span className="font-mono text-muted text-[12px]">P{action.priority}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-surface rounded-full overflow-hidden border border-border/50">
                          <div 
                            className={`h-full ${action.confidence > 0.8 ? 'bg-success' : action.confidence > 0.5 ? 'bg-warning' : 'bg-danger'}`} 
                            style={{ width: `${action.confidence * 100}%` }}
                          ></div>
                        </div>
                        <span className="font-mono text-[11px] text-muted">
                          {Math.round(action.confidence * 100)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-right text-muted">
                      <div className="flex items-center justify-end gap-1.5 text-[12px]">
                        <Calendar className="w-3.5 h-3.5 text-muted/70" />
                        {action.due_date ? new Date(action.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : 'None'}
                      </div>
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

function CheckSquareIcon(props: any) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 11 12 14 22 4"></polyline>
      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
    </svg>
  );
}
