import { CheckCircle2, Link2 as GithubIcon, Calendar as CalendarIcon, Server, Shield } from "lucide-react";

export default function ConnectionsPage() {
  // In a real application, we would fetch connector status from the API.
  // For NEXUS Phase 02, the connectors are statically loaded in the registry.
  // We represent their deterministic properties here.

  return (
    <div className="space-y-6 max-w-7xl mx-auto h-full">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Connections</h1>
          <p className="text-muted mt-1">External systems authorized for NEXUS execution.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
          name="System Simulation" 
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
  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden flex flex-col">
      <div className="p-6 border-b border-border flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-background rounded-lg border border-border">
            <Icon className="w-8 h-8 text-text" />
          </div>
          <div>
            <h2 className="text-xl font-bold">{name}</h2>
            <div className="font-mono text-xs text-muted mt-1">{id}</div>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-success/10 text-success border border-success/20 px-3 py-1 rounded-full text-xs font-medium">
          <CheckCircle2 className="w-3 h-3" /> {status}
        </div>
      </div>
      <div className="p-6 bg-background/50 flex-1">
        <h3 className="text-sm font-semibold text-muted uppercase tracking-wider mb-4 flex items-center gap-2">
          <Shield className="w-4 h-4" /> Capabilities
        </h3>
        <ul className="space-y-2">
          {capabilities.map((cap: string) => (
            <li key={cap} className="font-mono text-xs bg-surface border border-border px-2 py-1.5 rounded text-text">
              {cap}
            </li>
          ))}
        </ul>
      </div>
      <div className="px-6 py-4 border-t border-border bg-surface text-right">
        <button className="text-sm font-medium text-danger hover:text-danger/80 transition-colors">
          Disconnect
        </button>
      </div>
    </div>
  );
}
