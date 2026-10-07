import type {
  Signal,
  NewsImpact,
  AgentStatus,
  CycleInfo,
  StatsData,
  MarketStructure,
  Forecast,
  SetupCandidate,
  RiskAssessment,
} from '@/types/api';

const API_BASE = '/api/v1';

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'include', // Send cookies
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const message = err?.detail ?? err?.message ?? `HTTP ${res.status}`;
    throw new APIError(res.status, message);
  }
  return res.json();
}

export class APIError extends Error {
  readonly status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'APIError';
    this.status = status;
  }
}

export interface Instrument {
  symbol: string;
  broker_symbol: string;
  agent_name: string;
  digits: number;
  point: number;
  enabled: boolean;
}

export interface InstrumentDecision {
  symbol: string;
  decision: string | null;
  direction: string | null;
  confidence: number | null;
  status: string | null;
}

export interface CalendarEvent {
  id: string;
  name: string;
  currency: string;
  importance: number;
  event_time: string;
  blackout_start: string | null;
  blackout_end: string | null;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  username: string;
  role: 'OWNER' | 'VIEWER';
}

export interface HealthStatus {
  status: string;
  adapters: Record<string, string>;
}

export interface SSEEventMap {
  'signal.created': { signal: Signal };
  'signal.updated': { signal: Signal };
  'cycle.status': { cycle: CycleInfo };
  'agent.health': { agent: AgentStatus };
}

export const api = {
  health: {
    get: () => fetchJson<HealthStatus>('/health'),
  },

  auth: {
    login: (username: string, password: string) =>
      fetchJson<LoginResponse>('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      }),
    logout: () =>
      fetchJson<{ message: string }>('/auth/logout', { method: 'POST' }),
    me: () => fetchJson<User>('/auth/me'),
    refresh: () => fetchJson<LoginResponse>('/auth/refresh', { method: 'POST' }),
  },

  instruments: {
    list: () => fetchJson<Instrument[]>('/instruments'),
    decisions: () => fetchJson<InstrumentDecision[]>('/instruments/decisions'),
    update: (symbol: string, enabled: boolean) =>
      fetchJson<Instrument>(`/instruments/${symbol}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      }),
  },

  signals: {
    list: (params?: { limit?: number; symbol?: string; status?: string; decision?: string; cursor?: string }) => {
      const qs = new URLSearchParams();
      if (params?.limit) qs.set('limit', String(params.limit));
      if (params?.symbol) qs.set('symbol', params.symbol);
      if (params?.status) qs.set('status', params.status);
      if (params?.decision) qs.set('decision', params.decision);
      if (params?.cursor) qs.set('cursor', params.cursor);
      const query = qs.toString();
      return fetchJson<{ data: Signal[]; next_cursor: string | null }>(
        `/signals${query ? `?${query}` : ''}`,
      );
    },
    get: (id: string) => fetchJson<Signal>(`/signals/${id}`),
    open: (symbol?: string) => {
      const qs = symbol ? `?symbol=${symbol}` : '';
      return fetchJson<{ data: Signal[]; next_cursor: string | null }>(`/signals/open${qs}`);
    },
  },

  agents: {
    status: (params?: { cycle_id?: string; agent?: string; limit?: number }) => {
      const qs = new URLSearchParams();
      if (params?.cycle_id) qs.set('cycle_id', params.cycle_id);
      if (params?.agent) qs.set('agent', params.agent);
      if (params?.limit) qs.set('limit', String(params.limit));
      const query = qs.toString();
      return fetchJson<AgentStatus[]>(`/agents/status${query ? `?${query}` : ''}`);
    },
  },

  cycles: {
    list: (limit = 20) => fetchJson<CycleInfo[]>(`/cycles?limit=${limit}`),
    get: (id: string) => fetchJson<CycleInfo>(`/cycles/${id}`),
    run: () =>
      fetchJson<{ id: string; status: string; message?: string }>('/cycles/run', {
        method: 'POST',
      }),
  },

  news: {
    list: (params?: { limit?: number; symbol?: string; cursor?: string }) => {
      const qs = new URLSearchParams();
      if (params?.limit) qs.set('limit', String(params.limit));
      if (params?.symbol) qs.set('symbol', params.symbol);
      if (params?.cursor) qs.set('cursor', params.cursor);
      const query = qs.toString();
      return fetchJson<{ data: NewsImpact[]; next_cursor: string | null }>(
        `/news${query ? `?${query}` : ''}`,
      );
    },
    forSymbol: (symbol: string, limit = 50) =>
      fetchJson<{ data: NewsImpact[]; next_cursor: string | null }>(
        `/news/${symbol}?limit=${limit}`,
      ),
    calendar: (limit = 100) =>
      fetchJson<{ data: CalendarEvent[]; next_cursor: string | null }>(
        `/news/calendar/events?limit=${limit}`,
      ),
  },

  stats: {
    get: (params?: { symbol?: string; strategy?: string }) => {
      const qs = new URLSearchParams();
      if (params?.symbol) qs.set('symbol', params.symbol);
      if (params?.strategy) qs.set('strategy', params.strategy);
      const query = qs.toString();
      return fetchJson<StatsData>(`/stats${query ? `?${query}` : ''}`);
    },
  },

  structure: {
    forSymbol: (symbol: string) => fetchJson<MarketStructure>(`/structure/${symbol}`),
  },

  forecast: {
    forSymbol: (symbol: string) => fetchJson<Forecast>(`/forecast/${symbol}`),
  },

  candidates: {
    forSymbol: (symbol: string) => fetchJson<SetupCandidate[]>(`/candidates/${symbol}`),
  },

  risk: {
    forSymbol: (symbol: string) => fetchJson<RiskAssessment[]>(`/risk/${symbol}`),
  },

  sse: {
    /**
     * Connect to SSE stream. Handles named events via addEventListener.
     * Returns the EventSource for cleanup.
     */
    connect(): EventSource {
      return new EventSource(`${API_BASE}/stream`, { withCredentials: true });
    },

    /**
     * Subscribe to a named SSE event.
     * @param es EventSource from connect()
     * @param event One of: signal.created | signal.updated | cycle.status | agent.health
     * @param handler Callback receiving the parsed data
     * @returns Unsubscribe function
     */
    on<K extends keyof SSEEventMap>(
      es: EventSource,
      event: K,
      handler: (data: SSEEventMap[K]) => void,
    ): () => void {
      const listener = (e: MessageEvent) => {
        try {
          const parsed = JSON.parse(e.data);
          handler(parsed as SSEEventMap[K]);
        } catch {
          // ignore parse errors
        }
      };
      es.addEventListener(event, listener);
      return () => es.removeEventListener(event, listener);
    },
  },
};
