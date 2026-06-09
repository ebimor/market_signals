// API base URL - prefer same-origin proxy to avoid localhost/network mismatch in browser
const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined)?.trim() || '/api/trading';

async function parseResponse<T>(res: Response): Promise<T> {
  const raw = await res.text();
  const contentType = (res.headers.get('content-type') || '').toLowerCase();
  const looksLikeJson = contentType.includes('application/json') || raw.trim().startsWith('{') || raw.trim().startsWith('[');

  let data: any = null;
  if (looksLikeJson && raw.trim()) {
    try {
      data = JSON.parse(raw);
    } catch {
      if (res.ok) {
        throw new Error(`Server returned invalid JSON: ${raw.slice(0, 160)}`);
      }
    }
  }

  if (!res.ok) {
    const message =
      data?.detail ||
      data?.message ||
      (raw ? raw.split('\n')[0].slice(0, 200) : '') ||
      `Request failed (${res.status})`;
    throw new Error(message);
  }

  return (data as T);
}

export interface Signal {
  signal_id: string;
  symbol: string;
  type: 'BUY' | 'SELL' | 'EXIT';
  price: number;
  confidence: number;
  reason: string;
  position_size: number;
  stop_loss: number;
  take_profit: number;
  atr?: number;
  timestamp?: string;
}

export interface Trade {
  trade_id: string;
  symbol: string;
  entry_price: number;
  entry_date: string;
  position_size: number;
  stop_loss: number;
  take_profit: number;
  status: 'executed' | 'closed';
  exit_price?: number;
  exit_date?: string;
  exit_reason?: string;
  pnl?: number;
  pnl_percent?: number;
  notes?: string;
}

export interface TickerQuote {
  symbol: string;
  price: number | null;
  source: 'live' | 'latest_close' | 'latest' | 'unavailable';
  data_provider: string;
  market_open: boolean;
  message: string;
  last_updated: string | null;
}

export interface MonitorItem {
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  condition: string;
  action: string;
  price: number | null;
  price_source: 'live' | 'latest_close' | 'latest' | 'unavailable';
  data_provider: string;
  market_open: boolean;
  price_message: string;
  last_updated: string | null;
  price_change: number | null;
  price_change_pct: number | null;
  signal_metrics: SignalMetric[];
  suggested_stop_loss?: number | null;
  suggested_take_profit?: number | null;
}

export interface SignalMetric {
  name: string;
  current: number | null;
  low_trigger: number;
  high_trigger: number;
  unit: string;
  trigger_mode?: 'outside_range' | 'max_value' | 'min_value';
  daily_change_pct?: number | null;
  description: string;
}

export interface HistoricalBar {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
}

export interface TickerHistory {
  symbol: string;
  interval: string;
  bars: HistoricalBar[];
  source: string;
}

export interface RsiSeriesPoint {
  timestamp: string;
  value: number;
}

export interface RsiTimeframeSeries {
  interval: string;
  points: RsiSeriesPoint[];
  latest: number | null;
}

export interface DrawdownInfo {
  all_time_high: number | null;
  all_time_high_date: string | null;
  current: number | null;
  drawdown_pct: number | null;
  is_down: boolean;
}

export interface TickerAnalysis {
  symbol: string;
  rsi_4h: RsiTimeframeSeries;
  rsi_weekly: RsiTimeframeSeries;
  drawdown: DrawdownInfo;
}

export interface PerformanceStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  avg_pnl: number;
  best_trade: number;
  worst_trade: number;
  total_exposure: number;
  current_cash: number;
}

export interface SystemStatus {
  status: string;
  pending_signals: number;
  open_trades: number;
  closed_trades: number;
  total_trades: number;
  timestamp: string;
}

