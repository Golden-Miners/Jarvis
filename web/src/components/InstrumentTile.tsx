import { cn } from '../lib/utils';
import { StatusRing } from './ui/StatusRing';
import { DecisionBadge } from './ui/DecisionBadge';
import { DirectionChip } from './ui/DirectionChip';
import { ConfidenceRing } from './ui/ConfidenceRing';
import type { Signal, AgentStatus } from '../types/api';

interface InstrumentTileProps {
  symbol: string;
  agent: string;
  signal?: Signal | null;
  agentStatus?: AgentStatus | null;
  featured?: boolean;
  className?: string;
}

const agentNames: Record<string, string> = {
  iron_man: 'Iron Man',
  captain_america: 'Captain America',
  thor: 'Thor',
  hulk: 'Hulk',
  black_panther: 'Black Panther',
};

const agentIcons: Record<string, React.ReactNode> = {
  iron_man: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
    </svg>
  ),
  captain_america: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <circle cx="12" cy="12" r="10" />
      <path d="M8 15v-6" />
      <path d="M16 15v-6" />
    </svg>
  ),
  thor: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h3a1 1 0 011 1v5" />
    </svg>
  ),
  hulk: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 5.636l-13.24 13.24" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M5.636 18.972L18.972 5.636" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364l-13.24-13.24" />
    </svg>
  ),
  black_panther: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <circle cx="12" cy="12" r="10" />
      <path d="M8 14v-4" />
      <path d="M16 14v-4" />
    </svg>
  ),
};

export function InstrumentTile({
  symbol,
  agent,
  signal,
  agentStatus,
  featured = false,
  className,
}: InstrumentTileProps) {
  const Icon = agentIcons[agent] || (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <circle cx="12" cy="12" r="10" />
    </svg>
  );

  return (
    <article
      className={cn(
        'glass rounded-[16px] p-4 space-y-3 transition-all duration-200',
        'hover:border-[var(--arc)]/50',
        featured ? 'md:col-span-2' : '',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-[10px] bg-[var(--surface-2)] flex items-center justify-center text-[var(--arc)] flex-shrink-0">
            {Icon}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-heading font-semibold text-lg truncate">{symbol}</span>
              <span className="px-2 py-0.5 text-[10px] font-medium text-[var(--muted)] bg-[var(--surface-2)] rounded-[6px]">
                {agentNames[agent] || agent}
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs text-[var(--muted)] mt-0.5">
              <StatusRing
                active={agentStatus?.status === 'OK'}
                size="sm"
                ariaLabel={`${agentNames[agent] || agent}: ${agentStatus?.status || 'Unknown'}`}
              />
              <span className="font-mono">{agentStatus?.latency_ms || 0}ms</span>
            </div>
          </div>
        </div>
        {signal && (
          <div className="flex items-center gap-2 flex-shrink-0">
            <DecisionBadge decision={signal.decision} />
            <DirectionChip direction={signal.direction} />
            <ConfidenceRing value={signal.confidence} size="sm" showLabel />
          </div>
        )}
      </div>

      {/* Signal Summary or "No Setup" */}
      {signal ? (
        <div className="grid grid-cols-4 gap-3 text-center">
          <div className="p-2 rounded-[8px] bg-[var(--surface-2)]">
            <div className="text-[10px] font-medium text-[var(--muted)] uppercase tracking-wider">ENTRY</div>
            <div className="font-mono text-sm text-[var(--text)]">{signal.entry?.toFixed(2)}</div>
          </div>
          <div className="p-2 rounded-[8px] bg-[var(--surface-2)]">
            <div className="text-[10px] font-medium text-[var(--muted)] uppercase tracking-wider">SL</div>
            <div className="font-mono text-sm" style={{ color: signal.direction === 'BUY' ? 'var(--sell)' : 'var(--buy)' }}>
              {signal.sl?.toFixed(2)}
            </div>
          </div>
          <div className="p-2 rounded-[8px] bg-[var(--surface-2)]">
            <div className="text-[10px] font-medium text-[var(--muted)] uppercase tracking-wider">TP</div>
            <div className="font-mono text-sm" style={{ color: signal.direction === 'BUY' ? 'var(--buy)' : 'var(--sell)' }}>
              {signal.tp?.toFixed(2)}
            </div>
          </div>
          <div className="p-2 rounded-[8px] bg-[var(--surface-2)]">
            <div className="text-[10px] font-medium text-[var(--muted)] uppercase tracking-wider">R:R</div>
            <div className="font-mono font-bold text-[var(--arc)]">{signal.rr?.toFixed(2)}</div>
          </div>
        </div>
      ) : (
        <div className="text-center py-4 text-[var(--muted)]">
          <p className="text-sm">No qualified setup</p>
          <p className="text-xs mt-1">Jarvis is patient</p>
        </div>
      )}
    </article>
  );
}