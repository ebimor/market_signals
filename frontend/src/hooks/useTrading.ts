import { useState, useEffect } from 'react';
import { api, Signal, Trade, PerformanceStats, SystemStatus } from '../services/api';

export function useTrading() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [openTrades, setOpenTrades] = useState<Trade[]>([]);
  const [tradeHistory, setTradeHistory] = useState<Trade[]>([]);
  const [stats, setStats] = useState<PerformanceStats | null>(null);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshAll = async (options?: { silent?: boolean }) => {
    const silent = options?.silent ?? false;
    if (!silent) setLoading(true);
    setError(null);
    try {
      const [s, o, h, st, st2] = await Promise.all([
        api.getSignals(),
        api.getOpenTrades(),
        api.getTradeHistory(),
        api.getStats(),
        api.getStatus()
      ]);
      setSignals(s);
      setOpenTrades(o);
      setTradeHistory(h);
      setStats(st);
      setStatus(st2);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    refreshAll();
    // Poll every 5 seconds
    const interval = setInterval(() => refreshAll({ silent: true }), 5000);
    return () => clearInterval(interval);
  }, []);

  const approveTrade = async (signal_id: string, mods?: any) => {
    await api.approveTrade(signal_id, mods);
    await refreshAll();
  };

  const rejectTrade = async (signal_id: string, reason?: string) => {
    await api.rejectTrade(signal_id, reason);
    await refreshAll();
  };

  const executeTrade = async (signal_id: string) => {
    await api.executeTrade(signal_id);
    await refreshAll();
  };

  const closeTrade = async (trade_id: string, exit_price: number, exit_reason: string) => {
    await api.closeTrade(trade_id, exit_price, exit_reason);
    await refreshAll();
  };

  return {
    signals,
    openTrades,
    tradeHistory,
    stats,
    status,
    loading,
    error,
    refreshAll,
    approveTrade,
    rejectTrade,
    executeTrade,
    closeTrade
  };
}
