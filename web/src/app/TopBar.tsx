import { Bell, ChevronDown, LogOut, Moon, Sun, User } from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useTheme } from '@/hooks/useTheme';
import { useAuth } from '@/app/AuthContext';
import { useLatestCycle } from '@/hooks/useData';
import { StatusRing } from '@/components/ui/StatusRing';
interface TopBarProps {
  sseColor: string;
  sseLabel: string;
}

export function TopBar({ sseColor, sseLabel }: TopBarProps) {
  const { theme, toggleTheme } = useTheme();
  const { user, logout, isOwner } = useAuth();
  const { data: latestCycle } = useLatestCycle();

  const cycleStatus = latestCycle?.status ?? 'IDLE';
  const isRunning = cycleStatus === 'RUNNING';

  return (
    <header className="h-16 shrink-0 border-b border-[var(--border)] bg-[var(--surface)] px-4 flex items-center justify-between gap-4">
      {/* Left: cycle pill */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)]">
          <StatusRing
            active={isRunning}
            size="sm"
            ariaLabel={`Cycle: ${cycleStatus}`}
          />
          <span className="font-mono text-sm text-[var(--muted)]">{cycleStatus}</span>
        </div>

        {/* SSE connection pill */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)]">
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: sseColor }}
            aria-hidden="true"
          />
          <span className="font-mono text-xs text-[var(--muted)]">{sseLabel}</span>
        </div>
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-2">
        {/* Alerts bell */}
        <button
          className="relative w-10 h-10 rounded-[10px] flex items-center justify-center text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--arc)]"
          aria-label="Alerts"
        >
          <Bell className="w-5 h-5" aria-hidden="true" />
          <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[var(--arc)]" aria-hidden="true" />
        </button>

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="w-10 h-10 rounded-[10px] flex items-center justify-center text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--arc)]"
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? (
            <Moon className="w-5 h-5" aria-hidden="true" />
          ) : (
            <Sun className="w-5 h-5" aria-hidden="true" />
          )}
        </button>

        {/* Profile / user menu */}
        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <button
              className="flex items-center gap-2 px-3 py-1.5 rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)] hover:bg-[var(--surface)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--arc)]"
              aria-label="User menu"
            >
              <User className="w-4 h-4 text-[var(--muted)]" aria-hidden="true" />
              <span className="text-sm font-medium hidden sm:block">
                {user?.username ?? 'Guest'}
              </span>
              {isOwner && (
                <span className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-[var(--arc)] text-[var(--bg)]">
                  OWNER
                </span>
              )}
              <ChevronDown className="w-3 h-3 text-[var(--muted)]" aria-hidden="true" />
            </button>
          </DropdownMenu.Trigger>

          <DropdownMenu.Portal>
            <DropdownMenu.Content
              align="end"
              sideOffset={8}
              className="min-w-[200px] rounded-[12px] bg-[var(--surface)] border border-[var(--border)] shadow-xl p-1 z-50"
            >
              <div className="px-3 py-2 border-b border-[var(--border)]">
                <p className="text-sm font-medium">{user?.username}</p>
                <p className="text-xs text-[var(--muted)]">{user?.role}</p>
              </div>
              <DropdownMenu.Item
                onClick={logout}
                className="flex items-center gap-2 px-3 py-2 rounded-[8px] text-sm text-[var(--sell)] cursor-pointer hover:bg-[var(--surface-2)] focus:bg-[var(--surface-2)] focus:outline-none"
              >
                <LogOut className="w-4 h-4" aria-hidden="true" />
                Sign out
              </DropdownMenu.Item>
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </div>
    </header>
  );
}
