"use client";
import { useEffect, useState, use } from "react";
import { executionsApi, ExecutionRequest, ExecutionState } from "@/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import Link from "next/link";
import { ArrowLeft, Shield, Check, X, ShieldAlert, Code } from "lucide-react";

export default function ExecutionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const [execution, setExecution] = useState<ExecutionRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);

  useEffect(() => {
    loadData();
  }, [resolvedParams.id]);

  async function loadData() {
    try {
      setLoading(true);
      const data = await executionsApi.getExecution(resolvedParams.id);
      setExecution(data);
    } catch (err: any) {
      setError(err.message || "Failed to load execution details");
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove() {
    try {
      setApproving(true);
      const data = await executionsApi.approveExecution(resolvedParams.id);
      setExecution(data);
    } catch (err: any) {
      alert("Failed to approve: " + err.message);
    } finally {
      setApproving(false);
    }
  }

  async function handleReject() {
    try {
      setApproving(true);
      const data = await executionsApi.rejectExecution(resolvedParams.id);
      setExecution(data);
    } catch (err: any) {
      alert("Failed to reject: " + err.message);
    } finally {
      setApproving(false);
    }
  }

  if (loading) {
    return <div className="flex h-full items-center justify-center text-muted">Loading execution details...</div>;
  }

  if (error || !execution) {
    return <div className="flex h-full items-center justify-center text-danger">{error || "Execution not found"}</div>;
  }

  const needsApproval = execution.state === ExecutionState.AWAITING_APPROVAL;

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      <div>
        <Link href="/execution" className="inline-flex items-center text-sm text-muted hover:text-text mb-4 transition-colors">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back to Executions
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight font-mono break-all">{execution.id}</h1>
            <div className="flex items-center gap-4 mt-3">
              <StatusBadge status={execution.state} type="execution" />
              <Link href={`/actions/${execution.action_id}`} className="font-mono text-sm text-accent hover:underline bg-surface px-2 py-1 rounded border border-border">
                Action: {execution.action_id.split('-')[0]}...
              </Link>
            </div>
          </div>
        </div>
      </div>

      {needsApproval && (
        <div className="bg-warning/10 border border-warning/30 rounded-lg p-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <ShieldAlert className="w-8 h-8 text-warning shrink-0" />
            <div>
              <h3 className="text-lg font-semibold text-warning">Approval Required</h3>
              <p className="text-text/80 text-sm mt-1">
                This execution attempts to mutate an external system via the <span className="font-mono">{execution.connector_name}</span> connector.
                Review the parameters before approving.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <button 
              onClick={handleReject} 
              disabled={approving}
              className="flex items-center gap-2 bg-surface hover:bg-border text-text px-4 py-2 rounded-md font-medium transition-colors border border-border disabled:opacity-50"
            >
              <X className="w-4 h-4" /> Reject
            </button>
            <button 
              onClick={handleApprove} 
              disabled={approving}
              className="flex items-center gap-2 bg-success hover:bg-success/90 text-background px-4 py-2 rounded-md font-medium transition-colors disabled:opacity-50"
            >
              <Check className="w-4 h-4" /> Approve & Execute
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <section className="bg-surface border border-border rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-border bg-background flex items-center gap-2">
              <Code className="w-4 h-4 text-muted" />
              <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">Execution Parameters</h2>
            </div>
            <div className="p-0">
              <pre className="p-6 text-sm font-mono text-text/90 overflow-x-auto bg-surface">
                {JSON.stringify(execution.parameters, null, 2)}
              </pre>
            </div>
          </section>

          {(execution.result_payload || execution.error_message) && (
            <section className="bg-surface border border-border rounded-lg overflow-hidden">
              <div className="px-6 py-4 border-b border-border bg-background flex items-center gap-2">
                <Shield className="w-4 h-4 text-muted" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">Result Payload</h2>
              </div>
              <div className="p-0">
                {execution.error_message ? (
                  <div className="p-6 text-sm font-mono text-danger bg-danger/5 border-l-4 border-danger">
                    {execution.error_message}
                  </div>
                ) : (
                  <pre className="p-6 text-sm font-mono text-text/90 overflow-x-auto bg-surface">
                    {JSON.stringify(execution.result_payload, null, 2)}
                  </pre>
                )}
              </div>
            </section>
          )}
        </div>

        <div className="space-y-6">
          <section className="bg-surface border border-border rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Target System</h2>
            <dl className="space-y-4 text-sm">
              <div>
                <dt className="text-muted mb-1">Connector</dt>
                <dd className="font-mono bg-background border border-border px-3 py-2 rounded">{execution.connector_name}</dd>
              </div>
              <div>
                <dt className="text-muted mb-1">Tool</dt>
                <dd className="font-mono bg-background border border-border px-3 py-2 rounded text-accent">{execution.tool_name}</dd>
              </div>
            </dl>
          </section>
          
          <section className="bg-surface border border-border rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Timeline</h2>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted">Created</dt>
                <dd>{new Date(execution.created_at).toLocaleString()}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">Updated</dt>
                <dd>{new Date(execution.updated_at).toLocaleString()}</dd>
              </div>
            </dl>
          </section>
        </div>
      </div>
    </div>
  );
}
