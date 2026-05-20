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
      const [s, o, h, st, st2] = await Promise.allSettled([
        api.getSignals(),
        api.getOpenTrades(),
        api.getTradeHistory(),
        api.getStats(),
        api.getStatus()
      ]);

      if (s.status === 'fulfilled') setSignals(s.value);
      if (o.status === 'fulfilled') setOpenTrades(o.value);
      if (h.status === 'fulfilled') setTradeHistory(h.value);
      if (st.status === 'fulfilled') setStats(st.value);
      if (st2.status === 'fulfilled') setStatus(st2.value);

      const failures = [s, o, h, st, st2].filter(r => r.status === 'rejected') as PromiseRejectedResult[];
      if (failures.length > 0) {
        const firstReason = failures[0]?.reason;
        const message = firstReason instanceof Error ? firstReason.message : String(firstReason ?? 'Unknown error');
        setError(`Some data failed to load (${failures.length}/5): ${message}`);
      }
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
