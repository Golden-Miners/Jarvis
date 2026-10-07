import { cn } from '../../lib/utils';
import type { Direction } from '../../types/api';

interface DirectionChipProps {
  direction: Direction | null;
  className?: string;
}

export function DirectionChip({ direction, className }: DirectionChipProps) {
  if (!direction) return null;

  const configs = {
    BUY: {
      label: 'BUY',
      className: 'bg-[var(--buy)]/15 text-[var(--buy)] border-[var(--buy)]',
      icon: (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
        </svg>
      ),
    },
    SELL: {
      label: 'SELL',
      className: 'bg-[var(--sell)]/15 text-[var(--sell)] border-[var(--sell)]',
      icon: (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      ),
    },
  };

  const config = configs[direction];

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-[10px] text-xs font-medium border',
        config.className,
        className
      )}
      aria-label={`Direction: ${direction}`}
    >
      <span aria-hidden="true">{config.icon}</span>
      <span>{config.label}</span>
    </span>
  );
}