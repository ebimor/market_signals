import React, { useEffect, useState } from 'react';
import { api, SystemStatus, TickerQuote, Trade } from '../services/api';
import '../styles/OpenPositions.css';

interface OpenPositionsProps {
  trades: Trade[];
  status: SystemStatus | null;
}

export const OpenPositions: React.FC<OpenPositionsProps> = ({ trades, status: _status }) => {
  const [quotes, setQuotes] = useState<Record<string, TickerQuote>>({});

  useEffect(() => {
    const symbols = Array.from(new Set(trades.map(t => t.symbol)));
    if (!symbols.length) {
      setQuotes({});
      return;
    }

    let canceled = false;
    Promise.all(
      symbols.map(async (symbol) => {
        try {
          const quote = await api.getQuote(symbol);
          return [symbol, quote] as const;
        } catch {
          return [symbol, {
            symbol,
            price: null,
            source: 'unavailable' as const,
            market_open: false,
            message: 'Price unavailable',
            last_updated: null,
          }] as const;
        }
      })
    ).then((pairs) => {
      if (canceled) return;
      setQuotes(Object.fromEntries(pairs));
    });

    return () => { canceled = true; };
  }, [trades]);

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
            {quotes[trade.symbol] && (
              <div className={`position-price-badge ${quotes[trade.symbol].source === 'live' ? 'live' : quotes[trade.symbol].source === 'latest_close' ? 'closed' : 'fallback'}`}>
                {quotes[trade.symbol].price !== null ? `$${quotes[trade.symbol].price!.toFixed(2)} · ` : ''}
                {quotes[trade.symbol].source === 'live' ? 'Live price' : quotes[trade.symbol].message}
              </div>
            )}
            <div className="position-details">
              <div className="detail">
                <label>Entry:</label>
                <span>${trade.entry_price.toFixed(2)}</span>
              </div>
              <div className="detail">
                <label>SL:</label>
                <span>{typeof trade.stop_loss === 'number' ? `$${trade.stop_loss.toFixed(2)}` : '—'}</span>
              </div>
              <div className="detail">
                <label>TP:</label>
                <span>{typeof trade.take_profit === 'number' ? `$${trade.take_profit.toFixed(2)}` : '—'}</span>
              </div>
            </div>
            <div className="progress-bars">
              <div className="progress-label">
                Distance to TP: {typeof trade.take_profit === 'number' ? `$${(trade.take_profit - trade.entry_price).toFixed(2)}` : 'N/A'}
              </div>
              <div className="progress-label">
                Distance to SL: {typeof trade.stop_loss === 'number' ? `$${(trade.entry_price - trade.stop_loss).toFixed(2)}` : 'N/A'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
