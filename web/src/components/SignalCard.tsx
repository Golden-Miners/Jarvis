import { cn, formatConfidence, getTimeUntilExpiry } from '../lib/utils';
import { DecisionBadge } from './ui/DecisionBadge';
import { DirectionChip } from './ui/DirectionChip';
import { PriceBlock } from './ui/PriceBlock';
import { ConfidenceRing } from './ui/ConfidenceRing';
import { ScoreBars } from './ui/ScoreBars';
import type { Signal } from '../types/api';

interface SignalCardProps {
  signal: Signal;
  onExpand?: () => void;
  expanded?: boolean;
  className?: string;
}

export function SignalCard({ signal, onExpand, expanded = false, className }: SignalCardProps) {
  const timeUntilExpiry = getTimeUntilExpiry(signal.expires_at);
  const isExpired = signal.status === 'EXPIRED';

  return (
    <article
      className={cn(
        'glass rounded-[16px] p-4 space-y-4 transition-all duration-200',
        'hover:border-[var(--arc)]/50',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="w-10 h-10 rounded-[10px] bg-[var(--surface-2)] flex items-center justify-center text-[var(--arc)]">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.79 1.07M18 12a6 6 0 01-6 6 6 6 0 01-6-6 6 6 0 016-6m0 4v8" />
            </svg>
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-heading font-semibold text-lg truncate">{signal.symbol}</span>
              <DecisionBadge decision={signal.decision} />
              <DirectionChip direction={signal.direction} />
            </div>
            <div className="flex items-center gap-3 text-xs text-[var(--muted)] mt-1">
              <span className="flex items-center gap-1 font-mono">
                <span aria-hidden="true">⏱</span>
                {timeUntilExpiry}
              </span>
              <span className="px-1.5 py-0.5 rounded-[6px] bg-[var(--surface-2)] font-medium"
                style={{ color: isExpired ? 'var(--neutral)' : signal.status === 'OPEN' ? 'var(--buy)' : 'var(--warn)' }}>
                {signal.status}
              </span>
            </div>
          </div>
        </div>
        <ConfidenceRing value={signal.confidence} size="sm" showLabel />
      </div>

      {/* Price Block */}
      {signal.entry && signal.sl && signal.tp && signal.rr && (
        <PriceBlock
          entry={signal.entry}
          sl={signal.sl}
          tp={signal.tp}
          rr={signal.rr}
          direction={signal.direction}
        />
      )}

      {/* Confidence */}
      <div className="flex items-center gap-3">
        <ConfidenceRing value={signal.confidence} size="md" />
        <div className="flex-1">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-[var(--muted)]">Confidence</span>
            <span className="font-mono font-medium" style={{ color: signal.confidence >= 0.7 ? 'var(--buy)' : signal.confidence >= 0.4 ? 'var(--warn)' : 'var(--sell)' }}>
              {formatConfidence(signal.confidence)}
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-[var(--surface-2)] overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${signal.confidence * 100}%`,
                backgroundColor: signal.confidence >= 0.7 ? 'var(--buy)' : signal.confidence >= 0.4 ? 'var(--warn)' : 'var(--sell)',
              }}
            />
          </div>
        </div>
      </div>

      {/* Score Breakdown */}
      <ScoreBars breakdown={signal.score_breakdown} />

      {/* Expandable Rationale */}
      <div className="border-t border-[var(--border)] pt-3">
        <button
          onClick={onExpand}
          className={cn(
            'w-full flex items-center justify-between text-left p-2 rounded-[8px]',
            'bg-[var(--surface-2)] hover:bg-[var(--surface)]/50',
            'transition-colors text-sm font-medium'
          )}
          aria-expanded={expanded}
        >
          <span className="flex items-center gap-2">
            <svg className={cn('w-4 h-4 text-[var(--muted)] transition-transform', expanded && 'rotate-180')} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
            <span>Why this signal — Jarvis Rationale</span>
          </span>
        </button>

        {expanded && (
          <div className="space-y-3 mt-2 animate-in" style={{ animationDelay: '50ms' }}>
            <div className="p-3 rounded-[8px] bg-[var(--surface-2)]">
              <div className="text-xs text-[var(--muted)] mb-1">Rationale</div>
              <p className="text-sm leading-relaxed">{signal.rationale}</p>
            </div>
            <div className="p-3 rounded-[8px] bg-[var(--surface-2)]">
              <div className="text-xs text-[var(--muted)] mb-1">Agent Verdicts</div>
              <div className="space-y-1">
                {Object.entries(signal.agent_verdicts).map(([agent, verdict]) => (
                  <div key={agent} className="flex justify-between text-sm">
                    <span className="text-[var(--muted)] font-medium capitalize">{agent.replace(/_/g, ' ')}</span>
                    <span className="font-mono font-medium text-[var(--arc)]">{verdict}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Disclaimer */}
      <p className="text-center text-[11px] text-[var(--muted)] pt-2 border-t border-[var(--border)]">
        Signals are informational, not financial advice.
      </p>
    </article>
  );
}