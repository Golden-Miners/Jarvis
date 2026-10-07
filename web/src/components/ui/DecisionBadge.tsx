import { cn } from '../../lib/utils';
import type { Decision } from '../../types/api';

interface DecisionBadgeProps {
  decision: Decision;
  className?: string;
}

export function DecisionBadge({ decision, className }: DecisionBadgeProps) {
  const configs = {
    TRADE: {
      label: 'TRADE',
      className: 'bg-[var(--buy)]/15 text-[var(--buy)] border-[var(--buy)]',
      icon: (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-6-6h12" />
        </svg>
      ),
    },
    NO_TRADE: {
      label: 'NO TRADE',
      className: 'bg-[var(--neutral)]/15 text-[var(--neutral)] border-[var(--neutral)]',
      icon: (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 5.636l-13.24 13.24m0 0L5.636 18.972 18.972 5.636M18.364 18.364l-13.24-13.24" />
        </svg>
      ),
    },
  };

  const config = configs[decision];

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-[10px] text-xs font-medium border',
        config.className,
        className
      )}
      aria-label={`Decision: ${decision}`}
    >
      <span aria-hidden="true">{config.icon}</span>
      <span>{config.label}</span>
    </span>
  );
}