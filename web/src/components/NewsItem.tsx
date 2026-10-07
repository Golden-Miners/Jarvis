import { cn, formatTimeAgo } from '../lib/utils';
import type { NewsImpact } from '../types/api';

interface NewsItemProps {
  news: NewsImpact;
  className?: string;
}

const biasConfig = {
  BULLISH: { color: 'var(--buy)', icon: (
    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
    </svg>
  )},
  BEARISH: { color: 'var(--sell)', icon: (
    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  )},
  NEUTRAL: { color: 'var(--neutral)', icon: (
    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14" />
    </svg>
  )},
};

export function NewsItem({ news, className }: NewsItemProps) {
  const config = biasConfig[news.bias as keyof typeof biasConfig];
  const hasBlackout = news.blackout_until && new Date(news.blackout_until) > new Date();

  return (
    <article className={cn('glass rounded-[10px] p-3 space-y-2', className)}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span className={cn('w-2 h-2 rounded-full flex-shrink-0', config.icon?.props?.style?.color ? `bg-${config.color}` : '')}>
            {config.icon}
          </span>
          <span className="font-mono text-xs text-[var(--muted)] truncate">{news.symbol}</span>
          <span
            className={cn(
              'px-1.5 py-0.5 text-[10px] font-medium rounded-[6px] border',
              `bg-${config.color}/15 text-${config.color} border-${config.color}`
            )}
          >
            {news.bias}
          </span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="px-2 py-0.5 text-[10px] font-mono font-medium bg-[var(--surface-2)] rounded-[6px] text-[var(--warn)]">
            Impact: {news.impact}/10
          </span>
          <span className="text-[11px] text-[var(--muted)]">{formatTimeAgo(new Date(news.published_at || Date.now()))}</span>
        </div>
      </div>

      <p className="text-sm text-[var(--text)] leading-relaxed">{news.summary}</p>

      {hasBlackout && (
        <div className="flex items-center gap-2 px-2 py-1.5 rounded-[8px] bg-[var(--warn)]/15 border border-[var(--warn)]/30">
          <svg className="w-3.5 h-3.5 text-[var(--warn)] flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 17h.01" />
          </svg>
          <span className="text-xs font-medium text-[var(--warn)]">
            Blackout until {new Date(news.blackout_until!).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      )}
    </article>
  );
}