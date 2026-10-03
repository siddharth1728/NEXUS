"use client";
import { useEffect, useState, use } from "react";
import { actionsApi, Action, ActionEdge } from "@/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import Link from "next/link";
import { ArrowLeft, Clock, FileText, PlayCircle, Shield, Link2, GitBranch } from "lucide-react";

export default function ActionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const [action, setAction] = useState<Action | null>(null);
  const [edges, setEdges] = useState<ActionEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [actionData, edgesData] = await Promise.all([
          actionsApi.getAction(resolvedParams.id),
          actionsApi.getActionEdges(resolvedParams.id).catch(() => []),
        ]);
        setAction(actionData);
        setEdges(edgesData);
      } catch (err: any) {
        setError(err.message || "Failed to load action details");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [resolvedParams.id]);

  if (loading) {
    return (
      <div className="flex flex-col h-[60vh] items-center justify-center text-muted gap-4">
        <div className="w-5 h-5 rounded-full border-2 border-muted/30 border-t-accent animate-spin"></div>
        <div className="text-[13px] font-medium">Loading action details...</div>
      </div>
    );
  }

  if (error || !action) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="text-danger bg-danger-bg/10 px-4 py-2 rounded-md border border-danger/20 text-[13px] font-medium">
          {error || "Action not found"}
        </div>
      </div>
    );
  }

  const dependencies = edges.filter(e => e.target_id === action.id && e.relation_type === 'depends_on');
  const blocks = edges.filter(e => e.source_id === action.id && e.relation_type === 'depends_on');

  return (
    <div className="space-y-6 mx-auto pb-12">
      <div>
        <Link href="/actions" className="inline-flex items-center text-[12px] font-medium text-muted hover:text-text mb-6 transition-colors">
          <ArrowLeft className="w-3.5 h-3.5 mr-1.5" /> Back to Action Center
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-text leading-tight max-w-3xl">{action.title}</h1>
            <div className="flex items-center gap-3 mt-3">
              <StatusBadge status={action.status} />
              <div className="h-4 w-px bg-border"></div>
              <span className="font-mono text-[11px] text-muted bg-surface/50 px-2 py-0.5 rounded border border-border/60 flex items-center gap-1.5">
                <Shield className="w-3 h-3 text-muted/70" />
                {action.id}
              </span>
            </div>
          </div>
          <button className="flex items-center gap-2 bg-text hover:bg-white text-background px-4 py-2 rounded-md text-[13px] font-medium transition-all shadow-sm group">
            <PlayCircle className="w-4 h-4 group-hover:text-accent transition-colors" />
            Simulate Execution
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-4">
        <div className="lg:col-span-2 space-y-6">
          <section className="bg-surface/30 border border-border/60 rounded-xl overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-border/40 bg-surface/50">
              <h2 className="text-[13px] font-semibold tracking-wide uppercase text-text">Description</h2>
            </div>
            <div className="p-6">
              <div className="text-[14px] text-text/90 whitespace-pre-wrap leading-relaxed">
                {action.description || "No description provided."}
              </div>
            </div>
          </section>

          <section className="bg-surface/30 border border-border/60 rounded-xl overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-border/40 bg-surface/50">
              <h2 className="text-[13px] font-semibold tracking-wide uppercase text-text">Context & Source</h2>
            </div>
            <div className="p-6">
              {action.source_document_id ? (
                <div className="flex items-start gap-4 p-4 bg-background border border-border/60 rounded-lg group hover:border-info/30 transition-colors">
                  <div className="bg-info-bg/50 p-2 rounded-md border border-info/20 mt-0.5">
                    <FileText className="w-4 h-4 text-info" />
                  </div>
                  <div>
                    <div className="text-[13px] font-medium text-text mb-1">Derived from Document</div>
                    <Link href={`/documents/${action.source_document_id}`} className="text-[12px] text-muted hover:text-info font-mono transition-colors break-all">
                      {action.source_document_id}
                    </Link>
                  </div>
                </div>
              ) : (
                <div className="text-muted text-[13px] italic bg-background border border-border/50 rounded-lg p-4 text-center">
                  No specific source document linked. Synthesized from global context.
                </div>
              )}
            </div>
          </section>

          <section className="bg-surface/30 border border-border/60 rounded-xl overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-border/40 bg-surface/50 flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-muted" />
              <h2 className="text-[13px] font-semibold tracking-wide uppercase text-text">Execution Graph</h2>
            </div>
            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-[11px] font-semibold text-muted mb-3 uppercase tracking-widest flex items-center gap-2">
                  <Link2 className="w-3 h-3" /> Depends On
                </h3>
                {dependencies.length > 0 ? (
                  <ul className="space-y-2">
                    {dependencies.map(dep => (
                      <li key={dep.id} className="text-[12px] bg-background border border-border/60 p-2.5 rounded-md flex items-center justify-between group hover:border-border transition-colors">
                        <Link href={`/actions/${dep.source_id}`} className="font-mono text-muted group-hover:text-text truncate pr-4">{dep.source_id}</Link>
                        <span className="text-muted/60 text-[10px] uppercase font-medium bg-surface px-1.5 py-0.5 rounded shrink-0">Req</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-[12px] text-muted/70 bg-background/50 border border-border/40 border-dashed rounded-md p-3 text-center">
                    No upstream dependencies
                  </div>
                )}
              </div>
              <div>
                <h3 className="text-[11px] font-semibold text-muted mb-3 uppercase tracking-widest flex items-center gap-2">
                  <Link2 className="w-3 h-3" /> Blocks
                </h3>
                {blocks.length > 0 ? (
                  <ul className="space-y-2">
                    {blocks.map(block => (
                      <li key={block.id} className="text-[12px] bg-background border border-border/60 p-2.5 rounded-md flex items-center justify-between group hover:border-border transition-colors">
                        <Link href={`/actions/${block.target_id}`} className="font-mono text-muted group-hover:text-text truncate pr-4">{block.target_id}</Link>
                        <span className="text-muted/60 text-[10px] uppercase font-medium bg-surface px-1.5 py-0.5 rounded shrink-0">Downstream</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-[12px] text-muted/70 bg-background/50 border border-border/40 border-dashed rounded-md p-3 text-center">
                    No downstream blockers
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <section className="bg-surface/30 border border-border/60 rounded-xl overflow-hidden shadow-sm sticky top-24">
            <div className="px-5 py-4 border-b border-border/40 bg-surface/50">
              <h2 className="text-[13px] font-semibold tracking-wide uppercase text-text">Metadata</h2>
            </div>
            <div className="p-5">
              <dl className="space-y-4 text-[13px]">
                <div className="flex justify-between items-center pb-3 border-b border-border/40">
                  <dt className="text-muted">Priority</dt>
                  <dd className="font-mono bg-surface border border-border px-2 py-0.5 rounded text-text text-[12px]">P{action.priority}</dd>
                </div>
                <div className="flex justify-between items-center pb-3 border-b border-border/40">
                  <dt className="text-muted">Confidence</dt>
                  <dd className="flex items-center gap-2">
                    <div className="w-16 h-1 bg-surface rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${action.confidence > 0.8 ? 'bg-success' : action.confidence > 0.5 ? 'bg-warning' : 'bg-danger'}`} 
                        style={{ width: `${action.confidence * 100}%` }}
                      ></div>
                    </div>
                    <span className="font-mono text-[12px]">{Math.round(action.confidence * 100)}%</span>
                  </dd>
                </div>
                <div className="flex justify-between items-center pb-3 border-b border-border/40">
                  <dt className="text-muted">Due Date</dt>
                  <dd className="flex items-center gap-1.5 text-text">
                    <Clock className="w-3.5 h-3.5 text-muted" />
                    {action.due_date ? new Date(action.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : 'None'}
                  </dd>
                </div>
                <div className="flex justify-between items-center pb-3 border-b border-border/40">
                  <dt className="text-muted">Hard Deadline</dt>
                  <dd className="text-text">{action.is_hard_deadline ? 'Yes' : 'No'}</dd>
                </div>
                <div className="flex justify-between items-center">
                  <dt className="text-muted">Created</dt>
                  <dd className="text-muted font-mono text-[12px]">{new Date(action.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}</dd>
                </div>
              </dl>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
