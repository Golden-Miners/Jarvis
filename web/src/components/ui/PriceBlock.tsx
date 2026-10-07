import { cn } from '../../lib/utils';
import { formatPrice } from '../../lib/utils';
import type { Direction } from '../../types/api';

interface PriceBlockProps {
  entry: number | null;
  sl: number | null;
  tp: number | null;
  rr: number | null;
  direction: Direction | null;
  digits?: number;
  className?: string;
}

export function PriceBlock({ entry, sl, tp, rr, direction, digits = 2, className }: PriceBlockProps) {
  if (entry === null || sl === null || tp === null) return null;

  const entryDir = direction === 'BUY' ? '+' : '-';
  const slColor = direction === 'BUY' ? 'var(--sell)' : 'var(--buy)';
  const tpColor = direction === 'BUY' ? 'var(--buy)' : 'var(--sell)';

  return (
    <div className={cn('grid grid-cols-4 gap-3 text-center', className)}>
      <div className="p-3 rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)]">
        <div className="text-[10px] font-medium text-[var(--muted)] uppercase tracking-wider mb-1">ENTRY</div>
        <div className="font-mono text-[16px] font-medium text-[var(--text)]">{formatPrice(entry, digits)}</div>
        <div className="font-mono text-[11px] text-[var(--muted)] mt-0.5">{entryDir} from current</div>
      </div>
      <div className="p-3 rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)]">
        <div className="text-[10px] font-medium text-[var(--muted)] uppercase tracking-wider mb-1">STOP LOSS</div>
        <div className="font-mono text-[16px] font-medium" style={{ color: slColor }}>{formatPrice(sl, digits)}</div>
        <div className="font-mono text-[11px] text-[var(--muted)] mt-0.5">
          {direction === 'BUY' ? `−${formatPrice(entry - sl, digits)}` : `+${formatPrice(sl - entry, digits)}`}
        </div>
      </div>
      <div className="p-3 rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)]">
        <div className="text-[10px] font-medium text-[var(--muted)] uppercase tracking-wider mb-1">TAKE PROFIT</div>
        <div className="font-mono text-[16px] font-medium" style={{ color: tpColor }}>{formatPrice(tp, digits)}</div>
        <div className="font-mono text-[11px] text-[var(--muted)] mt-0.5">
          {direction === 'BUY' ? `+${formatPrice(tp - entry, digits)}` : `+${formatPrice(entry - tp, digits)}`}
        </div>
      </div>
      <div className="p-3 rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)]">
        <div className="text-[10px] font-medium text-[var(--muted)] uppercase tracking-wider mb-1">R:R</div>
        <div className="font-mono text-[18px] font-bold text-[var(--arc)]">{rr?.toFixed(2) || '—'}</div>
        <div className="font-mono text-[11px] text-[var(--muted)] mt-0.5">target</div>
      </div>
    </div>
  );
}