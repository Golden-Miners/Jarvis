import { useParams } from 'react-router-dom';
import { useInstruments, useNews, useAgents } from '@/hooks/useData';
import { useSignals } from '@/hooks/useSignals';
import { SignalCard } from '@/components/SignalCard';
import { AgentRow } from '@/components/ui/AgentRow';
import { formatAgentName } from '@/lib/format';

export function InstrumentPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const { data: instruments = [] } = useInstruments();
  const { data: newsResult } = useNews({ symbol: symbol!, limit: 20 });
  const { data: signalsResult } = useSignals({ symbol: symbol!, limit: 20 });
  const { data: agents = [] } = useAgents();

  const inst = instruments.find((i) => i.symbol === symbol);
  const newsItems = newsResult?.data ?? [];
  const signals = signalsResult?.data ?? [];
  const symbolAgents = agents.filter((a) => a.symbol === symbol || a.symbol === null);

  if (!symbol) return null;

  return (
    <div className="p-4 pb-20 md:pb-4 space-y-4">
      {/* Header */}
      <div className="glass rounded-[16px] p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className={`font-heading font-bold text-2xl ${symbol === 'XAUUSD' ? 'text-[var(--gold)]' : 'text-[var(--text)]'}`}>
              {symbol}
            </h1>
            <p className="text-sm text-[var(--muted)]">
              Managed by {formatAgentName(inst?.agent_name ?? symbol)}
            </p>
          </div>
          {inst && (
            <div className="text-right">
              <p className="text-xs text-[var(--muted)]">Digits</p>
              <p className="font-mono text-sm">{inst.digits}</p>
            </div>
          )}
        </div>
      </div>

      {/* Latest signals */}
      {signals.length > 0 && (
        <section aria-label={`${symbol} signals`}>
          <h2 className="font-heading font-semibold text-base mb-3">Signal History</h2>
          <div className="space-y-3">
            {signals.slice(0, 5).map((sig) => (
              <SignalCard key={sig.id} signal={sig} expanded={false} onExpand={() => {}} />
            ))}
          </div>
        </section>
      )}

      {/* News for symbol */}
      {newsItems.length > 0 && (
        <section aria-label={`${symbol} news`}>
          <h2 className="font-heading font-semibold text-base mb-3">News &amp; Macro</h2>
          <div className="space-y-2">
            {newsItems.map((item) => (
              <div key={item.id ?? item.url} className="glass rounded-[16px] p-4">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium">{item.source ?? item.symbol}</span>
                  <span className="text-[11px] font-mono text-[var(--muted)]">
                    impact {item.impact}/10
                  </span>
                </div>
                <p className="text-sm text-[var(--muted)]">{item.summary}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Agents */}
      {symbolAgents.length > 0 && (
        <section aria-label={`${symbol} agents`}>
          <h2 className="font-heading font-semibold text-base mb-3">Agent Status</h2>
          <div className="space-y-2">
            {symbolAgents.map((agent) => (
              <AgentRow key={agent.agent} agent={agent} />
            ))}
          </div>
        </section>
      )}

      {signals.length === 0 && newsItems.length === 0 && (
        <div className="glass rounded-[16px] p-8 text-center">
          <p className="text-[var(--muted)]">No data for {symbol} yet</p>
        </div>
      )}
    </div>
  );
}
