import React, { useState } from 'react';
import { api, Trade, PerformanceStats } from '../services/api';
import '../styles/ManualTrade.css';

interface ManualTradeProps {
  openTrades: Trade[];
  stats: PerformanceStats | null;
  onTradeAdded: () => void;
}

interface OpenForm {
  symbol: string;
  signal_type: 'BUY' | 'SELL';
  entry_price: string;
  position_size: string;
  stop_loss: string;
  take_profit: string;
  notes: string;
}

interface CloseForm {
  exit_price: string;
  exit_reason: string;
}

const emptyOpen: OpenForm = {
  symbol: '',
  signal_type: 'BUY',
  entry_price: '',
  position_size: '',
  stop_loss: '',
  take_profit: '',
  notes: ''
};

export const ManualTrade: React.FC<ManualTradeProps> = ({ openTrades, stats, onTradeAdded }) => {
  const [openForm, setOpenForm] = useState<OpenForm>(emptyOpen);
  const [closeForms, setCloseForms] = useState<Record<string, CloseForm>>({});
  const [submitting, setSubmitting] = useState(false);
  const [closingId, setClosingId] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const flash = (msg: string, isError = false) => {
    if (isError) setErrorMsg(msg);
    else setSuccessMsg(msg);
    setTimeout(() => { setSuccessMsg(''); setErrorMsg(''); }, 3500);
  };

  const handleOpenChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setOpenForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleOpenSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!openForm.symbol || !openForm.entry_price || !openForm.position_size) {
      flash('Symbol, entry price, and position size are required.', true);
      return;
    }

    const price = parseFloat(openForm.entry_price);
    const size = parseFloat(openForm.position_size);
    const cost = price * size;

    if (stats && cost > stats.current_cash) {
      flash(`Insufficient cash! Trade cost is $${cost.toFixed(2)}, but current cash is $${stats.current_cash.toFixed(2)}.`, true);
      return;
    }

    setSubmitting(true);
    try {
      await api.manualTrade({
        symbol: openForm.symbol.toUpperCase(),
        signal_type: openForm.signal_type,
        entry_price: price,
        position_size: size,
        stop_loss: openForm.stop_loss ? parseFloat(openForm.stop_loss) : undefined,
        take_profit: openForm.take_profit ? parseFloat(openForm.take_profit) : undefined,
        notes: openForm.notes || 'Manual entry'
      });
      setOpenForm(emptyOpen);
      onTradeAdded();
      flash(`✅ ${openForm.signal_type} position opened for ${openForm.symbol.toUpperCase()}`);
    } catch (err: any) {
      flash(err.message || 'Failed to open trade', true);
    } finally {
      setSubmitting(false);
    }
  };

  const getCloseForm = (tradeId: string): CloseForm =>
    closeForms[tradeId] || { exit_price: '', exit_reason: 'Manual close' };

  const setCloseField = (tradeId: string, field: keyof CloseForm, value: string) => {
    setCloseForms(prev => ({
      ...prev,
      [tradeId]: { ...getCloseForm(tradeId), [field]: value }
    }));
  };

  const handleClose = async (trade: Trade) => {
    const form = getCloseForm(trade.trade_id);
    if (!form.exit_price) {
      flash('Enter an exit price to close the position.', true);
      return;
    }
    setClosingId(trade.trade_id);
    try {
      const exitPrice = parseFloat(form.exit_price);
      await api.closeTrade(trade.trade_id, exitPrice, form.exit_reason || 'Manual close');
      setCloseForms(prev => { const n = { ...prev }; delete n[trade.trade_id]; return n; });
      onTradeAdded();
      const pnl = (exitPrice - trade.entry_price) * trade.position_size;
      flash(`✅ ${trade.symbol} closed — P&L: ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}`);
    } catch (err: any) {
      flash(err.message || 'Failed to close trade', true);
    } finally {
      setClosingId(null);
    }
  };

  const calcRR = () => {
    const entry = parseFloat(openForm.entry_price);
    const sl = parseFloat(openForm.stop_loss);
    const tp = parseFloat(openForm.take_profit);
    if (!entry || !sl || !tp) return null;
    const risk = Math.abs(entry - sl);
    const reward = Math.abs(tp - entry);
    if (risk === 0) return null;
    return (reward / risk).toFixed(2);
  };

  const rr = calcRR();

  return (
    <div className="manual-trade">
      {successMsg && <div className="flash-success">{successMsg}</div>}
      {errorMsg && <div className="flash-error">{errorMsg}</div>}

      {/* ── Open Position ── */}
      <section className="manual-section">
        <div className="section-header-flex">
          <h2>📝 Record New Position</h2>
          {stats && (
            <div className="cash-badge">
              Cash: <strong>${stats.current_cash.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
            </div>
          )}
        </div>
        <p className="section-subtitle">Log a trade you entered manually at your broker.</p>

        <form className="manual-form" onSubmit={handleOpenSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>Ticker *</label>
              <input
                name="symbol"
                value={openForm.symbol}
                onChange={handleOpenChange}
                placeholder="e.g. AAPL"
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Direction *</label>
              <select name="signal_type" value={openForm.signal_type} onChange={handleOpenChange} className="form-input">
                <option value="BUY">BUY (Long)</option>
                <option value="SELL">SELL (Short)</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Entry Price *</label>
              <input
                name="entry_price"
                type="number"
                step="0.01"
                value={openForm.entry_price}
                onChange={handleOpenChange}
                placeholder="0.00"
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Shares / Contracts *</label>
              <input
                name="position_size"
                type="number"
                step="1"
                value={openForm.position_size}
                onChange={handleOpenChange}
                placeholder="100"
                className="form-input"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Stop Loss</label>
              <input
                name="stop_loss"
                type="number"
                step="0.01"
                value={openForm.stop_loss}
                onChange={handleOpenChange}
                placeholder="optional"
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Take Profit</label>
              <input
                name="take_profit"
                type="number"
                step="0.01"
                value={openForm.take_profit}
                onChange={handleOpenChange}
                placeholder="optional"
                className="form-input"
              />
            </div>
          </div>

          {rr && (
            <div className={`rr-badge ${parseFloat(rr) >= 2 ? 'good' : parseFloat(rr) >= 1.5 ? 'ok' : 'bad'}`}>
              Risk/Reward: {rr}:1 {parseFloat(rr) >= 2 ? '✅' : parseFloat(rr) >= 1.5 ? '⚠️' : '❌'}
            </div>
          )}

          <div className="form-group full-width">
            <label>Notes</label>
            <textarea
              name="notes"
              value={openForm.notes}
              onChange={handleOpenChange}
              placeholder="Why did you enter? What was the setup?"
              className="form-input form-textarea"
              rows={2}
            />
          </div>

          <button
            type="submit"
            className={`btn-open ${openForm.signal_type === 'SELL' ? 'sell' : 'buy'}`}
            disabled={submitting}
          >
            {submitting ? 'Recording...' : `📌 Record ${openForm.signal_type} Position`}
          </button>
        </form>
      </section>

      {/* ── Close Position ── */}
      <section className="manual-section">
        <h2>🔒 Close a Position</h2>
        {openTrades.length === 0 ? (
          <p className="no-data">No open positions to close.</p>
        ) : (
          <div className="close-list">
            {openTrades.map(trade => {
              const form = getCloseForm(trade.trade_id);
              const exitP = parseFloat(form.exit_price);
              const pnlPreview = form.exit_price
                ? (exitP - trade.entry_price) * trade.position_size
                : null;
              return (
                <div key={trade.trade_id} className="close-card">
                  <div className="close-header">
                    <div>
                      <span className="close-symbol">{trade.symbol}</span>
                      <span className="close-meta">
                        {trade.position_size} shares @ ${trade.entry_price.toFixed(2)}
                      </span>
                    </div>
                    {trade.notes && trade.notes !== '' && (
                      <span className="close-notes">{trade.notes}</span>
                    )}
                  </div>

                  <div className="close-form-row">
                    <input
                      type="number"
                      step="0.01"
                      placeholder="Exit price"
                      value={form.exit_price}
                      onChange={e => setCloseField(trade.trade_id, 'exit_price', e.target.value)}
                      className="form-input close-price-input"
                    />
                    <input
                      type="text"
                      placeholder="Reason (optional)"
                      value={form.exit_reason}
                      onChange={e => setCloseField(trade.trade_id, 'exit_reason', e.target.value)}
                      className="form-input close-reason-input"
                    />
                    <button
                      className="btn-close-trade"
                      onClick={() => handleClose(trade)}
                      disabled={closingId === trade.trade_id}
                    >
                      {closingId === trade.trade_id ? 'Closing...' : 'Close'}
                    </button>
                  </div>

                  {pnlPreview !== null && (
                    <div className={`pnl-preview ${pnlPreview >= 0 ? 'positive' : 'negative'}`}>
                      Est. P&L: {pnlPreview >= 0 ? '+' : ''}${pnlPreview.toFixed(2)}
                      {' '}({((exitP - trade.entry_price) / trade.entry_price * 100).toFixed(2)}%)
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
};
