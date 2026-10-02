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
    <div className="flex w-64 flex-col bg-surface border-r border-border min-h-screen">
      <div className="flex h-16 shrink-0 items-center px-6 border-b border-border">
        <span className="font-mono font-bold tracking-tight text-lg flex items-center gap-2">
          <Activity className="w-5 h-5 text-accent" />
          NEXUS
        </span>
      </div>
      <div className="flex flex-1 flex-col overflow-y-auto pt-6 px-4 pb-4">
        <nav className="flex-1 space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  isActive
                    ? 'bg-border text-text'
                    : 'text-muted hover:bg-border/50 hover:text-text',
                  'group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors'
                )}
              >
                <item.icon
                  className={cn(
                    isActive ? 'text-accent' : 'text-muted group-hover:text-text',
                    'mr-3 h-5 w-5 shrink-0 transition-colors'
                  )}
                  aria-hidden="true"
                />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
