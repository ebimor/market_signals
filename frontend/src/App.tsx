import { useState } from 'react'
import { useTrading } from './hooks/useTrading'
import { SignalReview } from './components/SignalReview'
import { TradeHistory } from './components/TradeHistory'
import { PerformanceDashboard } from './components/PerformanceDashboard'
import { OpenPositions } from './components/OpenPositions'
import { SystemStatusComponent as SystemStatus } from './components/SystemStatus'
import { SignalAnalysis } from './components/SignalAnalysis'
import { ManualTrade } from './components/ManualTrade'
import { TickerMonitor } from './components/TickerMonitor'
import './index.css'

type Tab = 'monitor' | 'signals' | 'analysis' | 'manual' | 'history' | 'performance' | 'positions'

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
          Signals {signals.length > 0 && <span className="badge">{signals.length}</span>}
        </button>
        <button className={activeTab === 'analysis' ? 'active' : ''} onClick={() => setActiveTab('analysis')}>
          📋 Analysis {signals.length > 0 && <span className="badge">{signals.length}</span>}
        </button>
        <button className={activeTab === 'positions' ? 'active' : ''} onClick={() => setActiveTab('positions')}>
          Positions {openTrades.length > 0 && <span className="badge">{openTrades.length}</span>}
        </button>
        <button className={activeTab === 'manual' ? 'active' : ''} onClick={() => setActiveTab('manual')}>
          ✍️ My Trades
        </button>
        <button className={activeTab === 'history' ? 'active' : ''} onClick={() => setActiveTab('history')}>
          Trade History
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
        {activeTab === 'analysis' && (
          <SignalAnalysis signals={signals} />
        )}
        {activeTab === 'positions' && (
          <OpenPositions trades={openTrades} status={status} />
        )}
        {activeTab === 'manual' && (
          <ManualTrade openTrades={openTrades} stats={stats} onTradeAdded={refreshAll} />
        )}
        {activeTab === 'history' && (
          <TradeHistory trades={tradeHistory} />
        )}
        {activeTab === 'performance' && (
          <PerformanceDashboard stats={stats} trades={tradeHistory} />
        )}
      </main>
    </div>
  )
}

export default App
