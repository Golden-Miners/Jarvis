import { useAgents } from '@/hooks/useData';
import { AgentRow } from '@/components/ui/AgentRow';

const AGENT_GROUPS: Record<string, string[]> = {
  Core: ['jarvis', 'vision', 'strange', 'fury', 'quicksilver', 'war_machine', 'coulson'],
  Instruments: ['iron_man', 'captain_america', 'thor', 'hulk', 'black_panther'],
  Strategies: ['hawkeye', 'black_widow', 'falcon', 'ant_man', 'wasp'],
};

export function AgentsPage() {
  const { data: agents = [], isLoading } = useAgents({ limit: 100 });

  const byName = (name: string) =>
    agents.find((a) => a.agent === name) ?? null;

  return (
    <div className="p-4 pb-20 md:pb-4 space-y-4">
      <h1 className="font-heading font-semibold text-xl">Agents</h1>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 7 }).map((_, i) => (
            <div key={i} className="glass rounded-[16px] h-16 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(AGENT_GROUPS).map(([group, names]) => (
            <section key={group} aria-label={`${group} agents`}>
              <h2 className="font-heading font-semibold text-sm text-[var(--muted)] mb-3 uppercase tracking-wider">
                {group}
              </h2>
              <div className="space-y-2">
                {names.map((name) => {
                  const agent = byName(name);
                  if (!agent) return null;
                  return <AgentRow key={name} agent={agent} />;
                })}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
