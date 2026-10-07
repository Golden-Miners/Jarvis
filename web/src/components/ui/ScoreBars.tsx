import { cn } from '../../lib/utils';

interface ScoreBarsProps {
  breakdown: Record<string, number>;
  className?: string;
}

const labelMap: Record<string, string> = {
  strategies: 'Strategies',
  structure: 'Structure',
  forecast: 'Forecast',
  news: 'News',
};

const colorMap: Record<string, string> = {
  strategies: 'var(--arc)',
  structure: 'var(--buy)',
  forecast: 'var(--warn)',
  news: 'var(--gold)',
};

export function ScoreBars({ breakdown, className }: ScoreBarsProps) {
  const entries = Object.entries(breakdown);
  if (entries.length === 0) return null;

  const total = entries.reduce((sum, [, v]) => sum + v, 0);

  return (
    <div className={cn('space-y-2', className)} role="img" aria-label="Score breakdown">
      {entries.map(([key, value]) => {
        const pct = total > 0 ? (value / total) * 100 : 0;
        const label = labelMap[key] || key;
        const color = colorMap[key] || 'var(--arc)';
        return (
          <div key={key} className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-[var(--muted)] font-medium">{label}</span>
              <span className="font-mono font-medium" style={{ color }}>
                {value.toFixed(2)}
              </span>
            </div>
            <div className="h-1.5 rounded-full bg-[var(--surface-2)] overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500 ease-out"
                style={{
                  width: `${Math.min(pct, 100)}%`,
                  backgroundColor: color,
                }}
              />
            </div>
          </div>
        );
      })}
      {total > 0 && (
        <div className="flex justify-between text-xs mt-1 pt-1 border-t border-[var(--border)]">
          <span className="text-[var(--muted)] font-medium">Total</span>
          <span className="font-mono font-bold text-[var(--arc)]">{total.toFixed(2)}</span>
        </div>
      )}
    </div>
  );
}