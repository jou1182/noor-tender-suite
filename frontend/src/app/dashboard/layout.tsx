'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  FolderKanban, BookMarked, Lightbulb, Settings, LayoutDashboard, Building2, Zap,
} from 'lucide-react';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Projects', icon: FolderKanban },
  { href: '/dashboard/sbc-knowledge-base', label: 'SBC Knowledge Base', icon: BookMarked },
  { href: '/dashboard/ve-library', label: 'VE Library', icon: Lightbulb },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-(--surface-page) text-slate-100 flex">
      {/* Enterprise Sidebar */}
      <aside className="w-64 shrink-0 bg-slate-950 border-r border-slate-800 flex flex-col sticky top-0 h-screen">
        <div className="flex items-center gap-2.5 px-5 py-5 border-b border-slate-800">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-teal-500 to-blue-600 flex items-center justify-center shrink-0">
            <Building2 className="h-5 w-5 text-white" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-black tracking-tight text-white leading-tight">ConTech AI</p>
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Enterprise Workspace</p>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition ${
                  active
                    ? 'bg-gradient-to-r from-teal-500/20 to-blue-600/20 text-teal-300 border border-teal-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60 border border-transparent'
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="px-4 py-4 border-t border-slate-800">
          <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-slate-600">
            <Zap className="h-3 w-3 text-teal-500" />
            Live Agent Pipeline
          </div>
          <p className="text-[10px] text-slate-600 mt-1 leading-relaxed">
            LangGraph swarm · PostgreSQL 16 · pgvector · Qdrant
          </p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 min-w-0 flex flex-col">
        <div className="flex items-center gap-2 px-6 py-3 border-b border-slate-800 bg-slate-900/50 sticky top-0 z-10 backdrop-blur">
          <LayoutDashboard className="h-4 w-4 text-teal-400" />
          <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Enterprise Project Workspace</span>
        </div>
        <div className="flex-1 px-6 py-6">{children}</div>
      </main>
    </div>
  );
}
