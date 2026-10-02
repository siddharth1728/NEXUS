import { ActionStatus, ExecutionState } from "@/api";
import { clsx } from "clsx";

export function StatusBadge({ status, type = "action" }: { status: ActionStatus | ExecutionState | string, type?: "action" | "execution" }) {
  let colorClass = "bg-border text-muted";

  if (type === "action") {
    switch (status as ActionStatus) {
      case ActionStatus.VERIFIED:
      case ActionStatus.COMPLETED:
        colorClass = "bg-success/20 text-success border-success/30";
        break;
      case ActionStatus.NOT_VERIFIED:
      case ActionStatus.FAILED:
        colorClass = "bg-danger/20 text-danger border-danger/30";
        break;
      case ActionStatus.REQUIRES_REVIEW:
      case ActionStatus.PENDING_VERIFICATION:
        colorClass = "bg-warning/20 text-warning border-warning/30";
        break;
      case ActionStatus.IN_PROGRESS:
        colorClass = "bg-info/20 text-info border-info/30";
        break;
      case ActionStatus.READY:
        colorClass = "bg-accent/20 text-accent border-accent/30";
        break;
      case ActionStatus.BLOCKED:
        colorClass = "bg-border/50 text-muted border-border";
        break;
      case ActionStatus.CANDIDATE:
        colorClass = "bg-surface text-text border-border";
        break;
    }
  } else if (type === "execution") {
    switch (status as ExecutionState) {
      case ExecutionState.SUCCEEDED:
        colorClass = "bg-success/20 text-success border-success/30";
        break;
      case ExecutionState.FAILED:
      case ExecutionState.DENIED:
      case ExecutionState.REJECTED:
        colorClass = "bg-danger/20 text-danger border-danger/30";
        break;
      case ExecutionState.AWAITING_APPROVAL:
        colorClass = "bg-warning/20 text-warning border-warning/30";
        break;
      case ExecutionState.RUNNING:
        colorClass = "bg-info/20 text-info border-info/30";
        break;
      case ExecutionState.AUTHORIZED:
        colorClass = "bg-accent/20 text-accent border-accent/30";
        break;
    }
  }

  return (
    <span className={clsx("inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border font-mono", colorClass)}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
