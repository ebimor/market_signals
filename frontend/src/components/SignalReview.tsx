import React, { useState } from 'react';
import { Signal } from '../services/api';
import '../styles/SignalReview.css';

interface SignalReviewProps {
  signals: Signal[];
  onApprove: (signal_id: string, mods?: any) => void;
  onReject: (signal_id: string) => void;
  loading: boolean;
}

function getSuggestionAnalysis(signal: Signal): string[] {
  const reason = (signal.reason || '').toLowerCase();
  const lines: string[] = [];

  if (reason.includes('rsi')) {
    lines.push('RSI momentum contributed to this setup (overbought/oversold context).');
  }
  if (reason.includes('macd')) {
    lines.push('MACD trend/crossover confirmed directional momentum.');
  }
  if (reason.includes('bollinger') || reason.includes('bb')) {
    lines.push('Bollinger position suggests price is stretched or mean-reverting.');
  }
  if (reason.includes('ema') || reason.includes('moving average')) {
    lines.push('Price-vs-EMA trend alignment supported this suggestion.');
  }
  if (reason.includes('volume')) {
    lines.push('Volume behavior supported the move quality.');
  }

  const hasRisk = Number.isFinite(signal.stop_loss) && Number.isFinite(signal.take_profit) && Number.isFinite(signal.price);
  if (hasRisk) {
    if (signal.type === 'BUY') {
      const risk = Math.max(0, signal.price - signal.stop_loss).toFixed(2);
      const reward = Math.max(0, signal.take_profit - signal.price).toFixed(2);
      lines.push(`Risk/Reward setup: risk $${risk}, target reward $${reward}.`);
    } else if (signal.type === 'SELL') {
      const risk = Math.max(0, signal.stop_loss - signal.price).toFixed(2);
      const reward = Math.max(0, signal.price - signal.take_profit).toFixed(2);
      lines.push(`Risk/Reward setup: risk $${risk}, target reward $${reward}.`);
    }
  }

  if (lines.length === 0) {
    lines.push('Composite monitor conditions and confidence threshold triggered this suggestion.');
  }

  return lines;
}

export const SignalReview: React.FC<SignalReviewProps> = ({
  signals,
  onApprove,
  onReject,
  loading
}) => {
  const [modifications, setModifications] = useState<Record<string, any>>({});

  const handleApprove = (signal_id: string) => {
    const mods = modifications[signal_id];
    onApprove(signal_id, mods);
    setModifications(prev => ({ ...prev, [signal_id]: undefined }));
  };

  const handleModChange = (signal_id: string, field: string, value: any) => {
    setModifications(prev => ({
      ...prev,
      [signal_id]: { ...prev[signal_id], [field]: value }
    }));
  };

  if (signals.length === 0) {
    return (
      <div className="signal-review">
        <h2>Pending Signals</h2>
        <p className="no-data">No pending signals</p>
      </div>
    );
  }

  return (
    <div className="signal-review">
      <h2>Pending Signals ({signals.length})</h2>
      <div className="signals-list">
        {signals.map(signal => (
          <div key={signal.signal_id} className="signal-card">
            <div className="signal-header">
              <span className={`signal-type ${signal.type.toLowerCase()}`}>
                {signal.type}
              </span>
              <h3>{signal.symbol}</h3>
              <span className="confidence">{signal.confidence.toFixed(0)}%</span>
            </div>

            <div className="signal-details">
              <div className="detail-row">
                <label>Entry Price:</label>
                <span>${signal.price.toFixed(2)}</span>
              </div>
              <div className="detail-row">
                <label>Stop Loss:</label>
                <span>${signal.stop_loss.toFixed(2)}</span>
              </div>
              <div className="detail-row">
                <label>Take Profit:</label>
                <span>${signal.take_profit.toFixed(2)}</span>
              </div>
              <div className="detail-row">
                <label>Position:</label>
                <span>{signal.position_size} shares</span>
              </div>
            </div>

            <div className="signal-reason">
              <small><strong>Created suggestion:</strong> {signal.reason}</small>
              <ul className="signal-analysis-list">
                {getSuggestionAnalysis(signal).map((line, idx) => (
                  <li key={`${signal.signal_id}-analysis-${idx}`}>{line}</li>
                ))}
              </ul>
            </div>

            <div className="modifications">
              <label>
                Modify Position:
                <input
                  type="number"
                  value={modifications[signal.signal_id]?.position_size ?? signal.position_size}
                  onChange={(e) =>
                    handleModChange(signal.signal_id, 'position_size', parseFloat(e.target.value))
                  }
                  disabled={loading}
                />
              </label>
              <label>
                Modify SL:
                <input
                  type="number"
                  step="0.01"
                  value={modifications[signal.signal_id]?.stop_loss ?? signal.stop_loss}
                  onChange={(e) =>
                    handleModChange(signal.signal_id, 'stop_loss', parseFloat(e.target.value))
                  }
                  disabled={loading}
                />
              </label>
              <label>
                Modify TP:
                <input
                  type="number"
                  step="0.01"
                  value={modifications[signal.signal_id]?.take_profit ?? signal.take_profit}
                  onChange={(e) =>
                    handleModChange(signal.signal_id, 'take_profit', parseFloat(e.target.value))
                  }
                  disabled={loading}
                />
              </label>
            </div>

            <div className="signal-actions">
              <button
                className="btn btn-approve"
                onClick={() => handleApprove(signal.signal_id)}
                disabled={loading}
              >
                ✓ Approve
              </button>
              <button
                className="btn btn-reject"
                onClick={() => onReject(signal.signal_id)}
                disabled={loading}
              >
                ✗ Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
