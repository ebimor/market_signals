import React from 'react';
import { PerformanceStats, Trade } from '../services/api';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import '../styles/PerformanceDashboard.css';

interface PerformanceDashboardProps {
  stats: PerformanceStats | null;
  trades: Trade[];
}

export const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({ stats, trades }) => {
  if (!stats) {
    return <div className="performance-dashboard"><p>Loading...</p></div>;
  }

  const pieData = [
    { name: 'Wins', value: stats.winning_trades, fill: '#10b981' },
    { name: 'Losses', value: stats.losing_trades, fill: '#ef4444' }
  ];

  const winningTrades = trades
    .filter(t => (t.pnl ?? 0) > 0)
    .sort((a, b) => (b.pnl ?? 0) - (a.pnl ?? 0))
    .slice(0, 5);

  const losingTrades = trades
    .filter(t => (t.pnl ?? 0) < 0)
    .sort((a, b) => (a.pnl ?? 0) - (b.pnl ?? 0))
    .slice(0, 5);

  const winningSum = winningTrades.reduce((sum, trade) => sum + (trade.pnl ?? 0), 0);
  const losingSum = losingTrades.reduce((sum, trade) => sum + (trade.pnl ?? 0), 0);

  return (
    <div className="performance-dashboard">
      <h2>Performance Analytics</h2>

      <div className="metrics-grid">
        <div className="metric-card">
          <h3>Current Cash</h3>
          <div className="metric-value">${stats.current_cash.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        </div>
        <div className="metric-card">
          <h3>Total Exposure</h3>
          <div className="metric-value" style={{ color: stats.total_exposure > 0 ? '#10b981' : 'inherit' }}>
            ${stats.total_exposure.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <div className="metric-card">
          <h3>Total Trades</h3>
          <div className="metric-value">{stats.total_trades}</div>
        </div>
        <div className="metric-card">
          <h3>Win Rate</h3>
          <div className="metric-value">{stats.win_rate.toFixed(1)}%</div>
        </div>
        <div className="metric-card">
          <h3>Total P&L</h3>
          <div className={`metric-value ${stats.total_pnl >= 0 ? 'positive' : 'negative'}`}>
            ${stats.total_pnl.toFixed(2)}
          </div>
        </div>
        <div className="metric-card">
          <h3>Avg P&L</h3>
          <div className={`metric-value ${stats.avg_pnl >= 0 ? 'positive' : 'negative'}`}>
            ${stats.avg_pnl.toFixed(2)}
          </div>
        </div>
      </div>

      <div className="charts-container">
        <div className="chart">
          <h3>Win/Loss Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart">
          <h3>Brief Winning & Losing Trades</h3>

          <div className="brief-tables">
            <div className="brief-table-card">
              <h4 className="brief-title win">Top Winners</h4>
              <table className="brief-table">
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>P&L</th>
                    <th>Return</th>
                  </tr>
                </thead>
                <tbody>
                  {winningTrades.length === 0 ? (
                    <tr><td colSpan={3} className="empty-cell">No winning trades</td></tr>
                  ) : (
                    winningTrades.map(trade => (
                      <tr key={trade.trade_id}>
                        <td>{trade.symbol}</td>
                        <td className="win-value">${(trade.pnl ?? 0).toFixed(2)}</td>
                        <td className="win-value">{(trade.pnl_percent ?? 0).toFixed(2)}%</td>
                      </tr>
                    ))
                  )}
                </tbody>
                <tfoot>
                  <tr className="sum-row">
                    <td className="sum-label">Sum</td>
                    <td className="win-value">${winningSum.toFixed(2)}</td>
                    <td className="sum-muted">—</td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <div className="brief-table-card">
              <h4 className="brief-title loss">Top Losers</h4>
              <table className="brief-table">
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>P&L</th>
                    <th>Return</th>
                  </tr>
                </thead>
                <tbody>
                  {losingTrades.length === 0 ? (
                    <tr><td colSpan={3} className="empty-cell">No losing trades</td></tr>
                  ) : (
                    losingTrades.map(trade => (
                      <tr key={trade.trade_id}>
                        <td>{trade.symbol}</td>
                        <td className="loss-value">${(trade.pnl ?? 0).toFixed(2)}</td>
                        <td className="loss-value">{(trade.pnl_percent ?? 0).toFixed(2)}%</td>
                      </tr>
                    ))
                  )}
                </tbody>
                <tfoot>
                  <tr className="sum-row">
                    <td className="sum-label">Sum</td>
                    <td className="loss-value">${losingSum.toFixed(2)}</td>
                    <td className="sum-muted">—</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
