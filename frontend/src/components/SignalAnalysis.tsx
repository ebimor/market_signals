import React, { useEffect, useState } from 'react';
import { Signal } from '../services/api';

async function fetchJsonSafe<T>(url: string): Promise<T> {
  const res = await fetch(url);
  const raw = await res.text();
  let data: any = null;

  if (raw.trim()) {
    try {
      data = JSON.parse(raw);
    } catch {
      throw new Error(raw.split('\n')[0] || 'Invalid server response');
    }
  }

  if (!res.ok) {
    throw new Error(data?.detail || data?.message || raw.split('\n')[0] || `Request failed (${res.status})`);
  }

  return data as T;
}

interface SignalAnalysisProps {
  signals: Signal[];
}

interface IndicatorData {
  rsi?: { value: number; signal: string; confidence: number; interpretation: string };
  macd?: { macd: number; signal_line: number; histogram: number; signal: string; interpretation: string };
  data_source?: 'live' | 'simulated';
  last_updated?: string | null;
  loading: boolean;
  error?: string;
}

function getRSIAnalysis(value: number): { text: string; color: string } {
  if (value >= 75) return { text: `RSI at ${value.toFixed(1)} — extremely overbought. Price momentum is exhausted, high probability of reversal or pullback.`, color: '#fc8181' };
  if (value >= 70) return { text: `RSI at ${value.toFixed(1)} — overbought territory. Buyers are losing strength. Watch for bearish reversal signals.`, color: '#f6ad55' };
  if (value >= 55) return { text: `RSI at ${value.toFixed(1)} — bullish momentum, but approaching overbought. Trend is healthy but gains may slow.`, color: '#68d391' };
  if (value >= 45) return { text: `RSI at ${value.toFixed(1)} — neutral zone. No strong directional bias from RSI alone.`, color: '#a0aec0' };
  if (value >= 30) return { text: `RSI at ${value.toFixed(1)} — oversold territory. Sellers are losing strength. Watch for bullish reversal signals.`, color: '#63b3ed' };
  return { text: `RSI at ${value.toFixed(1)} — extremely oversold. Selling pressure exhausted, high probability of bounce or reversal.`, color: '#76e4f7' };
}

function getMACDAnalysis(macd: number, signal: number, histogram: number): string {
  const cross = macd > signal ? 'bullish' : 'bearish';
  const strength = Math.abs(histogram).toFixed(3);
  if (histogram > 0 && histogram > Math.abs(macd) * 0.1)
    return `MACD crossed above signal line (bullish crossover). Histogram at +${strength} — buying momentum is building.`;
  if (histogram < 0 && Math.abs(histogram) > Math.abs(macd) * 0.1)
    return `MACD crossed below signal line (bearish crossover). Histogram at ${strength} — selling momentum is building.`;
  return `MACD showing ${cross} alignment. Histogram near zero (${strength}) — momentum transition in progress.`;
}

