"use client";
import { useEffect, useState, use } from "react";
import { executionsApi, ExecutionRequest, ExecutionState } from "@/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import Link from "next/link";
import { ArrowLeft, Shield, Check, X, ShieldAlert, Code, CheckSquare, Zap } from "lucide-react";

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
    return (
      <div className="flex flex-col h-[60vh] items-center justify-center text-muted gap-4">
        <div className="w-5 h-5 rounded-full border-2 border-muted/30 border-t-info animate-spin"></div>
        <div className="text-[13px] font-medium">Loading execution details...</div>
      </div>
    );
  }

  if (error || !execution) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="text-danger bg-danger-bg/10 px-4 py-2 rounded-md border border-danger/20 text-[13px] font-medium">
          {error || "Execution not found"}
        </div>
      </div>
    );
  }

  const needsApproval = execution.state === ExecutionState.AWAITING_APPROVAL;

  return (
    <div className="space-y-6 mx-auto pb-12">
      <div>
        <Link href="/execution" className="inline-flex items-center text-[12px] font-medium text-muted hover:text-text mb-6 transition-colors">
          <ArrowLeft className="w-3.5 h-3.5 mr-1.5" /> Back to Execution Center
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight font-mono text-text break-all flex items-center gap-3">
              <Zap className="w-5 h-5 text-info" />
              {execution.id}
            </h1>
            <div className="flex items-center gap-3 mt-3">
              <StatusBadge status={execution.state} type="execution" />
              <div className="h-4 w-px bg-border"></div>
              <Link href={`/actions/${execution.action_id}`} className="font-mono text-[11px] text-muted hover:text-text bg-surface/50 hover:bg-surface-hover px-2 py-0.5 rounded border border-border/60 flex items-center gap-1.5 transition-colors">
                <CheckSquare className="w-3 h-3 text-muted/70" />
                Action: {execution.action_id.split('-')[0]}...
              </Link>
            </div>
          </div>
        </div>
      </div>

      {needsApproval && (
        <div className="bg-warning-bg/40 border border-warning/30 rounded-xl p-6 flex flex-col md:flex-row items-center justify-between gap-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="bg-warning/20 p-2 rounded-full border border-warning/30 shrink-0">
              <ShieldAlert className="w-5 h-5 text-warning" />
            </div>
            <div>
              <h3 className="text-[14px] font-semibold text-warning">Approval Required</h3>
              <p className="text-text/80 text-[13px] mt-1 max-w-2xl leading-relaxed">
                This execution attempts to mutate an external system via the <span className="font-mono bg-warning/10 text-warning px-1 rounded">{execution.connector_name}</span> connector.
                Review the parameters before approving.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <button 
              onClick={handleReject} 
              disabled={approving}
              className="flex items-center gap-2 bg-surface hover:bg-surface-hover text-text px-4 py-2 rounded-md text-[13px] font-medium transition-colors border border-border/60 disabled:opacity-50"
            >
              <X className="w-4 h-4" /> Reject
            </button>
            <button 
              onClick={handleApprove} 
              disabled={approving}
              className="flex items-center gap-2 bg-success hover:bg-success/90 text-background px-4 py-2 rounded-md text-[13px] font-medium transition-colors disabled:opacity-50 shadow-sm"
            >
              <Check className="w-4 h-4" /> Approve & Execute
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-4">
        <div className="lg:col-span-2 space-y-6">
          <section className="bg-surface/30 border border-border/60 rounded-xl overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-border/40 bg-surface/50 flex items-center gap-2">
              <Code className="w-4 h-4 text-muted" />
              <h2 className="text-[13px] font-semibold uppercase tracking-wide text-text">Execution Parameters</h2>
            </div>
            <div className="p-0">
              <pre className="p-6 text-[12px] font-mono text-text/90 overflow-x-auto bg-[#0a0a0c]">
                {JSON.stringify(execution.parameters, null, 2)}
              </pre>
            </div>
          </section>

          {(execution.result_payload || execution.error_message) && (
            <section className="bg-surface/30 border border-border/60 rounded-xl overflow-hidden shadow-sm">
              <div className="px-6 py-4 border-b border-border/40 bg-surface/50 flex items-center gap-2">
                <Shield className="w-4 h-4 text-muted" />
                <h2 className="text-[13px] font-semibold uppercase tracking-wide text-text">Result Payload</h2>
              </div>
              <div className="p-0">
                {execution.error_message ? (
                  <div className="p-6 text-[13px] font-mono text-danger bg-[#0a0a0c] border-l-2 border-danger">
                    {execution.error_message}
                  </div>
                ) : (
                  <pre className="p-6 text-[12px] font-mono text-text/90 overflow-x-auto bg-[#0a0a0c]">
                    {JSON.stringify(execution.result_payload, null, 2)}
                  </pre>
                )}
              </div>
            </section>
          )}
        </div>

        <div className="space-y-6">
          <section className="bg-surface/30 border border-border/60 rounded-xl overflow-hidden shadow-sm sticky top-24">
            <div className="px-5 py-4 border-b border-border/40 bg-surface/50">
              <h2 className="text-[13px] font-semibold tracking-wide uppercase text-text">Target System</h2>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <dt className="text-[11px] font-semibold uppercase tracking-wider text-muted mb-2">Connector</dt>
                <dd className="font-mono text-[12px] bg-background border border-border/60 px-3 py-2 rounded-md text-text">{execution.connector_name}</dd>
              </div>
              <div>
                <dt className="text-[11px] font-semibold uppercase tracking-wider text-muted mb-2">Tool</dt>
                <dd className="font-mono text-[12px] bg-background border border-border/60 px-3 py-2 rounded-md text-info">{execution.tool_name}</dd>
              </div>
            </div>
            
            <div className="px-5 py-4 border-t border-b border-border/40 bg-surface/50">
              <h2 className="text-[13px] font-semibold tracking-wide uppercase text-text">Timeline</h2>
            </div>
            <div className="p-5">
              <dl className="space-y-4 text-[13px]">
                <div className="flex justify-between items-center pb-3 border-b border-border/40">
                  <dt className="text-muted">Created</dt>
                  <dd className="text-text font-mono text-[11px]">{new Date(execution.created_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })}</dd>
                </div>
                <div className="flex justify-between items-center">
                  <dt className="text-muted">Updated</dt>
                  <dd className="text-text font-mono text-[11px]">{new Date(execution.updated_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })}</dd>
                </div>
              </dl>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
