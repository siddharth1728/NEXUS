import { Activity, AlertTriangle, CheckCircle2, Clock, Terminal, ChevronRight } from "lucide-react";

export default function Dashboard() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-text">Dashboard</h1>
        <p className="text-[13px] text-muted mt-1.5 font-medium">System overview and autonomous execution status.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard title="Requires Review" value="0" icon={AlertTriangle} variant="warning" />
        <MetricCard title="Active Actions" value="0" icon={Activity} variant="info" />
        <MetricCard title="Awaiting Execution" value="0" icon={Clock} variant="neutral" />
        <MetricCard title="Verified Today" value="0" icon={CheckCircle2} variant="success" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="flex flex-col border border-border/60 rounded-xl bg-surface/30 overflow-hidden">
          <div className="flex items-center justify-between border-b border-border/40 px-5 py-4 bg-surface/50">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-warning" />
              <h2 className="text-[13px] font-semibold tracking-wide uppercase text-text">Attention Required</h2>
            </div>
            <button className="text-[11px] font-medium text-muted hover:text-text flex items-center gap-1 transition-colors">
              View All <ChevronRight className="w-3 h-3" />
            </button>
          </div>
          <div className="flex-1 p-8 flex flex-col items-center justify-center text-center">
            <div className="w-12 h-12 rounded-full bg-surface border border-border flex items-center justify-center mb-3">
              <CheckCircle2 className="w-5 h-5 text-muted/50" />
            </div>
            <div className="text-[14px] font-medium text-text">All Clear</div>
            <div className="text-[12px] text-muted mt-1">No items require immediate attention or manual approval.</div>
          </div>
        </div>
        
        <div className="flex flex-col border border-border/60 rounded-xl bg-surface/30 overflow-hidden">
          <div className="flex items-center justify-between border-b border-border/40 px-5 py-4 bg-surface/50">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-info" />
              <h2 className="text-[13px] font-semibold tracking-wide uppercase text-text">Recent Executions</h2>
            </div>
            <button className="text-[11px] font-medium text-muted hover:text-text flex items-center gap-1 transition-colors">
              View Logs <ChevronRight className="w-3 h-3" />
            </button>
          </div>
          <div className="flex-1 p-8 flex flex-col items-center justify-center text-center">
            <div className="text-[12px] text-muted font-mono bg-surface border border-border px-3 py-1.5 rounded-md">
              No recent execution logs found.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon: Icon, variant }: { title: string, value: string, icon: any, variant: 'warning' | 'info' | 'success' | 'neutral' }) {
  const styles = {
    warning: { text: "text-warning", bg: "bg-warning-bg", border: "border-warning/20" },
    info: { text: "text-info", bg: "bg-info-bg", border: "border-info/20" },
    success: { text: "text-success", bg: "bg-success-bg", border: "border-success/20" },
    neutral: { text: "text-text", bg: "bg-surface-hover", border: "border-border" }
  };
  
  const currentStyle = styles[variant];

  return (
    <div className="relative overflow-hidden border border-border/60 rounded-xl bg-surface/40 p-5 flex flex-col justify-between group hover:bg-surface hover:border-border transition-all duration-200">
      <div className="flex justify-between items-start mb-4">
        <span className="text-muted font-medium text-[13px]">{title}</span>
        <div className={`p-1.5 rounded-md ${currentStyle.bg} ${currentStyle.border} border`}>
          <Icon className={`w-4 h-4 ${currentStyle.text}`} />
        </div>
      </div>
      <div className="flex items-baseline gap-2">
        <div className="text-3xl font-bold font-mono tracking-tight">{value}</div>
      </div>
    </div>
  );
}