function getSignalRationale(signal: Signal, indicators: IndicatorData): string[] {
  const lines: string[] = [];
  const type = signal.type;

  // Parse reason for keywords
  const reason = signal.reason.toLowerCase();

  if (reason.includes('rsi')) {
    if (indicators.rsi) {
      const { text } = getRSIAnalysis(indicators.rsi.value);
      const interp = indicators.rsi.interpretation ? ` — ${indicators.rsi.interpretation}` : '';
      lines.push(`📊 RSI: ${text}${interp}`);
    } else {
      if (reason.includes('oversold') || reason.includes('bounce'))
        lines.push(`📊 RSI: Dropped into oversold zone (typically below 30). Daily selling pressure is exhausted — historically signals a bounce.`);
      else if (reason.includes('overbought'))
        lines.push(`📊 RSI: Climbed into overbought zone (typically above 70). Daily buying pressure is exhausted — trade momentum is fading.`);
    }
  }

  if (reason.includes('macd')) {
    if (indicators.macd) {
      const interp = indicators.macd.interpretation || getMACDAnalysis(indicators.macd.macd, indicators.macd.signal_line, indicators.macd.histogram);
      lines.push(`📈 MACD: ${interp} (histogram: ${indicators.macd.histogram > 0 ? '+' : ''}${indicators.macd.histogram.toFixed(3)})`);
    } else {
      if (type === 'BUY')
        lines.push(`📈 MACD: Bullish crossover detected — MACD line crossed above signal line, confirming upward momentum shift.`);
      else
        lines.push(`📈 MACD: Bearish crossover detected — MACD line crossed below signal line, confirming downward momentum shift.`);
    }
  }

  if (reason.includes('volume'))
    lines.push(`📦 Volume: Unusual volume spike detected. High volume on this move confirms institutional participation — not just retail noise.`);

  if (reason.includes('resistance'))
    lines.push(`🧱 Resistance: Price is approaching a known resistance level. Previous sellers at this zone may cause the price to stall or reverse.`);

  if (reason.includes('support'))
    lines.push(`🧲 Support: Price is near a key support level. Historical buyers at this zone make a bounce statistically likely.`);

  if (reason.includes('sma') || reason.includes('moving average'))
    lines.push(`📉 Moving Average: Price interaction with a key moving average — these act as dynamic support/resistance and trend filters.`);

  // Risk/reward summary
  const rr = ((signal.take_profit - signal.price) / (signal.price - signal.stop_loss));
  const rrText = type === 'BUY'
    ? `Risk $${(signal.price - signal.stop_loss).toFixed(2)} to make $${(signal.take_profit - signal.price).toFixed(2)}`
    : `Risk $${(signal.stop_loss - signal.price).toFixed(2)} to make $${(signal.price - signal.take_profit).toFixed(2)}`;
  lines.push(`⚖️ Risk/Reward: ${rrText} → ratio ${Math.abs(rr).toFixed(1)}:1 ${Math.abs(rr) >= 2 ? '✅ Good' : Math.abs(rr) >= 1.5 ? '⚠️ Acceptable' : '❌ Poor'}`);

  return lines;
}

