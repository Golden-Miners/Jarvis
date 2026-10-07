/** Price formatting with symbol-specific decimal places. */
export function formatPrice(price: number | null | undefined, digits = 2): string {
  if (price == null) return '—';
  return price.toFixed(digits);
}

/** Format a Signal's copy text exactly per Dashboard_Layout.md s4.6. */
export function formatSignalCopyText(signal: {
  symbol: string;
  direction: string | null;
  entry: number | null;
  sl: number | null;
  tp: number | null;
  rr: number | null;
  confidence: number;
  expires_at: string;
}): string {
  const dir = signal.direction?.toUpperCase() ?? '';
  const entry = formatPrice(signal.entry);
  const sl = formatPrice(signal.sl);
  const tp = formatPrice(signal.tp);
  const rr = signal.rr?.toFixed(1) ?? '—';
  const conf = Math.round(signal.confidence * 100);
  const expires = signal.expires_at
    ? new Date(signal.expires_at).toISOString().replace('T', ' ').slice(0, 16) + ' UTC'
    : '';
  return `${signal.symbol} ${dir} | Entry ${entry} | SL ${sl} | TP ${tp} | RR ${rr} | Conf ${conf}% | expires ${expires} | not financial advice`;
}

/** Copy text to clipboard. */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

/** "x ago" string from Date. */
export function formatTimeAgo(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const seconds = Math.floor((Date.now() - d.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

/** Local time string with UTC tooltip. */
export function formatLocalTime(isoString: string): string {
  const d = new Date(isoString);
  const local = d.toLocaleString();
  const utc = d.toISOString();
  return `${local} (${utc} UTC)`;
}

/** Countdown string from expiry ISO string. */
export function formatCountdown(expiresAt: string): string {
  const d = new Date(expiresAt);
  const ms = d.getTime() - Date.now();
  if (ms <= 0) return 'expired';
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  if (minutes >= 60) {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return `${h}h ${m}m`;
  }
  return `${minutes}m ${seconds}s`;
}

/** NO_TRADE reason code → plain language (Dashboard_Layout.md s8). */
const NO_TRADE_MAP: Record<string, string> = {
  NEWS_BLACKOUT: 'News blackout',
  CONFLICT: 'Strategies disagree',
  RR_LOW: 'Risk/reward below minimum',
  SCORE_LOW: 'Not enough confluence',
  MIN_ALIGNED: 'Fewer than 2 strategies aligned',
  DATA_STALE: 'Market data stale',
  RISK_INVALID: 'Risk check failed',
  FORECAST_OPPOSITE: 'Forecast disagrees',
  DUPLICATE_OPEN: 'Signal already open',
  DAILY_CAP: 'Daily signal limit reached',
};

export function formatNoTradeReason(reason: string | null | undefined): string {
  if (!reason) return '';
  // Handle DEGRADED:{agent} format
  if (reason.startsWith('DEGRADED:')) {
    const agent = reason.slice(9);
    return `${agent} unavailable`;
  }
  return NO_TRADE_MAP[reason] ?? reason;
}

/** Agent name snake_case → Title Case. */
export function formatAgentName(name: string): string {
  return name
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

/** Format latency in ms. */
export function formatLatency(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

/** Format confidence as ring percentage string. */
export function formatConfidence(conf: number): string {
  return `${Math.round(conf * 100)}%`;
}
