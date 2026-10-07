import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

const REFRESH_INTERVAL = 30_000;

function pauseWhenHidden<T>(fetcher: () => Promise<T>): () => Promise<T> {
  return () => {
    if (document.visibilityState === 'hidden') {
      return new Promise((resolve) => {
        const handler = () => {
          if (document.visibilityState === 'visible') {
            document.removeEventListener('visibilitychange', handler);
            fetcher().then(resolve);
          }
        };
        document.addEventListener('visibilitychange', handler);
      });
    }
    return fetcher();
  };
}

export function useInstruments() {
  return useQuery({
    queryKey: ['instruments'],
    queryFn: pauseWhenHidden(() => api.instruments.list()),
    refetchInterval: REFRESH_INTERVAL,
    staleTime: 10_000,
  });
}

export function useInstrumentDecisions() {
  return useQuery({
    queryKey: ['instruments', 'decisions'],
    queryFn: pauseWhenHidden(() => api.instruments.decisions()),
    refetchInterval: REFRESH_INTERVAL,
    staleTime: 5_000,
  });
}

export function useAgents(params?: Parameters<typeof api.agents.status>[0]) {
  return useQuery({
    queryKey: ['agents', 'status', params],
    queryFn: pauseWhenHidden(() => api.agents.status(params)),
    refetchInterval: REFRESH_INTERVAL,
    staleTime: 5_000,
  });
}

export function useCycles(limit = 20) {
  return useQuery({
    queryKey: ['cycles', limit],
    queryFn: pauseWhenHidden(() => api.cycles.list(limit)),
    refetchInterval: REFRESH_INTERVAL,
    staleTime: 5_000,
  });
}

export function useLatestCycle() {
  return useQuery({
    queryKey: ['cycles', 'latest'],
    queryFn: pauseWhenHidden(async () => {
      const cycles = await api.cycles.list(1);
      return cycles[0] ?? null;
    }),
    refetchInterval: REFRESH_INTERVAL,
    staleTime: 5_000,
  });
}

export function useNews(params?: Parameters<typeof api.news.list>[0]) {
  return useQuery({
    queryKey: ['news', params],
    queryFn: pauseWhenHidden(() => api.news.list(params)),
    refetchInterval: REFRESH_INTERVAL * 2,
    staleTime: 30_000,
  });
}

export function useCalendar() {
  return useQuery({
    queryKey: ['news', 'calendar'],
    queryFn: pauseWhenHidden(() => api.news.calendar()),
    refetchInterval: REFRESH_INTERVAL * 5,
    staleTime: 60_000,
  });
}

export function useSignalsData(params?: Parameters<typeof api.signals.list>[0]) {
  return useQuery({
    queryKey: ['signals', 'data', params],
    queryFn: pauseWhenHidden(() => api.signals.list(params)),
    refetchInterval: REFRESH_INTERVAL,
    staleTime: 5_000,
  });
}

export function useStats(params?: Parameters<typeof api.stats.get>[0]) {
  return useQuery({
    queryKey: ['stats', params],
    queryFn: pauseWhenHidden(() => api.stats.get(params)),
    refetchInterval: REFRESH_INTERVAL * 2,
    staleTime: 30_000,
  });
}

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.health.get(),
    refetchInterval: 10_000,
    staleTime: 5_000,
  });
}
