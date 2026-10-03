import { User, Shield, Key } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-6 max-w-4xl mx-auto h-full">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted mt-1">Manage workspace configuration and security.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        <div className="md:col-span-1 space-y-1">
          <button className="w-full text-left px-3 py-2 bg-surface border border-border text-text rounded-md font-medium text-sm">
            Profile
          </button>
          <button className="w-full text-left px-3 py-2 text-muted hover:text-text rounded-md font-medium text-sm transition-colors">
            Security
          </button>
          <button className="w-full text-left px-3 py-2 text-muted hover:text-text rounded-md font-medium text-sm transition-colors">
            API Keys
          </button>
        </div>

        <div className="md:col-span-3 space-y-6">
          <section className="bg-surface border border-border rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><User className="w-5 h-5 text-muted" /> Profile Settings</h2>
            <div className="space-y-4 max-w-md">
              <div>
                <label className="block text-sm font-medium text-muted mb-1">Display Name</label>
                <input type="text" defaultValue="NEXUS Admin" disabled className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm text-text opacity-50 cursor-not-allowed" />
              </div>
              <div>
                <label className="block text-sm font-medium text-muted mb-1">Email</label>
                <input type="email" defaultValue="admin@nexus.local" disabled className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm text-text opacity-50 cursor-not-allowed" />
              </div>
            </div>
          </section>

          <section className="bg-surface border border-border rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><Shield className="w-5 h-5 text-muted" /> Tenant Context</h2>
            <div className="space-y-4 max-w-md">
              <div>
                <label className="block text-sm font-medium text-muted mb-1">Active Tenant ID</label>
                <div className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono text-accent">
                  dev-tenant
                </div>
                <p className="text-xs text-muted mt-2">
                  All Actions, Documents, and Executions are isolated to this tenant ID as enforced by the backend authorization layer.
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
