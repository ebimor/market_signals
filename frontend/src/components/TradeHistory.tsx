import React from 'react';
import { Trade } from '../services/api';
import '../styles/TradeHistory.css';

interface TradeHistoryProps {
  trades: Trade[];
}

export const TradeHistory: React.FC<TradeHistoryProps> = ({ trades }) => {
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
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Entry Price</th>
              <th>Exit Price</th>
              <th>Position</th>
              <th>Entry Date</th>
              <th>Exit Date</th>
              <th>P&L</th>
              <th>Return %</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {trades.map(trade => (
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
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
