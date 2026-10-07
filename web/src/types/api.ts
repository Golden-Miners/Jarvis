export type Direction = 'BUY' | 'SELL';
export type Decision = 'TRADE' | 'NO_TRADE';
export type SignalStatus = 'OPEN' | 'TP_HIT' | 'SL_HIT' | 'EXPIRED' | 'SKIPPED';
export type Bias = 'BULLISH' | 'BEARISH' | 'NEUTRAL';
export type ForecastDirection = 'UP' | 'DOWN' | 'FLAT';
export type VolatilityRegime = 'LOW' | 'NORMAL' | 'HIGH';

export interface MarketStructure {
  symbol: string;
  timeframe_trends: Record<string, 'UP' | 'DOWN' | 'RANGE'>;
  last_bos: { level: number; direction: 'UP' | 'DOWN'; kind: 'BOS' | 'CHOCH'; timestamp: string } | null;
  last_choch: { level: number; direction: 'UP' | 'DOWN'; kind: 'BOS' | 'CHOCH'; timestamp: string } | null;
  key_levels: number[];
  atr: Record<string, number>;
  volatility_regime: VolatilityRegime;
  session: string;
}

export interface NewsImpact {
  id?: string;
  source?: string;
  url?: string;
  symbol: string;
  bias: Bias;
  impact: number;
  blackout_until: string | null;
  published_at?: string;
  events: Record<string, unknown>[];
  summary: string;
}

export interface Forecast {
  symbol: string;
  horizon_bars: number;
  timeframe: string;
  median: number[];
  q10: number[];
  q90: number[];
  expected_direction: ForecastDirection;
  strength: number;
}

export interface SetupCandidate {
  symbol: string;
  strategy: string;
  agent: string;
  direction: Direction;
  entry: number;
  sl: number;
  tp: number;
  confidence: number;
  evidence: string[];
  created_at: string;
}

export interface RiskAssessment {
  candidate_id: string;
  valid: boolean;
  rr: number;
  sl_atr_mult: number;
  spread_ok: boolean;
  suggested_lot: number | null;
  issues: string[];
}

export interface Signal {
  id: string;
  symbol: string;
  decision: Decision;
  direction: Direction | null;
  entry: number | null;
  sl: number | null;
  tp: number | null;
  rr: number | null;
  confidence: number;
  score: number;
  score_breakdown: Record<string, number>;
  agent_verdicts: Record<string, string>;
  rationale: string;
  status: SignalStatus;
  created_at: string;
  expires_at: string;
  no_trade_reason?: string;
}

export interface AgentStatus {
  agent: string;
  symbol: string | null;
  last_run: string;
  latency_ms: number;
  status: 'OK' | 'DEGRADED' | 'ERROR' | 'SKIPPED';
  error?: string;
}

export interface CycleInfo {
  id: string;
  status: 'RUNNING' | 'COMPLETED' | 'DEGRADED' | 'FAILED';
  started_at: string;
  finished_at: string | null;
  duration_ms: number | null;
}

export interface StatsData {
  total_signals: number;
  win_rate: number;
  avg_rr: number;
  expectancy: number;
  by_strategy: Record<string, { win_rate: number; avg_rr: number; count: number }>;
  by_instrument: Record<string, { win_rate: number; avg_rr: number; count: number }>;
}

export interface APIResponse<T> {
  data: T;
  error?: string;
}