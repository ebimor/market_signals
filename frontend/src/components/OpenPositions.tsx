import React from 'react';
import { SystemStatus, Trade } from '../services/api';
import '../styles/OpenPositions.css';

interface OpenPositionsProps {
  trades: Trade[];
  status: SystemStatus | null;
}

export const OpenPositions: React.FC<OpenPositionsProps> = ({ trades, status: _status }) => {
  if (trades.length === 0) {
    return (
      <div className="open-positions">
        <h2>Open Positions</h2>
        <p className="no-data">No open positions</p>
      </div>
    );
  }

  return (
    <div className="open-positions">
      <h2>Open Positions ({trades.length})</h2>
      <div className="positions-list">
        {trades.map(trade => (
          <div key={trade.trade_id} className="position-card">
            <div className="position-header">
              <h3>{trade.symbol}</h3>
              <span className="position-size">{trade.position_size} shares</span>
            </div>
            <div className="position-details">
              <div className="detail">
                <label>Entry:</label>
                <span>${trade.entry_price.toFixed(2)}</span>
              </div>
              <div className="detail">
                <label>SL:</label>
                <span>${trade.stop_loss.toFixed(2)}</span>
              </div>
              <div className="detail">
                <label>TP:</label>
                <span>${trade.take_profit.toFixed(2)}</span>
              </div>
            </div>
            <div className="progress-bars">
              <div className="progress-label">Distance to TP: ${(trade.take_profit - trade.entry_price).toFixed(2)}</div>
              <div className="progress-label">Distance to SL: ${(trade.entry_price - trade.stop_loss).toFixed(2)}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
