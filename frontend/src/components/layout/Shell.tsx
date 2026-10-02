import { Sidebar } from './Sidebar';

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-full w-full">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-border bg-background px-8">
          <div className="font-mono text-sm text-muted">Workspace: <span className="text-text font-bold">dev-tenant</span></div>
          <div className="flex items-center gap-4 text-sm text-muted">
            Global Search <kbd className="font-mono bg-border px-1.5 py-0.5 rounded text-xs">⌘K</kbd>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-8 bg-background">
          {children}
        </main>
      </div>
    </div>
  );
}
