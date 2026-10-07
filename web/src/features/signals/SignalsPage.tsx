import { useState } from 'react';
import { useSignals } from '@/hooks/useSignals';
import { SignalCard } from '@/components/SignalCard';


export function SignalsPage() {
  const [filterDir, setFilterDir] = useState<'ALL' | 'BUY' | 'SELL'>('ALL');
  const [filterSymbol, setFilterSymbol] = useState<string>('');
  const { data: result, isLoading } = useSignals({ limit: 100 });
  const signals = result?.data ?? [];

  const filtered = signals.filter((s) => {
    if (filterDir !== 'ALL' && s.direction !== filterDir) return false;
    if (filterSymbol && s.symbol !== filterSymbol) return false;
    return true;
  });

  const symbols = [...new Set(signals.map((s) => s.symbol))];

  return (
    <div className="p-4 pb-20 md:pb-4 space-y-4">
      <h1 className="font-heading font-semibold text-xl">Signals</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        {(['ALL', 'BUY', 'SELL'] as const).map((d) => (
          <button
            key={d}
            onClick={() => setFilterDir(d)}
            className={`px-3 py-1.5 rounded-[10px] text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--arc)] ${
              filterDir === d
                ? 'bg-[var(--arc)] text-[var(--bg)]'
                : 'bg-[var(--surface)] border border-[var(--border)] text-[var(--muted)] hover:text-[var(--text)]'
            }`}
          >
            {d}
          </button>
        ))}
        <select
          value={filterSymbol}
          onChange={(e) => setFilterSymbol(e.target.value)}
          className="px-3 py-1.5 rounded-[10px] text-xs bg-[var(--surface)] border border-[var(--border)] text-[var(--muted)] focus:outline-none focus:ring-2 focus-visible:ring-[var(--arc)]"
        >
          <option value="">All symbols</option>
          {symbols.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="glass rounded-[16px] h-32 animate-pulse" />
          ))}
        </div>
      ) : filtered.length > 0 ? (
        <div className="space-y-3">
          {filtered.map((sig) => (
            <SignalCard
              key={sig.id}
              signal={sig}
              expanded={false}
              onExpand={() => {}}
            />
          ))}
        </div>
      ) : (
        <div className="glass rounded-[16px] p-8 text-center">
          <p className="text-[var(--muted)]">No signals match the filter</p>
        </div>
      )}
    </div>
  );
}