export const SignalAnalysis: React.FC<SignalAnalysisProps> = ({ signals }) => {
  const [indicatorMap, setIndicatorMap] = useState<Record<string, IndicatorData>>({});

  useEffect(() => {
    signals.forEach(signal => {
      if (indicatorMap[signal.symbol]) return;

      setIndicatorMap(prev => ({ ...prev, [signal.symbol]: { loading: true } }));

      // Fetch RSI
      fetchJsonSafe<any>(`/api/market/indicators/rsi/${signal.symbol}?lookback=30`)
        .then(rsiData => {
          // Fetch MACD
          return fetchJsonSafe<any>(`/api/market/indicators/macd/${signal.symbol}?lookback=30`)
            .then(macdData => {
              setIndicatorMap(prev => ({
                ...prev,
                [signal.symbol]: {
                  loading: false,
                  data_source: rsiData.data_source ?? macdData.data_source ?? 'live',
                  last_updated: rsiData.last_updated ?? macdData.last_updated ?? null,
                  rsi: rsiData.current_value !== undefined ? {
                    value: rsiData.current_value,
                    signal: rsiData.signal,
                    confidence: rsiData.confidence,
                    interpretation: rsiData.interpretation
                  } : undefined,
                  macd: macdData.current ? {
                    macd: macdData.current.macd,
                    signal_line: macdData.current.signal,
                    histogram: macdData.current.histogram,
                    signal: macdData.signal,
                    interpretation: macdData.interpretation
                  } : undefined
                }
              }));
            });
        })
        .catch(() => {
          setIndicatorMap(prev => ({
            ...prev,
            [signal.symbol]: { loading: false, error: 'Could not fetch live indicators' }
          }));
        });
    });
  }, [signals]);

  if (signals.length === 0) {
    return (
      <div className="empty-state">
        <h3>No signals to analyze</h3>
        <p>Signal analysis will appear here when pending signals are available.</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <h2 style={{ color: '#63b3ed', marginBottom: '0.5rem' }}>📋 Signal Analysis</h2>
      <p style={{ color: '#a0aec0', fontSize: '0.9rem', marginTop: '-0.5rem' }}>
        Detailed breakdown of why each signal was generated
      </p>

      {signals.map(signal => {
        const indicators = indicatorMap[signal.symbol] || { loading: true };
        const rationale = getSignalRationale(signal, indicators);
        const rsiAnalysis = indicators.rsi ? getRSIAnalysis(indicators.rsi.value) : null;
        const borderColor = signal.type === 'BUY' ? '#48bb78' : signal.type === 'SELL' ? '#fc8181' : '#ecc94b';

        return (
          <div key={signal.signal_id} style={{
            background: '#1a1d2e',
            border: `1px solid #2d3748`,
            borderLeft: `5px solid ${borderColor}`,
            borderRadius: '10px',
            padding: '1.5rem',
          }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '1.4rem', fontWeight: 'bold' }}>{signal.symbol}</span>
                <span style={{
                  padding: '0.2rem 0.7rem',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  fontWeight: 'bold',
                  background: signal.type === 'BUY' ? '#1c4532' : '#742a2a',
                  color: borderColor
                }}>{signal.type}</span>
                <span style={{ color: '#a0aec0', fontSize: '0.85rem' }}>@ ${signal.price.toFixed(2)}</span>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.8rem', color: '#718096' }}>Confidence</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: signal.confidence >= 80 ? '#48bb78' : signal.confidence >= 60 ? '#ecc94b' : '#fc8181' }}>
                  {signal.confidence.toFixed(0)}%
                </div>
              </div>
            </div>

            {/* Original reason */}
            <div style={{ background: '#0f1117', borderRadius: '6px', padding: '0.75rem', marginBottom: '1rem', fontSize: '0.85rem', color: '#e2e8f0', fontStyle: 'italic' }}>
              💬 "{signal.reason}"
            </div>

            {/* Data source badge */}
            {!indicators.loading && (
              <div style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {indicators.data_source === 'live' ? (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', padding: '0.2rem 0.6rem', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600, background: '#1c4532', color: '#68d391', border: '1px solid #2f855a' }}>
                    📡 Live data
                  </span>
                ) : indicators.data_source === 'simulated' ? (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', padding: '0.2rem 0.6rem', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600, background: '#744210', color: '#f6ad55', border: '1px solid #b7791f' }}>
                    ⚠️ Simulated data — yfinance unavailable
                  </span>
                ) : null}
                {indicators.last_updated && (
                  <span style={{ fontSize: '0.72rem', color: '#718096' }}>
                    Last bar: {new Date(indicators.last_updated).toLocaleDateString()}
                  </span>
                )}
              </div>
            )}

            {/* Live indicator bar */}
            {indicators.loading && (
              <div style={{ color: '#718096', fontSize: '0.85rem', marginBottom: '1rem' }}>⏳ Fetching live indicators...</div>
            )}

            {indicators.rsi && (
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                  <span style={{ fontSize: '0.8rem', color: '#718096' }}>RSI (14)</span>
                  <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: rsiAnalysis?.color }}>{indicators.rsi.value.toFixed(1)}</span>
                </div>
                <div style={{ background: '#2d3748', borderRadius: '4px', height: '8px', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.min(indicators.rsi.value, 100)}%`, height: '100%', borderRadius: '4px', background: rsiAnalysis?.color, transition: 'width 0.5s ease' }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#4a5568', marginTop: '0.2rem' }}>
                  <span>Oversold 30</span><span>Neutral 50</span><span>Overbought 70</span>
                </div>
              </div>
            )}

            {/* Detailed analysis lines */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 'bold', color: '#718096', marginBottom: '0.2rem' }}>Why this signal was generated:</div>
              {rationale.map((line, i) => (
                <div key={i} style={{
                  background: '#0f1117',
                  borderRadius: '6px',
                  padding: '0.6rem 0.75rem',
                  fontSize: '0.85rem',
                  color: '#e2e8f0',
                  lineHeight: '1.5'
                }}>{line}</div>
              ))}
            </div>

            {/* SL/TP summary */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', marginTop: '1rem' }}>
              {[
                { label: 'Entry', value: `$${signal.price.toFixed(2)}`, color: '#63b3ed' },
                { label: 'Stop Loss', value: `$${signal.stop_loss.toFixed(2)}`, color: '#fc8181' },
                { label: 'Take Profit', value: `$${signal.take_profit.toFixed(2)}`, color: '#48bb78' },
              ].map(item => (
                <div key={item.label} style={{ background: '#0f1117', borderRadius: '6px', padding: '0.5rem 0.75rem', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: '#718096' }}>{item.label}</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 'bold', color: item.color }}>{item.value}</div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};
