import { Sidebar } from './Sidebar';
import { Search } from 'lucide-react';

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden relative">
        {/* Subtle top gradient for depth */}
        <div className="absolute top-0 inset-x-0 h-32 bg-gradient-to-b from-surface/30 to-transparent pointer-events-none" />
        
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-border/40 bg-background/80 backdrop-blur-md px-8 z-10">
          <div className="flex items-center">
            {/* Breadcrumb area placeholder */}
            <div className="text-[13px] font-medium text-muted">
              NEXUS <span className="mx-2 text-border">/</span> <span className="text-text">Workspace</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button className="flex items-center gap-2 text-[13px] text-muted bg-surface/50 border border-border/50 rounded-md px-3 py-1.5 hover:bg-surface hover:text-text transition-colors">
              <Search className="w-3.5 h-3.5" />
              <span>Search</span>
              <kbd className="font-mono bg-surface-hover border border-border/50 px-1.5 py-0.5 rounded text-[10px] ml-2">⌘K</kbd>
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-8 z-0">
          <div className="mx-auto max-w-6xl w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
