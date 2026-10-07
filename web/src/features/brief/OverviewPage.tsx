import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useSignals, useRunCycle } from '@/hooks/useSignals';
import { useInstruments, useAgents, useCalendar, useNews } from '@/hooks/useData';
import { useAuth } from '@/app/AuthContext';
import { InstrumentTile } from '@/components/InstrumentTile';
import { SignalCard } from '@/components/SignalCard';
import { formatCountdown } from '@/lib/format';
import type { NewsImpact, AgentStatus, Signal } from '@/types/api';

function BriefCard({ label, value, subtext, accent }: {
  label: string; value: string | number; subtext?: string; accent?: string;
}) {
  return (
    <div className="glass rounded-[16px] p-4 flex-1 min-w-0" style={{ borderTop: accent ? `2px solid ${accent}` : undefined }}>
      <p className="text-[11px] text-[var(--muted)] uppercase tracking-wider mb-1">{label}</p>
      <p className="font-mono font-bold text-2xl text-[var(--text)]">{value}</p>
      {subtext && <p className="text-[11px] text-[var(--muted)] mt-0.5 truncate">{subtext}</p>}
    </div>
  );
}

function DegradedBanner({ agents }: { agents: AgentStatus[] }) {
  const degraded = agents.filter((a) => a.status === 'DEGRADED' || a.status === 'ERROR');
  if (degraded.length === 0) return null;
  return (
    <div className="px-4 py-2 rounded-[10px] bg-[color-mix(in_oklch,var(--warn)_15%,transparent)] border border-[var(--warn)] text-sm text-[var(--warn)]" role="alert">
      <strong>Degraded:</strong> {degraded.map((a) => a.agent).join(', ')} unavailable. Confidence may be reduced.
    </div>
  );
}

function NewsItemRow({ item }: { item: NewsImpact }) {
  const impactColor = item.impact >= 7 ? 'var(--sell)' : item.impact >= 4 ? 'var(--warn)' : 'var(--buy)';
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium truncate">{item.symbol}</span>
        <div className="flex items-center gap-1 shrink-0" aria-label={`Impact ${item.impact}/10`}>
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="w-1 h-2 rounded-sm" style={{ backgroundColor: i < item.impact ? impactColor : 'var(--border)' }} />
          ))}
        </div>
      </div>
      <p className="text-[11px] text-[var(--muted)] line-clamp-2">{item.summary}</p>
    </div>
  );
}

function AgentMiniRow({ agent }: { agent: AgentStatus }) {
  const dotColor = agent.status === 'OK' ? 'var(--buy)' : agent.status === 'DEGRADED' ? 'var(--warn)' : 'var(--sell)';
  const latencyLabel = agent.latency_ms < 1000 ? `${agent.latency_ms}ms` : `${(agent.latency_ms / 1000).toFixed(1)}s`;
  return (
    <div className="flex items-center justify-between gap-2">
      <div className="flex items-center gap-2 min-w-0">
        <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: dotColor }} aria-hidden="true" />
        <span className="text-xs truncate">{agent.agent.replace('_', ' ')}</span>
      </div>
      <span className="text-[11px] font-mono text-[var(--muted)] shrink-0">{latencyLabel}</span>
    </div>
  );
}

