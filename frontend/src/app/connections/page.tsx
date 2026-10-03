import { CheckCircle2, Link2 as GithubIcon, Calendar as CalendarIcon, Server, Shield, Link2, MoreVertical } from "lucide-react";

export default function ConnectionsPage() {
  // In a real application, we would fetch connector status from the API.
  // For NEXUS Phase 02, the connectors are statically loaded in the registry.
  // We represent their deterministic properties here.

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-text">Integrations & Connectors</h1>
        <p className="text-[13px] text-muted mt-1.5 font-medium">External systems authorized for NEXUS execution.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <ConnectorCard 
          name="GitHub" 
          id="github" 
          icon={GithubIcon} 
          status="Connected"
          capabilities={["GITHUB_REPOSITORY_READ", "GITHUB_ISSUE_READ", "GITHUB_ISSUE_CREATE", "GITHUB_ISSUE_COMMENT_CREATE"]}
        />
        
        <ConnectorCard 
          name="Google Calendar" 
          id="google_calendar" 
          icon={CalendarIcon} 
          status="Connected"
          capabilities={["CALENDAR_READ", "CALENDAR_CREATE"]}
        />

        <ConnectorCard 
          name="System Simulator" 
          id="system_simulator" 
          icon={Server} 
          status="Built-in"
          capabilities={["SYSTEM_SIMULATE"]}
        />
      </div>
    </div>
  );
}

function ConnectorCard({ name, id, icon: Icon, status, capabilities }: any) {
  const isBuiltIn = status === "Built-in";
  return (
    <div className="bg-surface/30 border border-border/60 rounded-xl overflow-hidden flex flex-col shadow-sm group hover:border-border transition-colors">
      <div className="p-5 border-b border-border/40 flex items-start justify-between bg-surface/50">
        <div className="flex items-center gap-4">
          <div className="p-2.5 bg-background rounded-lg border border-border/60 shadow-sm group-hover:border-border transition-colors">
            <Icon className="w-5 h-5 text-text" />
          </div>
          <div>
            <h2 className="text-[15px] font-semibold text-text">{name}</h2>
            <div className="font-mono text-[10px] text-muted mt-0.5">{id}</div>
          </div>
        </div>
        <button className="text-muted hover:text-text transition-colors">
          <MoreVertical className="w-4 h-4" />
        </button>
      </div>
      <div className="p-5 bg-[#0a0a0c]/50 flex-1">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[11px] font-semibold text-muted uppercase tracking-wider flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5" /> Capabilities
          </h3>
          <div className={`flex items-center gap-1.5 ${isBuiltIn ? 'bg-info/10 text-info border-info/20' : 'bg-success/10 text-success border-success/20'} border px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wide`}>
            <CheckCircle2 className="w-3 h-3" /> {status}
          </div>
        </div>
        <ul className="space-y-2">
          {capabilities.map((cap: string) => (
            <li key={cap} className="font-mono text-[10px] bg-background border border-border/60 px-2 py-1.5 rounded-md text-text flex items-center gap-2">
              <Link2 className="w-3 h-3 text-muted/50" /> {cap}
            </li>
          ))}
        </ul>
      </div>
      <div className="px-5 py-3 border-t border-border/40 bg-surface/50 text-right">
        {!isBuiltIn ? (
          <button className="text-[12px] font-medium text-danger hover:text-danger/80 transition-colors">
            Disconnect
          </button>
        ) : (
          <span className="text-[12px] font-medium text-muted/50">
            System Required
          </span>
        )}
      </div>
    </div>
  );
}
