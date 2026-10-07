import { useNews, useCalendar } from '@/hooks/useData';
import { formatCountdown } from '@/lib/format';

export function NewsPage() {
  const { data: newsResult, isLoading } = useNews({ limit: 100 });
  const { data: calendarResult } = useCalendar();
  const news = newsResult?.data ?? [];
  const events = calendarResult?.data ?? [];

  return (
    <div className="p-4 pb-20 md:pb-4 space-y-4">
      <h1 className="font-heading font-semibold text-xl">News &amp; Macro</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* News list */}
        <section aria-label="News">
          <h2 className="font-heading font-semibold text-sm text-[var(--muted)] mb-3 uppercase tracking-wider">
            Recent News
          </h2>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="glass rounded-[16px] h-20 animate-pulse" />
              ))}
            </div>
          ) : news.length > 0 ? (
            <div className="space-y-2">
              {news.map((item) => (
                <div key={item.id ?? item.url} className="glass rounded-[16px] p-4">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium">{item.symbol}</span>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded ${
                          item.bias === 'BULLISH'
                            ? 'bg-[color-mix(in_oklch,var(--buy)_15%,transparent)] text-[var(--buy)]'
                            : item.bias === 'BEARISH'
                            ? 'bg-[color-mix(in_oklch,var(--sell)_15%,transparent)] text-[var(--sell)]'
                            : 'bg-[var(--surface-2)] text-[var(--muted)]'
                        }`}
                      >
                        {item.bias}
                      </span>
                    </div>
                    <span className="text-[11px] font-mono text-[var(--muted)] shrink-0">
                      {item.impact}/10
                    </span>
                  </div>
                  <p className="text-sm text-[var(--muted)] line-clamp-2">{item.summary}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="glass rounded-[16px] p-6 text-center">
              <p className="text-sm text-[var(--muted)]">No news available</p>
              <p className="text-xs text-[var(--muted)] mt-1">Configure news source</p>
            </div>
          )}
        </section>

        {/* Calendar */}
        <section aria-label="Economic calendar">
          <h2 className="font-heading font-semibold text-sm text-[var(--muted)] mb-3 uppercase tracking-wider">
            Economic Calendar
          </h2>
          <div className="space-y-2">
            {events.length > 0 ? (
              events.map((event) => (
                <div key={event.id} className="glass rounded-[16px] p-4">
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <p className="text-sm font-medium">{event.name}</p>
                      <p className="text-xs text-[var(--muted)]">{event.currency}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-mono text-[var(--muted)]">
                        {formatCountdown(event.event_time)}
                      </p>
                      {/* Importance dots */}
                      <div className="flex justify-end gap-0.5 mt-1">
                        {Array.from({ length: 3 }).map((_, i) => (
                          <div
                            key={i}
                            className="w-1.5 h-1.5 rounded-full"
                            style={{
                              backgroundColor:
                                i < event.importance
                                  ? 'var(--warn)'
                                  : 'var(--border)',
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                  {event.blackout_start && (
                    <div className="mt-2 px-2 py-1 rounded-[6px] bg-[color-mix(in_oklch,var(--warn)_15%,transparent)] text-[10px] text-[var(--warn)]">
                      Blackout: {formatCountdown(event.blackout_start)} – {formatCountdown(event.blackout_end ?? event.blackout_start)}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="glass rounded-[16px] p-6 text-center">
                <p className="text-sm text-[var(--muted)]">No upcoming events</p>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