export function OverviewPage() {
  const { isOwner } = useAuth();
  const { data: signalsResult } = useSignals({ limit: 50 });
  const { data: instruments = [] } = useInstruments();
  const { data: agents = [] } = useAgents();
  const { data: calendarResult } = useCalendar();
  const { data: newsResult } = useNews({ limit: 10 });
  const runCycle = useRunCycle();

  const [expandedSignals, setExpandedSignals] = useState<Set<string>>(new Set());

  // Extract signals array from API response
  const allSignals: Signal[] = signalsResult?.data ?? [];
  const tradeSignals = allSignals.filter((s) => s.decision === 'TRADE');
  const openSignals = tradeSignals.filter((s) => s.status === 'OPEN');
  const waitingCount = Math.max(0, instruments.length - new Set(openSignals.map((s) => s.symbol)).size);

  const nextEvent = calendarResult?.data?.[0];
  const nextEventCountdown = nextEvent?.event_time ? formatCountdown(nextEvent.event_time) : null;
  const okAgents = agents.filter((a) => a.status === 'OK').length;
  const totalAgents = agents.length;
  const newsItems = newsResult?.data ?? [];

  const toggleExpand = (id: string) => {
    setExpandedSignals((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const briefLine = React.useMemo(() => {
    const q = openSignals.length;
    const w = waitingCount;
    const event = nextEvent?.name;
    const time = nextEventCountdown;
    let text = q > 0 ? `${q} setup${q > 1 ? 's' : ''} qualified` : 'No setups qualified';
    if (w > 0) text += `, ${w} waiting`;
    if (event && time) text += `. Next: ${event} in ${time}`;
    return text;
  }, [openSignals.length, waitingCount, nextEvent?.name, nextEventCountdown]);

  return (
    <div className="p-4 pb-20 md:pb-4 space-y-4">
      {/* Brief line */}
      <div className="glass rounded-[16px] px-5 py-3">
        <p className="text-sm font-medium text-[var(--text)]">
          <span className="text-[var(--arc)] font-heading">JARVIS BRIEF</span>
          {' — '}{briefLine}
        </p>
      </div>

      <DegradedBanner agents={agents} />

      {/* Brief cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <BriefCard label="Qualified" value={openSignals.length} accent="var(--arc)" />
        <BriefCard label="Waiting" value={waitingCount} subtext={instruments.length > 0 ? `${instruments.length} instruments checked` : undefined} />
        <BriefCard label="Open" value={openSignals.length} subtext={openSignals[0]?.expires_at ? `Next expiry: ${formatCountdown(openSignals[0].expires_at)}` : undefined} />
        <BriefCard label="Next Event" value={nextEvent?.name ?? '—'} subtext={nextEventCountdown ?? 'No upcoming events'} accent={nextEvent ? 'var(--warn)' : undefined} />
        <BriefCard label="System Health" value={totalAgents > 0 ? `${okAgents}/${totalAgents}` : '—'} subtext={totalAgents > 0 ? 'agents OK' : undefined} accent={okAgents < totalAgents && totalAgents > 0 ? 'var(--sell)' : 'var(--buy)'} />
      </div>

      {/* Instrument strip */}
      <section aria-label="Instruments">
        <h2 className="font-heading font-semibold text-sm text-[var(--muted)] mb-3 uppercase tracking-wider">Instruments</h2>
        <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide snap-x snap-mandatory">
          {instruments.length > 0 ? (
            instruments.map((inst) => {
              const sig = tradeSignals.find((s) => s.symbol === inst.symbol) ?? null;
              const agentStatus = agents.find((a) => a.symbol === inst.symbol) ?? null;
              return (
                <Link key={inst.symbol} to={`/instruments/${inst.symbol}`} className="shrink-0 snap-start">
                  <InstrumentTile symbol={inst.symbol} agent={inst.agent_name} signal={sig} agentStatus={agentStatus} featured={inst.symbol === 'XAUUSD'} />
                </Link>
              );
            })
          ) : (
            <div className="glass rounded-[16px] px-6 py-4 text-sm text-[var(--muted)] shrink-0">No instruments configured</div>
          )}
        </div>
      </section>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-heading font-semibold text-base">Active Signals</h2>
            {isOwner && (
              <button onClick={() => runCycle.mutate()} disabled={runCycle.isPending}
                className="px-3 py-1.5 rounded-[10px] bg-[var(--arc)] text-[var(--bg)] text-xs font-medium hover:opacity-90 disabled:opacity-50 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--arc)]">
                {runCycle.isPending ? 'Running…' : 'Run now'}
              </button>
            )}
          </div>
          {openSignals.length > 0 ? (
            <div className="space-y-3">
              {openSignals.map((sig) => (
                <SignalCard key={sig.id} signal={sig} expanded={expandedSignals.has(sig.id)} onExpand={() => toggleExpand(sig.id)} />
              ))}
            </div>
          ) : (
            <div className="glass rounded-[16px] p-8 text-center">
              <p className="text-[var(--muted)]">No qualified setups</p>
              <p className="text-xs text-[var(--muted)] mt-1">Jarvis is patient</p>
            </div>
          )}
        </div>

        {/* Right rail */}
        <div className="space-y-4">
          <section aria-label="News & Macro">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-heading font-semibold text-sm text-[var(--muted)] uppercase tracking-wider">News &amp; Macro</h3>
              <Link to="/news" className="text-xs text-[var(--arc)] hover:underline">View all</Link>
            </div>
            <div className="glass rounded-[16px] p-4">
              {newsItems.length > 0 ? (
                <div className="space-y-3 max-h-[300px] overflow-y-auto">
                  {newsItems.slice(0, 6).map((item) => <NewsItemRow key={item.id ?? item.url ?? Math.random()} item={item} />)}
                </div>
              ) : (
                <p className="text-sm text-[var(--muted)] text-center py-4">No relevant news right now</p>
              )}
            </div>
          </section>

          <section aria-label="Agent roster">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-heading font-semibold text-sm text-[var(--muted)] uppercase tracking-wider">Agents</h3>
              <Link to="/agents" className="text-xs text-[var(--arc)] hover:underline">View all</Link>
            </div>
            <div className="glass rounded-[16px] p-4">
              {agents.length > 0 ? (
                <div className="space-y-2">
                  {agents.slice(0, 8).map((agent) => <AgentMiniRow key={agent.agent} agent={agent} />)}
                </div>
              ) : (
                <p className="text-sm text-[var(--muted)] text-center py-4">No agent data yet</p>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
