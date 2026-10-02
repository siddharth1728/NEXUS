import { Activity, AlertTriangle, CheckCircle, Clock } from "lucide-react";

export default function Dashboard() {
  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted mt-1">System overview and attention required.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricCard title="Requires Review" value="0" icon={AlertTriangle} color="warning" />
        <MetricCard title="Active Actions" value="0" icon={Activity} color="info" />
        <MetricCard title="Awaiting Execution" value="0" icon={Clock} color="text" />
        <MetricCard title="Verified Today" value="0" icon={CheckCircle} color="success" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="border border-border rounded-lg bg-surface p-6">
          <h2 className="font-semibold mb-4">Attention Required</h2>
          <div className="text-sm text-muted">No items require immediate attention.</div>
        </div>
        <div className="border border-border rounded-lg bg-surface p-6">
          <h2 className="font-semibold mb-4">Recent Executions</h2>
          <div className="text-sm text-muted">No recent executions.</div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon: Icon, color }: any) {
  const colorMap: any = {
    warning: "text-warning",
    info: "text-info",
    success: "text-success",
    text: "text-text"
  };
  return (
    <div className="border border-border rounded-lg bg-surface p-6 flex flex-col justify-between">
      <div className="flex justify-between items-center mb-4">
        <span className="text-muted font-medium text-sm">{title}</span>
        <Icon className={`w-5 h-5 ${colorMap[color]}`} />
      </div>
      <div className="text-3xl font-bold font-mono">{value}</div>
    </div>
  );
}
