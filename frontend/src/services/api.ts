// API base URL - direct to backend (CORS enabled)
const API_BASE = 'http://localhost:8000/api/trading';

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
  market_open: boolean;
  price_message: string;
  last_updated: string | null;
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
    return res.json();
  },

  // Signals
  async getSignals(): Promise<Signal[]> {
    const res = await fetch(`${API_BASE}/signals`);
    return res.json();
  },

  async createSignal(signal: Partial<Signal>): Promise<Signal> {
    const res = await fetch(`${API_BASE}/signals`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(signal)
    });
    return res.json();
  },

  // Approvals
  async approveTrade(signal_id: string, modifications?: any): Promise<any> {
    const res = await fetch(`${API_BASE}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ signal_id, ...modifications })
    });
    return res.json();
  },

  async rejectTrade(signal_id: string, reason?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ signal_id, reason })
    });
    return res.json();
  },

  // Execution
  async executeTrade(signal_id: string): Promise<Trade> {
    const res = await fetch(`${API_BASE}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ signal_id })
    });
    return res.json();
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
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async closeTrade(trade_id: string, exit_price: number, exit_reason: string): Promise<Trade> {
    const res = await fetch(`${API_BASE}/close`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trade_id, exit_price, exit_reason })
    });
    return res.json();
  },

  // Queries
  async getOpenTrades(): Promise<Trade[]> {
    const res = await fetch(`${API_BASE}/trades/open`);
    return res.json();
  },

  async getTradeHistory(): Promise<Trade[]> {
    const res = await fetch(`${API_BASE}/trades/history`);
    return res.json();
  },

  async getStats(): Promise<PerformanceStats> {
    const res = await fetch(`${API_BASE}/stats`);
    return res.json();
  },

  async getDashboard(): Promise<any> {
    const res = await fetch(`${API_BASE}/dashboard`);
    return res.json();
  },

  async getMonitoredTickers(): Promise<string[]> {
    const res = await fetch(`${API_BASE}/monitor/tickers`);
    const data = await res.json();
    return data.tickers ?? [];
  },

  async setMonitoredTickers(tickers: string[]): Promise<string[]> {
    const res = await fetch(`${API_BASE}/monitor/tickers`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tickers })
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    return data.tickers ?? [];
  },

  async getMonitorOverview(): Promise<MonitorItem[]> {
    const res = await fetch(`${API_BASE}/monitor/overview`);
    return res.json();
  },

  async getQuote(symbol: string): Promise<TickerQuote> {
    const res = await fetch(`${API_BASE}/quote/${symbol}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getMonitorHistory(symbol: string, interval = '1d', period = '6mo', limit = 120): Promise<TickerHistory> {
    const res = await fetch(`${API_BASE}/monitor/history/${symbol}?interval=${interval}&period=${period}&limit=${limit}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }
};
