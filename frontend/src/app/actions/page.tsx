"use client";
import { useEffect, useState } from "react";
import { actionsApi, Action } from "@/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import Link from "next/link";
import { Calendar, Search } from "lucide-react";

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
    <div className="space-y-6 max-w-7xl mx-auto h-full flex flex-col">
      <div className="flex justify-between items-center shrink-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Actions</h1>
          <p className="text-muted mt-1">Context-driven tasks awaiting execution or verification.</p>
        </div>
      </div>

      <div className="flex items-center gap-4 bg-surface p-1 rounded-md border border-border shrink-0">
        <div className="flex items-center pl-3 text-muted">
          <Search className="w-4 h-4" />
        </div>
        <input 
          type="text" 
          placeholder="Search actions..." 
          className="bg-transparent border-none outline-none flex-1 py-2 text-sm text-text placeholder:text-muted"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="flex-1 overflow-hidden flex flex-col border border-border rounded-lg bg-surface">
        {loading ? (
          <div className="flex items-center justify-center h-64 text-muted">Loading actions...</div>
        ) : error ? (
          <div className="flex items-center justify-center h-64 text-danger">{error}</div>
        ) : filteredActions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted">
            <CheckSquareIcon className="w-12 h-12 mb-4 opacity-50" />
            <p>No actions found.</p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-background border-b border-border sticky top-0">
                <tr>
                  <th className="px-6 py-3 font-medium text-muted">Title</th>
                  <th className="px-6 py-3 font-medium text-muted">Status</th>
                  <th className="px-6 py-3 font-medium text-muted">Priority</th>
                  <th className="px-6 py-3 font-medium text-muted">Confidence</th>
                  <th className="px-6 py-3 font-medium text-muted">Due Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredActions.map((action) => (
                  <tr key={action.id} className="hover:bg-border/50 transition-colors group">
                    <td className="px-6 py-4 w-full">
                      <Link href={`/actions/${action.id}`} className="font-semibold text-text group-hover:text-accent transition-colors block truncate max-w-[400px]">
                        {action.title}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={action.status} />
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-mono text-muted">{action.priority}</span>
                    </td>
                    <td className="px-6 py-4">
                      {action.confidence}
                    </td>
                    <td className="px-6 py-4 text-muted flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      {action.due_date ? new Date(action.due_date).toLocaleDateString() : 'None'}
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
