import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { api, type SSEEventMap } from '@/lib/api';

export type SSEConnectionState = 'connecting' | 'live' | 'reconnecting' | 'offline';

const RECONNECT_BASE_DELAY_MS = 1_000;
const RECONNECT_MAX_DELAY_MS = 30_000;
const POLL_FALLBACK_INTERVAL_MS = 30_000;

export function useSSE() {
  const qc = useQueryClient();
  const [state, setState] = useState<SSEConnectionState>('connecting');
  const esRef = useRef<EventSource | null>(null);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const unmountedRef = useRef(false);

  const clearTimers = () => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
  };

  const invalidateRelated = useCallback((event: keyof SSEEventMap) => {
    switch (event) {
      case 'signal.created':
      case 'signal.updated':
        qc.invalidateQueries({ queryKey: ['signals'] });
        break;
      case 'cycle.status':
        qc.invalidateQueries({ queryKey: ['cycles'] });
        break;
      case 'agent.health':
        qc.invalidateQueries({ queryKey: ['agents'] });
        break;
    }
  }, [qc]);

  const subscribe = useCallback((es: EventSource) => {
    const events: Array<keyof SSEEventMap> = ['signal.created', 'signal.updated', 'cycle.status', 'agent.health'];

    for (const event of events) {
      const listener = (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          invalidateRelated(event);
          window.dispatchEvent(new CustomEvent(`sse:${event}`, { detail: data }));
        } catch { /* ignore */ }
      };
      es.addEventListener(event, listener);
    }

    es.addEventListener('open', () => {
      if (unmountedRef.current) return;
      reconnectAttemptRef.current = 0;
      setState('live');
    });

    es.addEventListener('error', () => {
      if (unmountedRef.current) return;
      es.close();
      esRef.current = null;

      const attempt = reconnectAttemptRef.current;
      const delay = Math.min(RECONNECT_BASE_DELAY_MS * 2 ** attempt, RECONNECT_MAX_DELAY_MS);
      reconnectAttemptRef.current = attempt + 1;

      setState('reconnecting');
      reconnectTimeoutRef.current = setTimeout(() => {
        if (unmountedRef.current) return;
        connect();
      }, delay);

      if (!pollIntervalRef.current) {
        pollIntervalRef.current = setInterval(() => {
          if (document.visibilityState === 'visible') qc.invalidateQueries();
        }, POLL_FALLBACK_INTERVAL_MS);
      }
    });
  }, [invalidateRelated, qc]);

  const connect = useCallback(() => {
    if (unmountedRef.current) return;
    try {
      const es = api.sse.connect();
      esRef.current = es;
      subscribe(es);
    } catch {
      setState('offline');
    }
  }, [subscribe]);

  useEffect(() => {
    unmountedRef.current = false;
    connect();
    return () => {
      unmountedRef.current = true;
      clearTimers();
      if (esRef.current) {
        esRef.current.close();
        esRef.current = null;
      }
    };
  }, [connect]);

  return { state, isLive: state === 'live', isReconnecting: state === 'reconnecting', isOffline: state === 'offline' };
}
