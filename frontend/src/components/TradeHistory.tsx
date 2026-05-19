import React, { useMemo, useState } from 'react';
import { api, Trade } from '../services/api';
import '../styles/TradeHistory.css';

interface TradeHistoryProps {
  trades: Trade[];
  onDeleted?: () => Promise<void> | void;
}

export const TradeHistory: React.FC<TradeHistoryProps> = ({ trades, onDeleted }) => {
  const [sortKey, setSortKey] = useState<'position_size' | 'entry_date' | 'exit_date' | 'pnl'>('exit_date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [deletingTradeId, setDeletingTradeId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sortedTrades = useMemo(() => {
    const valueForSort = (trade: Trade) => {
      switch (sortKey) {
        case 'position_size':
          return trade.position_size;
        case 'entry_date':
          return new Date(trade.entry_date).getTime();
        case 'exit_date':
          return trade.exit_date ? new Date(trade.exit_date).getTime() : Number.NEGATIVE_INFINITY;
        case 'pnl':
          return trade.pnl ?? Number.NEGATIVE_INFINITY;
        default:
          return 0;
      }
    };

    const directionMultiplier = sortDirection === 'asc' ? 1 : -1;

    return [...trades].sort((left, right) => {
      const leftValue = valueForSort(left);
      const rightValue = valueForSort(right);

      if (leftValue < rightValue) return -1 * directionMultiplier;
      if (leftValue > rightValue) return 1 * directionMultiplier;
      return 0;
    });
  }, [trades, sortKey, sortDirection]);

  const handleSort = (key: typeof sortKey) => {
    if (sortKey === key) {
      setSortDirection(current => (current === 'asc' ? 'desc' : 'asc'));
      return;
    }

    setSortKey(key);
    setSortDirection(key === 'exit_date' || key === 'pnl' ? 'desc' : 'asc');
  };

  const sortLabel = (key: typeof sortKey, label: string) => {
    const active = sortKey === key;
    const arrow = active ? (sortDirection === 'asc' ? ' ▲' : ' ▼') : ' ↕';
    return `${label}${arrow}`;
  };

  const handleDelete = async (trade: Trade) => {
    const confirmed = window.confirm(`Delete ${trade.symbol} from trade history? This cannot be undone.`);
    if (!confirmed) return;

    setDeletingTradeId(trade.trade_id);
    setError(null);

    try {
      await api.deleteTradeHistoryEntry(trade.trade_id);
      await onDeleted?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete trade history entry');
    } finally {
      setDeletingTradeId(null);
    }
  };

  if (trades.length === 0) {
    return (
      <div className="trade-history">
        <h2>Trade History</h2>
        <p className="no-data">No closed trades yet</p>
      </div>
    );
  }

  return (
    <div className="trade-history">
      <h2>Trade History ({trades.length})</h2>
      {error && <div className="trade-history-error">⚠️ {error}</div>}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Entry Price</th>
              <th>Exit Price</th>
              <th>
                <button className="sort-header" type="button" onClick={() => handleSort('position_size')}>
                  {sortLabel('position_size', 'Position')}
                </button>
              </th>
              <th>
                <button className="sort-header" type="button" onClick={() => handleSort('entry_date')}>
                  {sortLabel('entry_date', 'Entry Date')}
                </button>
              </th>
              <th>
                <button className="sort-header" type="button" onClick={() => handleSort('exit_date')}>
                  {sortLabel('exit_date', 'Exit Date')}
                </button>
              </th>
              <th>
                <button className="sort-header" type="button" onClick={() => handleSort('pnl')}>
                  {sortLabel('pnl', 'P&L')}
                </button>
              </th>
              <th>Return %</th>
              <th>Reason</th>
              <th>Delete</th>
            </tr>
          </thead>
          <tbody>
            {sortedTrades.map(trade => (
              <tr key={trade.trade_id} className={trade.pnl! >= 0 ? 'profit' : 'loss'}>
                <td className="symbol">{trade.symbol}</td>
                <td>${trade.entry_price.toFixed(2)}</td>
                <td>${trade.exit_price?.toFixed(2) ?? '-'}</td>
                <td>{trade.position_size}</td>
                <td>{new Date(trade.entry_date).toLocaleDateString()}</td>
                <td>{trade.exit_date ? new Date(trade.exit_date).toLocaleDateString() : '-'}</td>
                <td className={`pnl ${trade.pnl! >= 0 ? 'positive' : 'negative'}`}>
                  ${trade.pnl?.toFixed(2) ?? 0}
                </td>
                <td className={`return ${trade.pnl_percent! >= 0 ? 'positive' : 'negative'}`}>
                  {trade.pnl_percent?.toFixed(2) ?? 0}%
                </td>
                <td className="reason">{trade.exit_reason || '-'}</td>
                <td>
                  <button
                    type="button"
                    className="delete-trade-btn"
                    onClick={() => handleDelete(trade)}
                    disabled={deletingTradeId === trade.trade_id}
                    title="Delete this history entry"
                  >
                    {deletingTradeId === trade.trade_id ? 'Deleting...' : 'Delete'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