// API Functions
export const api = {
  // Status
  async getStatus(): Promise<SystemStatus> {
    const res = await fetch(`${API_BASE}/status`);
    return parseResponse<SystemStatus>(res);
  },

  // Signals
  async getSignals(): Promise<Signal[]> {
    const res = await fetch(`${API_BASE}/signals`);
    return parseResponse<Signal[]>(res);
  },

  async createSignal(signal: Partial<Signal>): Promise<Signal> {
    const res = await fetch(`${API_BASE}/signals`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(signal)
    });
    return parseResponse<Signal>(res);
  },

  // Approvals
  async approveTrade(signal_id: string, modifications?: any): Promise<any> {
    const res = await fetch(`${API_BASE}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ signal_id, ...modifications })
    });
    return parseResponse<any>(res);
  },

  async rejectTrade(signal_id: string, reason?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ signal_id, reason })
    });
    return parseResponse<any>(res);
  },

  // Execution
  async executeTrade(signal_id: string): Promise<Trade> {
    const res = await fetch(`${API_BASE}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ signal_id })
    });
    return parseResponse<Trade>(res);
  },

  async manualTrade(data: {
    symbol: string;
    signal_type: 'BUY' | 'SELL';
    entry_price: number;
    position_size: number;
    stop_loss?: number;
    take_profit?: number;
    notes?: string;
  }): Promise<Trade> {
    const res = await fetch(`${API_BASE}/manual`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return parseResponse<Trade>(res);
  },

  async closeTrade(trade_id: string, exit_price: number, exit_reason: string): Promise<Trade> {
    const res = await fetch(`${API_BASE}/close`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trade_id, exit_price, exit_reason })
    });
    return parseResponse<Trade>(res);
  },

  // Queries
  async getOpenTrades(): Promise<Trade[]> {
    const res = await fetch(`${API_BASE}/trades/open`);
    return parseResponse<Trade[]>(res);
  },

  async getTradeHistory(): Promise<Trade[]> {
    const res = await fetch(`${API_BASE}/trades/history`);
    return parseResponse<Trade[]>(res);
  },

  async deleteTradeHistoryEntry(trade_id: string): Promise<{ message: string; trade_id: string }> {
    const res = await fetch(`${API_BASE}/trades/history/${trade_id}`, {
      method: 'DELETE'
    });
    return parseResponse<{ message: string; trade_id: string }>(res);
  },

  async getStats(): Promise<PerformanceStats> {
    const res = await fetch(`${API_BASE}/stats`);
    return parseResponse<PerformanceStats>(res);
  },

  async getDashboard(): Promise<any> {
    const res = await fetch(`${API_BASE}/dashboard`);
    return parseResponse<any>(res);
  },

  async getMonitoredTickers(): Promise<string[]> {
    const res = await fetch(`${API_BASE}/monitor/tickers`);
    const data = await parseResponse<{ tickers?: string[] }>(res);
    return data.tickers ?? [];
  },

  async setMonitoredTickers(tickers: string[]): Promise<string[]> {
    const res = await fetch(`${API_BASE}/monitor/tickers`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tickers })
    });
    const data = await parseResponse<{ tickers?: string[] }>(res);
    return data.tickers ?? [];
  },

  async getMonitorOverview(): Promise<MonitorItem[]> {
    const res = await fetch(`${API_BASE}/monitor/overview`);
    return parseResponse<MonitorItem[]>(res);
  },

  async getQuote(symbol: string): Promise<TickerQuote> {
    const res = await fetch(`${API_BASE}/quote/${symbol}`);
    return parseResponse<TickerQuote>(res);
  },

  async getMonitorHistory(symbol: string, interval = '1d', period = '6mo', limit = 120): Promise<TickerHistory> {
    const res = await fetch(`${API_BASE}/monitor/history/${symbol}?interval=${interval}&period=${period}&limit=${limit}`);
    return parseResponse<TickerHistory>(res);
  },

  async getMonitorAnalysis(symbol: string): Promise<TickerAnalysis> {
    const res = await fetch(`${API_BASE}/monitor/analysis/${symbol}`);
    return parseResponse<TickerAnalysis>(res);
  }
};
