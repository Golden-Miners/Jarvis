import { useStats } from '@/hooks/useData';

const LOW_SAMPLE_THRESHOLD = 30;

function StatCard({ label, value, subtext, warn }: {
  label: string;
  value: string | number;
  subtext?: string;
  warn?: boolean;
}) {
  return (
    <div className="glass rounded-[16px] p-4">
      <p className="text-[11px] text-[var(--muted)] uppercase tracking-wider mb-1">{label}</p>
      <p className={`font-mono font-bold text-xl ${warn ? 'text-[var(--warn)]' : 'text-[var(--text)]'}`}>
        {value}
      </p>
      {subtext && <p className="text-[11px] text-[var(--muted)] mt-0.5">{subtext}</p>}
    </div>
  );
}

export function StatsPage() {
  const { data: stats, isLoading } = useStats();

  if (isLoading) {
    return (
      <div className="p-4 pb-20 md:pb-4">
        <h1 className="font-heading font-semibold text-xl mb-4">Stats</h1>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="glass rounded-[16px] h-24 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-4 pb-20 md:pb-4">
        <h1 className="font-heading font-semibold text-xl mb-4">Stats</h1>
        <div className="glass rounded-[16px] p-8 text-center">
          <p className="text-[var(--muted)]">No stats available yet</p>
        </div>
      </div>
    );
  }

  const { total_signals, win_rate, avg_rr, expectancy } = stats;
  const overallN = total_signals;
  const lowSample = overallN < LOW_SAMPLE_THRESHOLD;

  return (
    <div className="p-4 pb-20 md:pb-4 space-y-6">
      <h1 className="font-heading font-semibold text-xl">Stats</h1>

      {/* Low sample warning */}
      {lowSample && (
        <div
          className="px-4 py-2 rounded-[10px] bg-[color-mix(in_oklch,var(--warn)_15%,transparent)] border border-[var(--warn)] text-sm text-[var(--warn)]"
          role="alert"
        >
          Low sample size (n={overallN}). Results may not be statistically significant.
        </div>
      )}

      {/* Overall stats */}
      <section aria-label="Overall statistics">
        <h2 className="font-heading font-semibold text-sm text-[var(--muted)] mb-3 uppercase tracking-wider">
          Overall
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label="Total Signals" value={total_signals} subtext={`n=${total_signals}`} warn={lowSample} />
          <StatCard
            label="Win Rate"
            value={`${(win_rate * 100).toFixed(1)}%`}
            subtext={`n=${total_signals}`}
            warn={lowSample}
          />
          <StatCard label="Avg R:R" value={avg_rr.toFixed(2)} subtext="per signal" warn={lowSample} />
          <StatCard
            label="Expectancy"
            value={expectancy.toFixed(2)}
            subtext="R per trade"
            warn={lowSample}
          />
        </div>
      </section>

      {/* By instrument */}
      {Object.keys(stats.by_instrument).length > 0 && (
        <section aria-label="Statistics by instrument">
          <h2 className="font-heading font-semibold text-sm text-[var(--muted)] mb-3 uppercase tracking-wider">
            By Instrument
          </h2>
          <div className="space-y-3">
            {Object.entries(stats.by_instrument).map(([sym, data]) => {
              const n = data.count;
              const isLow = n < LOW_SAMPLE_THRESHOLD;
              return (
                <div key={sym} className="glass rounded-[16px] p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className={`font-heading font-semibold ${sym === 'XAUUSD' ? 'text-[var(--gold)]' : ''}`}>
                      {sym}
                    </h3>
                    {isLow && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-[color-mix(in_oklch,var(--warn)_15%,transparent)] text-[var(--warn)]">
                        low sample (n&lt;{LOW_SAMPLE_THRESHOLD})
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <p className="text-[11px] text-[var(--muted)]">Win Rate</p>
                      <p className="font-mono text-sm font-medium">{(data.win_rate * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-[11px] text-[var(--muted)]">Avg R:R</p>
                      <p className="font-mono text-sm font-medium">{data.avg_rr.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-[11px] text-[var(--muted)]">Count</p>
                      <p className="font-mono text-sm font-medium">{n}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* By strategy */}
      {Object.keys(stats.by_strategy).length > 0 && (
        <section aria-label="Statistics by strategy">
          <h2 className="font-heading font-semibold text-sm text-[var(--muted)] mb-3 uppercase tracking-wider">
            By Strategy
          </h2>
          <div className="space-y-3">
            {Object.entries(stats.by_strategy).map(([strategy, data]) => {
              const n = data.count;
              const isLow = n < LOW_SAMPLE_THRESHOLD;
              return (
                <div key={strategy} className="glass rounded-[16px] p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-heading font-medium text-sm capitalize">
                      {strategy.replace('_', ' ')}
                    </h3>
                    {isLow && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-[color-mix(in_oklch,var(--warn)_15%,transparent)] text-[var(--warn)]">
                        low sample (n&lt;{LOW_SAMPLE_THRESHOLD})
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <p className="text-[11px] text-[var(--muted)]">Win Rate</p>
                      <p className="font-mono text-sm font-medium">{(data.win_rate * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-[11px] text-[var(--muted)]">Avg R:R</p>
                      <p className="font-mono text-sm font-medium">{data.avg_rr.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-[11px] text-[var(--muted)]">Count</p>
                      <p className="font-mono text-sm font-medium">{n}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {total_signals === 0 && (
        <div className="glass rounded-[16px] p-8 text-center">
          <p className="text-[var(--muted)]">No completed signals yet</p>
          <p className="text-xs text-[var(--muted)] mt-1">Stats appear after signals resolve</p>
        </div>
      )}
    </div>
  );
}
