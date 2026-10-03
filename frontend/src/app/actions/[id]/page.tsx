"use client";
import { useEffect, useState, use } from "react";
import { actionsApi, Action, ActionEdge } from "@/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import Link from "next/link";
import { ArrowLeft, Clock, FileText, PlayCircle } from "lucide-react";

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
          actionsApi.getActionEdges(resolvedParams.id).catch(() => []), // Ignore edge fetch errors if not implemented
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
    return <div className="flex h-full items-center justify-center text-muted">Loading action context...</div>;
  }

  if (error || !action) {
    return <div className="flex h-full items-center justify-center text-danger">{error || "Action not found"}</div>;
  }

  const dependencies = edges.filter(e => e.target_id === action.id && e.relation_type === 'depends_on');
  const blocks = edges.filter(e => e.source_id === action.id && e.relation_type === 'depends_on');

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      <div>
        <Link href="/actions" className="inline-flex items-center text-sm text-muted hover:text-text mb-4 transition-colors">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back to Actions
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{action.title}</h1>
            <div className="flex items-center gap-4 mt-3">
              <StatusBadge status={action.status} />
              <span className="font-mono text-sm text-muted bg-surface px-2 py-1 rounded border border-border">
                {action.id}
              </span>
            </div>
          </div>
          <button className="flex items-center gap-2 bg-accent hover:bg-accent/90 text-white px-4 py-2 rounded-md font-medium transition-colors">
            <PlayCircle className="w-5 h-5" />
            Simulate Execution
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <section className="bg-surface border border-border rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Description</h2>
            <div className="text-text/90 whitespace-pre-wrap leading-relaxed">
              {action.description || "No description provided."}
            </div>
          </section>

          <section className="bg-surface border border-border rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Context & Source</h2>
            {action.source_document_id ? (
              <div className="flex items-center gap-3 p-3 bg-background border border-border rounded-md">
                <FileText className="w-5 h-5 text-info" />
                <div>
                  <div className="text-sm font-medium">Derived from Document</div>
                  <Link href={`/documents/${action.source_document_id}`} className="text-xs text-muted hover:text-accent font-mono transition-colors">
                    {action.source_document_id}
                  </Link>
                </div>
              </div>
            ) : (
              <div className="text-muted text-sm italic">No specific source document linked. Synthesized from global context.</div>
            )}
          </section>

          <section className="bg-surface border border-border rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Dependencies</h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-muted mb-2 uppercase tracking-wider">Depends On</h3>
                {dependencies.length > 0 ? (
                  <ul className="space-y-2">
                    {dependencies.map(dep => (
                      <li key={dep.id} className="text-sm bg-background border border-border p-2 rounded flex items-center justify-between">
                        <Link href={`/actions/${dep.source_id}`} className="font-mono text-accent hover:underline">{dep.source_id}</Link>
                        <span className="text-muted text-xs">Requirement</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-sm text-text/50">No upstream dependencies.</div>
                )}
              </div>
              <div>
                <h3 className="text-sm font-medium text-muted mb-2 uppercase tracking-wider">Blocks</h3>
                {blocks.length > 0 ? (
                  <ul className="space-y-2">
                    {blocks.map(block => (
                      <li key={block.id} className="text-sm bg-background border border-border p-2 rounded flex items-center justify-between">
                        <Link href={`/actions/${block.target_id}`} className="font-mono text-accent hover:underline">{block.target_id}</Link>
                        <span className="text-muted text-xs">Downstream</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-sm text-text/50">No downstream blockers.</div>
                )}
              </div>
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <section className="bg-surface border border-border rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Metadata</h2>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted">Priority</dt>
                <dd className="font-mono">{action.priority}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">Confidence</dt>
                <dd>{action.confidence}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">Due Date</dt>
                <dd className="flex items-center gap-1">
                  <Clock className="w-3 h-3 text-muted" />
                  {action.due_date ? new Date(action.due_date).toLocaleDateString() : 'None'}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">Hard Deadline</dt>
                <dd>{action.is_hard_deadline ? 'Yes' : 'No'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">Created</dt>
                <dd>{new Date(action.created_at).toLocaleDateString()}</dd>
              </div>
            </dl>
          </section>
        </div>
      </div>
    </div>
  );
}
