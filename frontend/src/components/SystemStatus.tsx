import React from 'react';
import { SystemStatus } from '../services/api';
import '../styles/SystemStatus.css';

interface SystemStatusProps {
  status: SystemStatus | null;
}

export const SystemStatusComponent: React.FC<SystemStatusProps> = ({ status }) => {
  if (!status) {
    return (
      <div className="system-status loading">
        <div className="status-indicator">⏳ INITIALIZING</div>
      </div>
    );
  }

  return (
    <div className="system-status">
      <div className="status-top">
        <div className={`status-indicator ${status.status.toLowerCase()}`}>
          {status.status === 'running' ? '🟢' : '🔴'} {status.status.toUpperCase()}
        </div>
        <div className="status-time" title="Last status update">
          {new Date(status.timestamp).toLocaleTimeString()}
        </div>
      </div>

      <div className="status-metrics">
        <div className="metric-chip">
          <span className="metric-label">Pending</span>
          <span className="metric-value">{status.pending_signals}</span>
        </div>
        <div className="metric-chip">
          <span className="metric-label">Open</span>
          <span className="metric-value">{status.open_trades}</span>
        </div>
        <div className="metric-chip">
          <span className="metric-label">Closed</span>
          <span className="metric-value">{status.closed_trades}</span>
        </div>
        <div className="metric-chip total">
          <span className="metric-label">Total</span>
          <span className="metric-value">{status.total_trades}</span>
        </div>
      </div>
    </div>
  );
};
