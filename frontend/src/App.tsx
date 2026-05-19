import { useState } from 'react'
import { useTrading } from './hooks/useTrading'
import { SignalReview } from './components/SignalReview'
import { TradeHistory } from './components/TradeHistory'
import { PerformanceDashboard } from './components/PerformanceDashboard'
import { OpenPositions } from './components/OpenPositions'
import { SystemStatusComponent as SystemStatus } from './components/SystemStatus'
import { ManualTrade } from './components/ManualTrade'
import { TickerMonitor } from './components/TickerMonitor'
import './index.css'

type Tab = 'monitor' | 'signals' | 'manual' | 'performance'

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('monitor')
  const {
    signals, openTrades, tradeHistory, stats, status,
    loading, error, approveTrade, rejectTrade, refreshAll
  } = useTrading()

  return (
    <div className="app">
      <header className="app-header">
        <h1>📈 SafeSwing Trader</h1>
        <SystemStatus status={status} />
      </header>

      {error && <div className="error-banner">⚠️ {error}</div>}

      <nav className="tab-nav">
        <button className={activeTab === 'monitor' ? 'active' : ''} onClick={() => setActiveTab('monitor')}>
          🎯 Monitor
        </button>
        <button className={activeTab === 'signals' ? 'active' : ''} onClick={() => setActiveTab('signals')}>
          🔔 Signals {signals.length > 0 && <span className="badge">{signals.length}</span>}
        </button>
        <button className={activeTab === 'manual' ? 'active' : ''} onClick={() => setActiveTab('manual')}>
          ✍️ My Trades {openTrades.length > 0 && <span className="badge">{openTrades.length}</span>}
        </button>
        <button className={activeTab === 'performance' ? 'active' : ''} onClick={() => setActiveTab('performance')}>
          Performance
        </button>
      </nav>

      <main className="app-main">
        {loading && <div className="loading">Loading...</div>}

        {activeTab === 'monitor' && (
          <TickerMonitor />
        )}

        {activeTab === 'signals' && (
          <SignalReview signals={signals} onApprove={approveTrade} onReject={rejectTrade} loading={loading} />
        )}
        {activeTab === 'manual' && (
          <>
            <OpenPositions trades={openTrades} status={status} />
            <div style={{ height: '1rem' }} />
            <ManualTrade openTrades={openTrades} stats={stats} onTradeAdded={refreshAll} />
          </>
        )}
        {activeTab === 'performance' && (
          <>
            <PerformanceDashboard stats={stats} trades={tradeHistory} />
            <div style={{ height: '1rem' }} />
            <TradeHistory trades={tradeHistory} onDeleted={refreshAll} />
          </>
        )}
      </main>
    </div>
  )
}

export default App
