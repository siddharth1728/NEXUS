'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Activity, CheckSquare, FileText, LayoutDashboard, Link2, Settings, Terminal } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Actions', href: '/actions', icon: CheckSquare },
  { name: 'Documents', href: '/documents', icon: FileText },
  { name: 'Execution', href: '/execution', icon: Terminal },
  { name: 'Connections', href: '/connections', icon: Link2 },
  { name: 'Settings', href: '/settings', icon: Settings },
];

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex w-[260px] flex-col bg-surface border-r border-border min-h-screen">
      <div className="flex h-14 shrink-0 items-center px-5">
        <div className="flex items-center gap-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-accent/20 border border-accent/30">
            <Activity className="w-4 h-4 text-accent" />
          </div>
          <span className="font-mono text-[13px] tracking-widest font-semibold text-text">
            NEXUS
          </span>
        </div>
      </div>
      
      <div className="flex flex-1 flex-col overflow-y-auto pt-4 px-3 pb-4">
        <div className="mb-2 px-2 text-[10px] font-mono text-muted uppercase tracking-widest font-semibold">
          Platform
        </div>
        <nav className="flex-1 space-y-0.5">
          {navigation.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  isActive
                    ? 'bg-surface-hover text-text'
                    : 'text-muted hover:bg-surface-hover/50 hover:text-text',
                  'group flex items-center rounded-md px-3 py-2 text-[13px] font-medium transition-all duration-200'
                )}
              >
                <item.icon
                  className={cn(
                    isActive ? 'text-text' : 'text-muted group-hover:text-text',
                    'mr-3 h-[18px] w-[18px] shrink-0 transition-colors'
                  )}
                  aria-hidden="true"
                  strokeWidth={2}
                />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
      
      <div className="p-4 border-t border-border/50">
        <div className="flex items-center gap-3 px-2 py-1.5 rounded-md hover:bg-surface-hover/50 transition-colors cursor-pointer">
          <div className="h-6 w-6 rounded-full bg-border flex items-center justify-center text-[10px] font-mono text-muted">
            DT
          </div>
          <div className="flex flex-col">
            <span className="text-[12px] font-medium text-text leading-tight">dev-tenant</span>
            <span className="text-[10px] text-muted leading-tight">Admin</span>
          </div>
        </div>
      </div>
    </div>
  );
}
