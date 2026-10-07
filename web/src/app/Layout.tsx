import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  Newspaper,
  Bot,
  History,
  BarChart3,
  Settings,
  Zap,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import * as Tooltip from '@radix-ui/react-tooltip';
import { useAuth } from './AuthContext';
import { useSSE } from '@/hooks/useSSE';
import { TopBar } from './TopBar';

const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Overview', end: true },
  { to: '/signals', icon: TrendingUp, label: 'Signals' },
  { to: '/news', icon: Newspaper, label: 'News & Macro' },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/history', icon: History, label: 'History' },
  { to: '/stats', icon: BarChart3, label: 'Stats' },
];

const OWNER_ITEMS = [
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export function Layout() {
  const [collapsed, setCollapsed] = React.useState(false);
  const { isOwner } = useAuth();
  const { state: sseState } = useSSE();

  const sseLabel = sseState === 'live' ? 'Live' : sseState === 'reconnecting' ? 'Reconnecting' : 'Offline';
  const sseColor = sseState === 'live' ? 'var(--buy)' : sseState === 'reconnecting' ? 'var(--warn)' : 'var(--sell)';

  return (
    <Tooltip.Provider delayDuration={300}>
      <div className="flex h-screen overflow-hidden bg-[var(--bg)]">
        {/* Skip to main */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-20 focus:z-50 focus:px-4 focus:py-2 focus:rounded-lg focus:text-sm focus:bg-[var(--arc)] focus:text-[var(--bg)]"
        >
          Skip to main content
        </a>

        {/* Desktop/Tablet Nav Rail */}
        <nav
          className="hidden md:flex flex-col border-r border-[var(--border)] bg-[var(--surface)] transition-all duration-200"
          style={{ width: collapsed ? 72 : 232 }}
          aria-label="Main navigation"
        >
          {/* Logo */}
          <div className={`flex items-center h-16 border-b border-[var(--border)] ${collapsed ? 'justify-center px-2' : 'px-4'} gap-3`}>
            <div className="w-8 h-8 rounded-[10px] bg-gradient-to-br from-[var(--arc)] to-[var(--buy)] flex items-center justify-center shrink-0">
              <Zap className="w-5 h-5 text-white" aria-hidden="true" />
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <span className="font-heading font-semibold text-lg tracking-tight">JARVIS</span>
                <p className="text-[10px] text-[var(--muted)] truncate">Signal Intelligence</p>
              </div>
            )}
          </div>

          {/* Nav items */}
          <div className="flex-1 overflow-y-auto py-3 px-2 space-y-1">
            {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
              <Tooltip.Root key={to} disableHoverableContent>
                <Tooltip.Trigger asChild>
                  <NavLink
                    to={to}
                    end={end}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-[10px] text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--arc)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--surface)] ${
                        isActive
                          ? 'bg-[var(--surface-2)] text-[var(--arc)] border-l-2 border-[var(--arc)]'
                          : 'text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)]'
                      } ${collapsed ? 'justify-center' : ''}`
                    }
                  >
                    <Icon className="w-5 h-5 shrink-0" aria-hidden="true" />
                    {!collapsed && <span className="truncate">{label}</span>}
                  </NavLink>
                </Tooltip.Trigger>
                {collapsed && (
                  <Tooltip.Portal>
                    <Tooltip.Content side="right" sideOffset={8} className="px-2 py-1 rounded-[6px] text-xs bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text)] shadow-lg z-50">
                      {label}
                      <Tooltip.Arrow className="fill-[var(--border)]" />
                    </Tooltip.Content>
                  </Tooltip.Portal>
                )}
              </Tooltip.Root>
            ))}

            {/* OWNER-only items */}
            {isOwner && (
              <>
                <div className={`my-2 mx-2 border-t border-[var(--border)] ${collapsed ? 'mx-1' : ''}`} />
                {OWNER_ITEMS.map(({ to, icon: Icon, label }) => (
                  <Tooltip.Root key={to} disableHoverableContent>
                    <Tooltip.Trigger asChild>
                      <NavLink
                        to={to}
                        className={({ isActive }) =>
                          `flex items-center gap-3 px-3 py-2.5 rounded-[10px] text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--arc)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--surface)] ${
                            isActive
                              ? 'bg-[var(--surface-2)] text-[var(--arc)]'
                              : 'text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)]'
                          } ${collapsed ? 'justify-center' : ''}`
                        }
                      >
                        <Icon className="w-5 h-5 shrink-0" aria-hidden="true" />
                        {!collapsed && <span className="truncate">{label}</span>}
                      </NavLink>
                    </Tooltip.Trigger>
                    {collapsed && (
                      <Tooltip.Portal>
                        <Tooltip.Content side="right" sideOffset={8} className="px-2 py-1 rounded-[6px] text-xs bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text)] shadow-lg z-50">
                          {label}
                          <Tooltip.Arrow className="fill-[var(--border)]" />
                        </Tooltip.Content>
                      </Tooltip.Portal>
                    )}
                  </Tooltip.Root>
                ))}
              </>
            )}
          </div>

          {/* Bottom */}
          <div className="border-t border-[var(--border)] p-3 space-y-2">
            {!collapsed && (
              <div className="flex items-center gap-2 px-2 py-1 rounded-[6px] bg-[var(--surface-2)]">
                <span className="text-[10px] font-mono font-medium text-[var(--muted)] bg-[var(--border)] px-1.5 py-0.5 rounded">PAPER</span>
                <span className="text-[10px] text-[var(--muted)]">v0.1.0</span>
              </div>
            )}
            {!collapsed && (
              <p className="text-[10px] text-[var(--muted)] px-1 text-center">Signals only — no execution</p>
            )}
            <button
              onClick={() => setCollapsed((c) => !c)}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-[10px] text-sm text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--arc)]"
              aria-label={collapsed ? 'Expand navigation' : 'Collapse navigation'}
            >
              {collapsed ? <ChevronRight className="w-4 h-4" /> : <><ChevronLeft className="w-4 h-4" /><span className="text-xs">Collapse</span></>}
            </button>
          </div>
        </nav>

        {/* Main content */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <TopBar sseColor={sseColor} sseLabel={sseLabel} />
          <main id="main-content" className="flex-1 overflow-y-auto" tabIndex={-1}>
            <Outlet />
          </main>
          <footer className="border-t border-[var(--border)] py-3 px-6 shrink-0">
            <p className="text-[11px] text-[var(--muted)] text-center">Signals are informational, not financial advice.</p>
          </footer>
        </div>

        {/* Mobile Bottom Nav */}
        <nav
          className="md:hidden fixed bottom-0 left-0 right-0 z-40 border-t border-[var(--border)] bg-[var(--surface)] safe-bottom"
          aria-label="Mobile navigation"
        >
          <div className="flex items-center justify-around py-2">
            {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end
                className={({ isActive }) =>
                  `flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-lg text-[10px] transition-colors focus-visible:outline-none ${isActive ? 'text-[var(--arc)]' : 'text-[var(--muted)]'}`
                }
              >
                <Icon className="w-5 h-5" aria-hidden="true" />
                <span className="font-medium">{label}</span>
              </NavLink>
            ))}
          </div>
        </nav>
      </div>
    </Tooltip.Provider>
  );
}
