import { useState } from 'react';
import { useSignals } from '@/hooks/useSignals';
import { DirectionChip } from '@/components/ui/DirectionChip';
import { formatPrice, formatTimeAgo } from '@/lib/format';

export function HistoryPage() {
  const [symbol, setSymbol] = useState('');
  const [status, setStatus] = useState('');
  const [cursor, setCursor] = useState<string | undefined>();

  const { data: result, isLoading } = useSignals({ limit: 50, cursor });
  const signals = result?.data ?? [];

  const filtered = signals.filter((s) => {
    if (symbol && s.symbol !== symbol) return false;
    if (status && s.status !== status) return false;
    return true;
  });

  const symbols = [...new Set(signals.map((s) => s.symbol))];

  const statusBadge = (sig: typeof signals[0]) => {
    const color = sig.status === 'TP_HIT' ? 'var(--buy)' : sig.status === 'SL_HIT' ? 'var(--sell)' : sig.status === 'OPEN' ? 'var(--arc)' : 'var(--muted)';
    return <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ backgroundColor: `color-mix(in oklch, ${color} 15%, transparent)`, color }}>{sig.status.replace('_', ' ')}</span>;
  };

  return (
    <div className="p-4 pb-20 md:pb-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading font-semibold text-xl">History</h1>
        <p className="text-xs text-[var(--muted)]">{filtered.length} signals</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <select value={symbol} onChange={(e) => setSymbol(e.target.value)}
          className="px-3 py-1.5 rounded-[10px] text-xs bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:ring-2 focus-visible:ring-[var(--arc)]">
          <option value="">All symbols</option>
          {symbols.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)}
          className="px-3 py-1.5 rounded-[10px] text-xs bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:ring-2 focus-visible:ring-[var(--arc)]">
          <option value="">All statuses</option>
          <option value="OPEN">Open</option>
          <option value="TP_HIT">TP Hit</option>
          <option value="SL_HIT">SL Hit</option>
          <option value="EXPIRED">Expired</option>
        </select>
      </div>

      {/* Table */}
      <div className="space-y-2">
        <div className="hidden md:grid grid-cols-12 gap-2 px-4 py-2 text-[11px] text-[var(--muted)] uppercase tracking-wider">
          <div className="col-span-2">Time</div>
          <div className="col-span-1">Symbol</div>
          <div className="col-span-1">Dir</div>
          <div className="col-span-2">Entry / SL / TP</div>
          <div className="col-span-1">RR</div>
          <div className="col-span-1">Conf</div>
          <div className="col-span-1">Status</div>
          <div className="col-span-2">Reason</div>
          <div className="col-span-1">Result</div>
        </div>

        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => <div key={i} className="glass rounded-[16px] h-14 animate-pulse" />)
        ) : filtered.length > 0 ? (
          filtered.map((sig) => (
            <div key={sig.id} className="glass rounded-[16px] p-4 md:grid md:grid-cols-12 md:gap-2 md:items-center md:p-3">
              <div className="md:contents">
                <div className="col-span-2 text-xs text-[var(--muted)]">{formatTimeAgo(sig.created_at)}</div>
                <div className="col-span-1 font-mono text-sm font-medium mt-1 md:mt-0">{sig.symbol}</div>
                <div className="col-span-1 mt-1 md:mt-0">{sig.direction && <DirectionChip direction={sig.direction} />}</div>
                <div className="col-span-2 font-mono text-xs mt-1 md:mt-0 space-y-0.5">
                  <div>Entry: {formatPrice(sig.entry)}</div>
                  <div className="text-[var(--sell)]">SL: {formatPrice(sig.sl)}</div>
                  <div className="text-[var(--buy)]">TP: {formatPrice(sig.tp)}</div>
                </div>
                <div className="col-span-1 font-mono text-xs mt-1 md:mt-0">{sig.rr?.toFixed(1) ?? '—'}</div>
                <div className="col-span-1 font-mono text-xs mt-1 md:mt-0">{Math.round(sig.confidence * 100)}%</div>
                <div className="col-span-1 mt-1 md:mt-0">{statusBadge(sig)}</div>
                <div className="col-span-2 text-[10px] text-[var(--muted)] mt-1 md:mt-0 truncate">{sig.no_trade_reason ?? sig.rationale?.slice(0, 60) ?? '—'}</div>
                <div className="col-span-1 mt-1 md:mt-0">
                  <span className={`text-xs font-medium ${sig.status === 'TP_HIT' ? 'text-[var(--buy)]' : sig.status === 'SL_HIT' ? 'text-[var(--sell)]' : 'text-[var(--muted)]'}`}>
                    {sig.status === 'TP_HIT' ? '+1R' : sig.status === 'SL_HIT' ? '-1R' : '—'}
                  </span>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="glass rounded-[16px] p-8 text-center">
            <p className="text-[var(--muted)]">No signals match the filter</p>
          </div>
        )}
      </div>

      {result?.next_cursor && (
        <button onClick={() => setCursor(result.next_cursor ?? undefined)}
          className="w-full py-2 rounded-[10px] bg-[var(--surface)] border border-[var(--border)] text-sm text-[var(--muted)] hover:text-[var(--text)] transition-colors">
          Load more
        </button>
      )}
    </div>
  );
}
