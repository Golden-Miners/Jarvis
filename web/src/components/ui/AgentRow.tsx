import { cn } from '../../lib/utils';
import { StatusRing } from './StatusRing';
import type { AgentStatus } from '../../types/api';

interface AgentRowProps {
  agent: AgentStatus;
  className?: string;
}

const agentIcons: Record<string, React.ReactNode> = {
  Vision: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  ),
  NickFury: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 01-2-2V7m2 13a2 2 0 01-2-2V7" />
    </svg>
  ),
  Quicksilver: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  ),
  DoctorStrange: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ),
  WarMachine: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a1 1 0 00-1-1h-4a1 1 0 00-1 1v4a1 1 0 01-1 1H7" />
    </svg>
  ),
  Hawkeye: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 3v18M12 3v18M9 3v18M21 12h-6" />
    </svg>
  ),
  BlackWidow: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 01-9 9c-2.5 0-4.8-.9-6.5-2.4" />
    </svg>
  ),
  Falcon: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17 18a5 5 0 00-10 0M15 11h-6m0 6h6M4 9l6-6 6 6" />
    </svg>
  ),
  AntMan: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <circle cx="12" cy="12" r="3" />
      <circle cx="12" cy="12" r="7" />
    </svg>
  ),
  Wasp: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
    </svg>
  ),
  IronMan: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
    </svg>
  ),
  CaptainAmerica: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <circle cx="12" cy="12" r="10" />
      <path d="M8 15v-6" />
      <path d="M16 15v-6" />
    </svg>
  ),
  Thor: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h3a1 1 0 011 1v5" />
    </svg>
  ),
  Hulk: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 5.636l-13.24 13.24m0 0L5.636 18.972 18.972 5.636M18.364 18.364l-13.24-13.24" />
    </svg>
  ),
  BlackPanther: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 2a10 10 0 1010 10A10 10 0 0012 2zm0 18a8 8 0 010-16 8 8 0 000 16z" />
    </svg>
  ),
  Jarvis: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ),
};

export function AgentRow({ agent, className }: AgentRowProps) {
  const statusColors = {
    OK: 'var(--buy)',
    DEGRADED: 'var(--warn)',
    ERROR: 'var(--sell)',
    SKIPPED: 'var(--neutral)',
  };

  const Icon = agentIcons[agent.agent] || (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <circle cx="12" cy="12" r="10" />
    </svg>
  );

  return (
    <div className={cn('flex items-center gap-3 p-3 rounded-[10px] bg-[var(--surface)] border border-[var(--border)]', className)}>
      <span className="w-8 h-8 flex items-center justify-center rounded-[8px] bg-[var(--surface-2)] text-[var(--arc)]" aria-hidden="true">
        {Icon}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm truncate">{agent.agent}</span>
          {agent.symbol && (
            <span className="px-1.5 py-0.5 text-[10px] font-mono text-[var(--muted)] bg-[var(--surface-2)] rounded-[6px]">
              {agent.symbol}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-[var(--muted)] mt-0.5">
          <span className="flex items-center gap-1 font-mono">
            <span aria-hidden="true">⏱</span>
            {agent.latency_ms}ms
          </span>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <StatusRing
          active={agent.status === 'OK'}
          size="sm"
          ariaLabel={`${agent.agent}: ${agent.status}`}
        />
        <span
          className={cn(
            'text-xs font-medium px-2 py-0.5 rounded-[6px]',
            'bg-[var(--surface-2)]',
            'border',
            `border-${statusColors[agent.status]} text-${statusColors[agent.status]}`
          )}
        >
          {agent.status}
        </span>
      </div>
    </div>
  );
}