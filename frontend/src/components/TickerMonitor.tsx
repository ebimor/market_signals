import React, { useEffect, useMemo, useState } from 'react';
import { api, HistoricalBar, MonitorItem } from '../services/api';
import '../styles/TickerMonitor.css';

export const TickerMonitor: React.FC = () => {
  type SortMode = 'signal_then_conf_desc' | 'conf_desc_then_signal' | 'signal_only' | 'confidence_only';

  const [tickersInput, setTickersInput] = useState('');
  const [draftTickers, setDraftTickers] = useState('');
  const [isEditingTickers, setIsEditingTickers] = useState(false);
  const [showTickerOptions, setShowTickerOptions] = useState(false);
  const [sortMode, setSortMode] = useState<SortMode>('signal_then_conf_desc');
  const [items, setItems] = useState<MonitorItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoricalBar[]>([]);
  const [refreshingTicker, setRefreshingTicker] = useState<string | null>(null);

  const loadAll = async (options?: { silent?: boolean }) => {
    const silent = options?.silent ?? false;
    if (!silent) setLoading(true);
    setError(null);
    try {
      const [tickers, overview] = await Promise.all([
        api.getMonitoredTickers(),
        api.getMonitorOverview()
      ]);
      const tickersText = tickers.join(', ');
      setTickersInput(tickersText);
      if (!isEditingTickers) {
        setDraftTickers(tickersText);
      }
      setItems(overview);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load ticker monitor');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  useEffect(() => {
    if (!items.length) {
      setSelectedSymbol(null);
      return;
    }

    const selectedStillExists = selectedSymbol && items.some(i => i.symbol === selectedSymbol);
    if (!selectedStillExists) {
      setSelectedSymbol(items[0].symbol);
    }
  }, [items, selectedSymbol]);

  const selected = useMemo(
    () => items.find(i => i.symbol === selectedSymbol) || items[0] || null,
    [items, selectedSymbol]
  );

  const sortedItems = useMemo(() => {
    const signalRank = (signal: MonitorItem['signal']) => {
      if (signal === 'BUY') return 0;
      if (signal === 'SELL') return 1;
      return 2;
    };

    const bySymbol = (a: MonitorItem, b: MonitorItem) => a.symbol.localeCompare(b.symbol);

    const sorted = [...items].sort((a, b) => {
      if (sortMode === 'signal_only') {
        const signalDiff = signalRank(a.signal) - signalRank(b.signal);
        if (signalDiff !== 0) return signalDiff;
        return bySymbol(a, b);
      }

      if (sortMode === 'confidence_only') {
        if (b.confidence !== a.confidence) return b.confidence - a.confidence;
        return bySymbol(a, b);
      }

      if (sortMode === 'conf_desc_then_signal') {
        if (b.confidence !== a.confidence) return b.confidence - a.confidence;
        const signalDiff = signalRank(a.signal) - signalRank(b.signal);
        if (signalDiff !== 0) return signalDiff;
        return bySymbol(a, b);
      }

      const signalDiff = signalRank(a.signal) - signalRank(b.signal);
      if (signalDiff !== 0) return signalDiff;
      if (b.confidence !== a.confidence) return b.confidence - a.confidence;
      return bySymbol(a, b);
    });

    return sorted;
  }, [items, sortMode]);

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
    const tickers = draftTickers
      .split(',')
      .map(t => t.trim().toUpperCase())
      .filter(Boolean);

    const confirmed = window.confirm(
      `Update monitored tickers to: ${tickers.join(', ')} ?\n\nThis changes the persistent monitored list.`
    );
    if (!confirmed) return;

    setSaving(true);
    setError(null);
    try {
      await api.setMonitoredTickers(tickers);
      setIsEditingTickers(false);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save tickers');
    } finally {
      setSaving(false);
    }
  };

  const handleRefreshTicker = async (symbol: string) => {
    setRefreshingTicker(symbol);
    try {
      const overview = await api.getMonitorOverview();
      const updated = overview.find(i => i.symbol === symbol);
      if (updated) {
        setItems(prev => prev.map(i => i.symbol === symbol ? updated : i));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to refresh ${symbol}`);
    } finally {
      setRefreshingTicker(null);
    }
  };

  const sourceLabel = (source: MonitorItem['price_source'], provider: string) => {
    const providerLabel = provider === 'questrade'
      ? 'Questrade'
      : provider === 'yahoo'
        ? 'Yahoo Finance'
        : provider === 'auto'
          ? 'Auto'
          : provider === 'none'
            ? 'Unavailable'
            : provider;

    if (source === 'live') return `${providerLabel} (Live)`;
    if (source === 'latest_close') return `${providerLabel} (Latest Close)`;
    if (source === 'latest') return `${providerLabel} (Latest)`;
    return 'Unavailable';
  };

  const isMetricTriggered = (current: number | null, low: number, high: number) => {
    if (current === null) return false;
    return current <= low || current >= high;
  };

  return (
    <div className="ticker-monitor">
      <div className="ticker-monitor-head">
        <div className="ticker-monitor-head-left">
          <h2>🎯 Monitored Tickers</h2>
          <p>Only these symbols are monitored for signal conditions.</p>
        </div>
        <button
          className="ticker-options-btn"
          onClick={() => setShowTickerOptions((prev) => !prev)}
          title="Manage monitored ticker list"
        >
          ⚙ List Options
        </button>
      </div>

      {showTickerOptions && (
        <div className="ticker-options-panel">
          <div className="ticker-options-title">Monitored List</div>
          {isEditingTickers ? (
            <div className="ticker-config-row">
              <input
                value={draftTickers}
                onChange={(e) => setDraftTickers(e.target.value)}
                placeholder="AAPL, MSFT, TSLA"
                className="ticker-input"
              />
              <button onClick={handleSave} disabled={saving} className="ticker-save-btn">
                {saving ? 'Saving...' : 'Save List'}
              </button>
              <button
                onClick={() => {
                  setIsEditingTickers(false);
                  setDraftTickers(tickersInput);
                }}
                disabled={saving}
                className="ticker-cancel-btn"
              >
                Cancel
              </button>
            </div>
          ) : (
            <>
              <div className="monitored-list" title="Current monitored tickers">
                {tickersInput
                  .split(',')
                  .map(t => t.trim())
                  .filter(Boolean)
                  .map((ticker) => (
                    <span key={ticker} className="ticker-chip">{ticker}</span>
                  ))}
              </div>
              <div className="ticker-options-actions">
                <button
                  onClick={() => {
                    setDraftTickers(tickersInput);
                    setIsEditingTickers(true);
                  }}
                  className="ticker-edit-btn"
                >
                  Edit List
                </button>
              </div>
            </>
          )}
          {!isEditingTickers && (
            <div className="ticker-list-meta">List is persistent. Use Edit List to make changes.</div>
          )}
          {isEditingTickers && (
            <div className="ticker-editing-note">Editing mode enabled — save to apply persistent changes.</div>
          )}
        </div>
      )}

      {error && <div className="ticker-error">⚠️ {error}</div>}
      {loading && <div className="ticker-loading">Loading monitor...</div>}

      <div className="ticker-layout">
        <div>
          <div className="ticker-sort-row">
            <label htmlFor="ticker-sort">Sort left pane:</label>
            <select
              id="ticker-sort"
              value={sortMode}
              onChange={(e) => setSortMode(e.target.value as SortMode)}
              className="ticker-sort-select"
            >
              <option value="signal_then_conf_desc">Signal → Confidence (high to low)</option>
              <option value="conf_desc_then_signal">Confidence (high to low) → Signal</option>
              <option value="signal_only">Signal only (BUY, SELL, HOLD)</option>
              <option value="confidence_only">Confidence only (high to low)</option>
            </select>
          </div>

        <div className="ticker-cards">
          {sortedItems.map(item => (
            <div
              key={item.symbol}
              className={`ticker-card ${item.signal.toLowerCase()} ${selectedSymbol === item.symbol ? 'active' : ''}`}
              onClick={() => setSelectedSymbol(item.symbol)}
            >
              <div className="ticker-top-row">
                <strong>{item.symbol}</strong>
                <span className={`signal-pill ${item.signal.toLowerCase()}`}>{item.signal}</span>
              </div>
              {item.price !== null && (
                <div className="ticker-price">
                  ${item.price.toFixed(2)}
                  {item.price_source === 'live' && <span className="price-badge">LIVE</span>}
                </div>
              )}
              <div className="ticker-condition">{item.condition}</div>
              <div className="ticker-confidence">Confidence: {item.confidence.toFixed(0)}%</div>
              <div className="ticker-source">Source: {sourceLabel(item.price_source, item.data_provider)}</div>
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  handleRefreshTicker(item.symbol);
                }}
                disabled={refreshingTicker === item.symbol}
                className="ticker-card-refresh"
                title="Refresh this ticker's data"
              >
                {refreshingTicker === item.symbol ? '⏳' : '🔄'}
              </button>
            </div>
          ))}
        </div>
        </div>

      {selected && (
        <div className="ticker-detail-panel">
          <h3>{selected.symbol} — Current Condition</h3>
          <div className="detail-line"><span>Signal:</span> {selected.signal} ({selected.confidence.toFixed(1)}%)</div>
          <div className="detail-line"><span>Condition:</span> {selected.condition}</div>
          <div className="detail-line"><span>Suggested Action:</span> {selected.action}</div>
          <div className="detail-line"><span>Data Source:</span> {sourceLabel(selected.price_source, selected.data_provider)}</div>
          <div className="detail-line">
            <span>Price:</span>{' '}
            {selected.price !== null ? `$${selected.price.toFixed(2)}` : 'N/A'}
            {' '}<em>({selected.price_message})</em>
          </div>
          {selected.last_updated && (
            <div className="detail-line"><span>Latest Update:</span> {new Date(selected.last_updated).toLocaleString()}</div>
          )}

          {selected.price_source !== 'live' && (
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
          )}

          {selected.signal_metrics && selected.signal_metrics.length > 0 && (
            <div className="metrics-block">
              <div className="metrics-title">Signal Metrics (Current vs Trigger Range)</div>
              <div className="metrics-list">
                {(() => {
                  const rsiNames = ['RSI (4H)', 'RSI (Daily)', 'RSI (Weekly)'];
                  const rsiMetrics = rsiNames
                    .map((name) => selected.signal_metrics.find((m) => m.name === name))
                    .filter((m): m is NonNullable<typeof m> => Boolean(m));

                  const nonRsiMetrics = selected.signal_metrics.filter(
                    (m) => !rsiNames.includes(m.name) && m.name !== 'RSI (Model)'
                  );

                  return (
                    <>
                      {rsiMetrics.length > 0 && (
                        <div className="metric-row">
                          <div className="metric-name">RSI Timeframes</div>
                          <div className="metric-timeframes">
                            {rsiMetrics.map((metric) => {
                              const met = isMetricTriggered(metric.current, metric.low_trigger, metric.high_trigger);
                              return (
                                <div key={metric.name} className={`metric-timeframe ${met ? 'met' : 'not-met'}`}>
                                  <span className="metric-status">{met ? '✅' : '🔴'}</span>
                                  <span>{metric.name.replace('RSI ', '')}: </span>
                                  <strong>{metric.current !== null ? metric.current.toFixed(2) : 'N/A'}</strong>
                                </div>
                              );
                            })}
                          </div>
                          <div className="metric-desc">Trigger met when RSI is below 30 or above 70.</div>
                        </div>
                      )}

                      {nonRsiMetrics.map((metric) => {
                        const met = isMetricTriggered(metric.current, metric.low_trigger, metric.high_trigger);
                        return (
                          <div key={metric.name} className="metric-row">
                            <div className="metric-name">
                              <span className="metric-status">{met ? '✅' : '🔴'}</span> {metric.name}
                            </div>
                            <div className="metric-values">
                              <span>Current: <strong>{metric.current !== null ? metric.current.toFixed(2) : 'N/A'}{metric.unit === '%' ? '%' : ''}</strong></span>
                              <span>Low trigger: {metric.low_trigger.toFixed(2)}{metric.unit === '%' ? '%' : ''}</span>
                              <span>High trigger: {metric.high_trigger.toFixed(2)}{metric.unit === '%' ? '%' : ''}</span>
                            </div>
                            <div className="metric-desc">{metric.description}</div>
                          </div>
                        );
                      })}
                    </>
                  );
                })()}
              </div>
            </div>
          )}
        </div>
      )}
      </div>
    </div>
  );
};
