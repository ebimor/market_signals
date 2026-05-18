import React, { useState } from 'react';
import { Signal } from '../services/api';
import '../styles/SignalReview.css';

interface SignalReviewProps {
  signals: Signal[];
  onApprove: (signal_id: string, mods?: any) => void;
  onReject: (signal_id: string) => void;
  loading: boolean;
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
              <small>{signal.reason}</small>
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
