import { ActionStatus, ExecutionState } from "@/api";
import { clsx } from "clsx";

export function StatusBadge({ status, type = "action" }: { status: ActionStatus | ExecutionState | string, type?: "action" | "execution" }) {
  let colorClass = "bg-surface border-border text-muted";
  let dotClass = "bg-muted";

  if (type === "action") {
    switch (status as ActionStatus) {
      case ActionStatus.VERIFIED:
      case ActionStatus.COMPLETED:
        colorClass = "bg-success/10 text-success border-success/20";
        dotClass = "bg-success";
        break;
      case ActionStatus.NOT_VERIFIED:
      case ActionStatus.FAILED:
        colorClass = "bg-danger/10 text-danger border-danger/20";
        dotClass = "bg-danger";
        break;
      case ActionStatus.REQUIRES_REVIEW:
      case ActionStatus.PENDING_VERIFICATION:
        colorClass = "bg-warning/10 text-warning border-warning/20";
        dotClass = "bg-warning";
        break;
      case ActionStatus.IN_PROGRESS:
        colorClass = "bg-info/10 text-info border-info/20";
        dotClass = "bg-info";
        break;
      case ActionStatus.READY:
        colorClass = "bg-accent/10 text-accent border-accent/20";
        dotClass = "bg-accent";
        break;
      case ActionStatus.BLOCKED:
        colorClass = "bg-surface border-border/60 text-muted/80";
        dotClass = "bg-muted/50";
        break;
      case ActionStatus.CANDIDATE:
        colorClass = "bg-surface text-text border-border";
        dotClass = "bg-text";
        break;
    }
  } else if (type === "execution") {
    switch (status as ExecutionState) {
      case ExecutionState.SUCCEEDED:
        colorClass = "bg-success/10 text-success border-success/20";
        dotClass = "bg-success";
        break;
      case ExecutionState.FAILED:
      case ExecutionState.DENIED:
      case ExecutionState.REJECTED:
        colorClass = "bg-danger/10 text-danger border-danger/20";
        dotClass = "bg-danger";
        break;
      case ExecutionState.AWAITING_APPROVAL:
        colorClass = "bg-warning/10 text-warning border-warning/20";
        dotClass = "bg-warning";
        break;
      case ExecutionState.RUNNING:
        colorClass = "bg-info/10 text-info border-info/20";
        dotClass = "bg-info";
        break;
      case ExecutionState.AUTHORIZED:
        colorClass = "bg-accent/10 text-accent border-accent/20";
        dotClass = "bg-accent";
        break;
    }
  }

  return (
    <span className={clsx("inline-flex items-center gap-1.5 px-2 py-0.5 rounded border text-[11px] font-medium font-mono uppercase tracking-wider", colorClass)}>
      <span className={clsx("w-1.5 h-1.5 rounded-full shadow-sm", dotClass)}></span>
      {status.replace(/_/g, " ")}
    </span>
  );
}
