import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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

export function useSignals(params?: Parameters<typeof api.signals.list>[0]) {
  return useQuery({
    queryKey: ['signals', params],
    queryFn: pauseWhenHidden(() => api.signals.list(params)),
    refetchInterval: REFRESH_INTERVAL,
    staleTime: 5_000,
  });
}

export function useOpenSignals(symbol?: string) {
  return useQuery({
    queryKey: ['signals', 'open', symbol],
    queryFn: pauseWhenHidden(() => api.signals.open(symbol)),
    refetchInterval: REFRESH_INTERVAL,
    staleTime: 5_000,
  });
}

export function useSignal(id: string) {
  return useQuery({
    queryKey: ['signals', id],
    queryFn: () => api.signals.get(id),
    enabled: !!id,
  });
}

export function useRunCycle() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.cycles.run(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cycles'] });
      qc.invalidateQueries({ queryKey: ['signals'] });
    },
  });
}
