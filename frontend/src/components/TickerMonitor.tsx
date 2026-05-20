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
  const [refreshingAll, setRefreshingAll] = useState(false);

  const isMarketOpenET = () => {
    const parts = new Intl.DateTimeFormat('en-US', {
      timeZone: 'America/New_York',
      weekday: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).formatToParts(new Date());

    const weekday = parts.find((p) => p.type === 'weekday')?.value ?? '';
    if (weekday === 'Sat' || weekday === 'Sun') return false;

    const hour = Number(parts.find((p) => p.type === 'hour')?.value ?? '0');
    const minute = Number(parts.find((p) => p.type === 'minute')?.value ?? '0');
    const totalMinutes = hour * 60 + minute;

    // 9:30 AM to 4:00 PM ET
    return totalMinutes >= (9 * 60 + 30) && totalMinutes <= (16 * 60);
  };

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
    api.getMonitorHistory(selected.symbol, '1d', '6mo', 120)
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

  const handleRefreshAll = async () => {
    setRefreshingAll(true);
    setError(null);
    try {
      await loadAll({ silent: true });
      if (selectedSymbol) {
        const resp = await api.getMonitorHistory(selectedSymbol, '1d', '6mo', 120);
        setHistory(resp.bars ?? []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh all tickers');
    } finally {
      setRefreshingAll(false);
    }
  };

  useEffect(() => {
    const interval = setInterval(async () => {
      if (!isMarketOpenET()) return;

      try {
        await loadAll({ silent: true });
        if (selectedSymbol) {
          const resp = await api.getMonitorHistory(selectedSymbol, '1d', '6mo', 120);
          setHistory(resp.bars ?? []);
        }
      } catch {
        // keep existing UI state on background auto-refresh errors
      }
    }, 120000);

    return () => clearInterval(interval);
  }, [selectedSymbol]);

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

  const historySeries = useMemo(() => {
    return history
      .map((bar) => ({
        t: new Date(bar.timestamp).getTime(),
        close: bar.close,
      }))
      .filter((x) => Number.isFinite(x.t) && Number.isFinite(x.close))
      .sort((a, b) => a.t - b.t);
  }, [history]);

  const chart = useMemo(() => {
    if (historySeries.length < 2) return null;

    const width = 680;
    const height = 220;
    const pad = 16;

    const values = historySeries.map((p) => p.close);
    const fallbackPrice = selected?.price ?? historySeries[historySeries.length - 1]?.close ?? null;
    const fallbackSL = fallbackPrice !== null ? Number((fallbackPrice * 0.98).toFixed(2)) : null;
    const fallbackTP = fallbackPrice !== null ? Number((fallbackPrice * 1.04).toFixed(2)) : null;
    const buySL = selected?.signal === 'BUY' ? (selected?.suggested_stop_loss ?? fallbackSL) : null;
    const buyTP = selected?.signal === 'BUY' ? (selected?.suggested_take_profit ?? fallbackTP) : null;
    const overlayValues = [
      ...values,
      ...(buySL !== null ? [buySL] : []),
      ...(buyTP !== null ? [buyTP] : []),
    ];

    const min = Math.min(...overlayValues);
    const max = Math.max(...overlayValues);
    const range = Math.max(max - min, 0.0001);

    const xFor = (i: number) => pad + (i / (historySeries.length - 1)) * (width - pad * 2);
    const yFor = (v: number) => height - pad - ((v - min) / range) * (height - pad * 2);

    const points = historySeries
      .map((p, i) => `${xFor(i)},${yFor(p.close)}`)
      .join(' ');

    const shortWindow = 20;
    const longWindow = 50;
    const maPointsFor = (window: number) => {
      const pts: string[] = [];
      for (let i = 0; i < historySeries.length; i += 1) {
        if (i + 1 < window) continue;
        const slice = historySeries.slice(i + 1 - window, i + 1);
        const avg = slice.reduce((sum, p) => sum + p.close, 0) / window;
        pts.push(`${xFor(i)},${yFor(avg)}`);
      }
      return pts.length >= 2 ? pts.join(' ') : null;
    };

    const maShortPoints = maPointsFor(shortWindow);
    const ma50Points = maPointsFor(longWindow);

    const bbWindow = 20;
    const bbStd = 2;
    const bbUpper: string[] = [];
    const bbMiddle: string[] = [];
    const bbLower: string[] = [];
    for (let i = 0; i < historySeries.length; i += 1) {
      if (i + 1 < bbWindow) continue;
      const slice = historySeries.slice(i + 1 - bbWindow, i + 1).map((p) => p.close);
      const mean = slice.reduce((sum, v) => sum + v, 0) / bbWindow;
      const variance = slice.reduce((sum, v) => sum + (v - mean) ** 2, 0) / bbWindow;
      const std = Math.sqrt(variance);
      const upper = mean + bbStd * std;
      const lower = mean - bbStd * std;
      bbUpper.push(`${xFor(i)},${yFor(upper)}`);
      bbMiddle.push(`${xFor(i)},${yFor(mean)}`);
      bbLower.push(`${xFor(i)},${yFor(lower)}`);
    }

    const bbUpperPoints = bbUpper.length >= 2 ? bbUpper.join(' ') : null;
    const bbMiddlePoints = bbMiddle.length >= 2 ? bbMiddle.join(' ') : null;
    const bbLowerPoints = bbLower.length >= 2 ? bbLower.join(' ') : null;
    const bbBandFillPoints = (bbUpper.length >= 2 && bbLower.length >= 2)
      ? `${bbUpper.join(' ')} ${[...bbLower].reverse().join(' ')}`
      : null;

    const latestMA = (window: number) => {
      if (historySeries.length < window) return null;
      const slice = historySeries.slice(historySeries.length - window);
      return slice.reduce((sum, p) => sum + p.close, 0) / window;
    };

    const maShortLatest = latestMA(shortWindow);
    const ma50Latest = latestMA(longWindow);
    const latestBB = (() => {
      if (historySeries.length < bbWindow) return null;
      const slice = historySeries.slice(historySeries.length - bbWindow).map((p) => p.close);
      const mean = slice.reduce((sum, v) => sum + v, 0) / bbWindow;
      const variance = slice.reduce((sum, v) => sum + (v - mean) ** 2, 0) / bbWindow;
      const std = Math.sqrt(variance);
      return {
        upper: mean + bbStd * std,
        middle: mean,
        lower: mean - bbStd * std,
      };
    })();

    const latest = historySeries[historySeries.length - 1]?.close ?? null;
    const first = historySeries[0]?.close ?? null;
    const slY = buySL !== null ? yFor(buySL) : null;
    const tpY = buyTP !== null ? yFor(buyTP) : null;

    return {
      width,
      height,
      points,
      min,
      max,
      latest,
      first,
      buySL,
      buyTP,
      slY,
      tpY,
      maShortPoints,
      ma50Points,
      maShortLatest,
      ma50Latest,
      shortWindow,
      longWindow,
      bbUpperPoints,
      bbMiddlePoints,
      bbLowerPoints,
      bbBandFillPoints,
      latestBB,
      bbWindow,
      bbStd,
      latestDate: new Date(historySeries[historySeries.length - 1].t).toLocaleDateString(),
      firstDate: new Date(historySeries[0].t).toLocaleDateString(),
    };
  }, [historySeries, selected?.signal, selected?.suggested_stop_loss, selected?.suggested_take_profit]);
  const isRegimeBlockedCondition = (condition?: string | null) =>
    Boolean(condition && condition.toLowerCase().includes('buy blocked by market regime filter'));

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
            <button
              className="ticker-refresh-all-btn"
              onClick={handleRefreshAll}
              disabled={refreshingAll}
              title="Refresh all monitored ticker data"
            >
              {refreshingAll ? 'Refreshing...' : '🔄 Refresh All'}
            </button>
          </div>

        <div className="ticker-cards">
          {sortedItems.map(item => (
            <div
              key={item.symbol}
              className={`ticker-card ${item.signal.toLowerCase()} ${selectedSymbol === item.symbol ? 'active' : ''} ${isRegimeBlockedCondition(item.condition) ? 'regime-blocked' : ''}`}
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
          <div className={`detail-line ${isRegimeBlockedCondition(selected.condition) ? 'warning' : ''}`}>
            <span>Condition:</span>{' '}
            {isRegimeBlockedCondition(selected.condition) ? '⚠️ ' : ''}
            {selected.condition}
          </div>
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

          <div className="metrics-history-layout">
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

            <div className="history-block">
              <div className="history-title">Recent Historical Closes</div>
              {!chart ? (
                <div className="history-empty">No historical bars available.</div>
              ) : (
                <div className="history-chart-wrap">
                  <svg
                    className="history-chart"
                    viewBox={`0 0 ${chart.width} ${chart.height}`}
                    role="img"
                    aria-label="Historical close price chart"
                  >
                    <line x1="0" y1={chart.height - 16} x2={chart.width} y2={chart.height - 16} className="history-axis" />
                    <line x1="16" y1="0" x2="16" y2={chart.height} className="history-axis" />
                    {chart.slY !== null && (
                      <>
                        <line x1="16" y1={chart.slY} x2={chart.width - 8} y2={chart.slY} className="history-line-sl" />
                        <text x={chart.width - 10} y={chart.slY - 4} textAnchor="end" className="history-line-sl-label">SL</text>
                      </>
                    )}
                    {chart.tpY !== null && (
                      <>
                        <line x1="16" y1={chart.tpY} x2={chart.width - 8} y2={chart.tpY} className="history-line-tp" />
                        <text x={chart.width - 10} y={chart.tpY - 4} textAnchor="end" className="history-line-tp-label">TP</text>
                      </>
                    )}
                    {chart.maShortPoints && (
                      <polyline points={chart.maShortPoints} fill="none" className="history-line-ma-short" />
                    )}
                    {chart.ma50Points && (
                      <polyline points={chart.ma50Points} fill="none" className="history-line-ma-50" />
                    )}
                    {chart.bbUpperPoints && (
                      <polygon points={chart.bbBandFillPoints ?? ''} className="history-bb-band-fill" />
                    )}
                    {chart.bbUpperPoints && (
                      <polyline points={chart.bbUpperPoints} fill="none" className="history-line-bb-upper" />
                    )}
                    {chart.bbMiddlePoints && (
                      <polyline points={chart.bbMiddlePoints} fill="none" className="history-line-bb-middle" />
                    )}
                    {chart.bbLowerPoints && (
                      <polyline points={chart.bbLowerPoints} fill="none" className="history-line-bb-lower" />
                    )}
                    <polyline points={chart.points} fill="none" className="history-line" />
                  </svg>
                  <div className="history-chart-meta">
                    <span>{chart.firstDate} (${chart.first?.toFixed(2)})</span>
                    <span>Low ${chart.min.toFixed(2)} · High ${chart.max.toFixed(2)}</span>
                    <span>{chart.latestDate} (${chart.latest?.toFixed(2)})</span>
                  </div>
                  <div className="history-ma-meta">
                    <span className="ma-short-tag">
                      MA{chart.shortWindow}: {chart.maShortLatest !== null ? `$${chart.maShortLatest.toFixed(2)}` : 'N/A'}
                    </span>
                    <span className="ma-50-tag">
                      MA{chart.longWindow}: {chart.ma50Latest !== null ? `$${chart.ma50Latest.toFixed(2)}` : 'N/A'}
                    </span>
                    <span className="bb-tag">
                      BB({chart.bbWindow},{chart.bbStd}) U/M/L: {chart.latestBB ? `$${chart.latestBB.upper.toFixed(2)} / $${chart.latestBB.middle.toFixed(2)} / $${chart.latestBB.lower.toFixed(2)}` : 'N/A'}
                    </span>
                  </div>
                  {(chart.buySL !== null || chart.buyTP !== null) && (
                    <div className="history-targets-meta">
                      {chart.buySL !== null && <span className="sl-tag">SL: ${chart.buySL.toFixed(2)}</span>}
                      {chart.buyTP !== null && <span className="tp-tag">TP: ${chart.buyTP.toFixed(2)}</span>}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
};
