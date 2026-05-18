import React, { useEffect, useMemo, useState } from 'react';
import { api, HistoricalBar, MonitorItem } from '../services/api';
import '../styles/TickerMonitor.css';

export const TickerMonitor: React.FC = () => {
  const [tickersInput, setTickersInput] = useState('');
  const [items, setItems] = useState<MonitorItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoricalBar[]>([]);

  const loadAll = async (options?: { silent?: boolean }) => {
    const silent = options?.silent ?? false;
    if (!silent) setLoading(true);
    setError(null);
    try {
      const [tickers, overview] = await Promise.all([
        api.getMonitoredTickers(),
        api.getMonitorOverview()
      ]);
      setTickersInput(tickers.join(', '));
      setItems(overview);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load ticker monitor');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
    const interval = setInterval(() => loadAll({ silent: true }), 10000);
    return () => clearInterval(interval);
  }, []);

  const selected = useMemo(
    () => items.find(i => i.symbol === hovered) || items[0] || null,
    [items, hovered]
  );

  useEffect(() => {
    if (!selected?.symbol) {
      setHistory([]);
      return;
    }

    let canceled = false;
    api.getMonitorHistory(selected.symbol, '1d', '6mo', 30)
      .then((resp) => {
        if (!canceled) setHistory(resp.bars ?? []);
      })
      .catch(() => {
        if (!canceled) setHistory([]);
      });

    return () => { canceled = true; };
  }, [selected?.symbol]);

  const handleSave = async () => {
    const tickers = tickersInput
      .split(',')
      .map(t => t.trim().toUpperCase())
      .filter(Boolean);

    setSaving(true);
    setError(null);
    try {
      await api.setMonitoredTickers(tickers);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save tickers');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="ticker-monitor">
      <div className="ticker-monitor-head">
        <h2>🎯 Monitored Tickers</h2>
        <p>Only these symbols are monitored for signal conditions.</p>
      </div>

      <div className="ticker-config-row">
        <input
          value={tickersInput}
          onChange={(e) => setTickersInput(e.target.value)}
          placeholder="AAPL, MSFT, TSLA"
          className="ticker-input"
        />
        <button onClick={handleSave} disabled={saving} className="ticker-save-btn">
          {saving ? 'Saving...' : 'Update List'}
        </button>
      </div>

      {error && <div className="ticker-error">⚠️ {error}</div>}
      {loading && <div className="ticker-loading">Loading monitor...</div>}

      <div className="ticker-cards">
        {items.map(item => (
          <div
            key={item.symbol}
            className={`ticker-card ${item.signal.toLowerCase()} ${hovered === item.symbol ? 'active' : ''}`}
            onMouseEnter={() => setHovered(item.symbol)}
          >
            <div className="ticker-top-row">
              <strong>{item.symbol}</strong>
              <span className={`signal-pill ${item.signal.toLowerCase()}`}>{item.signal}</span>
            </div>
            <div className="ticker-condition">{item.condition}</div>
            <div className="ticker-confidence">Confidence: {item.confidence.toFixed(0)}%</div>
          </div>
        ))}
      </div>

      {selected && (
        <div className="ticker-detail-panel">
          <h3>{selected.symbol} — Current Condition</h3>
          <div className="detail-line"><span>Signal:</span> {selected.signal} ({selected.confidence.toFixed(1)}%)</div>
          <div className="detail-line"><span>Condition:</span> {selected.condition}</div>
          <div className="detail-line"><span>Suggested Action:</span> {selected.action}</div>
          <div className="detail-line">
            <span>Price:</span>{' '}
            {selected.price !== null ? `$${selected.price.toFixed(2)}` : 'N/A'}
            {' '}<em>({selected.price_message})</em>
          </div>
          {selected.last_updated && (
            <div className="detail-line"><span>Latest Update:</span> {new Date(selected.last_updated).toLocaleString()}</div>
          )}

          <div className="history-block">
            <div className="history-title">Recent Historical Closes</div>
            {history.length === 0 ? (
              <div className="history-empty">No historical bars available.</div>
            ) : (
              <div className="history-list">
                {history.slice(-10).reverse().map((bar) => (
                  <div key={bar.timestamp} className="history-row">
                    <span>{new Date(bar.timestamp).toLocaleDateString()}</span>
                    <strong>${bar.close.toFixed(2)}</strong>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
