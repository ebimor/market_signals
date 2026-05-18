# SafeSwing Trader

Conservative Stock Market Monitoring & Swing Trade Assistant

## Overview

SafeSwing Trader is a desktop application designed to help retail investors identify lower-risk swing-trading opportunities while minimizing exposure to major market crashes. The system prioritizes capital preservation, controlled downside risk, and disciplined exit management over aggressive profit maximization.

## Documentation

- Core documentation index: [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md)
- Historical phase/status reports: [docs/archive](docs/archive)

## Key Features

- **Real-time Market Monitoring**: Track selected stocks with 1-15 minute refresh intervals
- **Conservative Signal Engine**: Entry/exit signals based on technical analysis and market health
- **Risk Management**: ATR-based stop losses, position sizing, and portfolio exposure limits
- **Watchlists**: Create and categorize stock watchlists
- **Charting**: TradingView Lightweight Charts integration with technical indicators
- **Backtesting**: Simulate historical trades to validate strategies
- **Alerts**: Desktop notifications for trade opportunities and risk events
- **Market Crash Protection**: Global filters to disable trading during high volatility

## Project Structure

```
safeswing_trader/
├── frontend/              # React + TypeScript frontend
│   ├── src/
│   │   ├── components/   # Reusable React components
│   │   ├── pages/        # Page components
│   │   ├── charts/       # Charting components
│   │   ├── hooks/        # Custom React hooks
│   │   └── services/     # API communication
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── backend/               # Python FastAPI backend
│   ├── api/              # REST API endpoints
│   ├── signals/          # Signal generation engine
│   ├── risk/             # Risk management engine
│   ├── strategies/       # Trading strategies
│   ├── backtesting/      # Backtesting engine
│   ├── market_data/      # Market data collection
│   ├── alerts/           # Alert system
│   ├── database/         # Database models and ORM
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration management
│   └── requirements.txt
│
├── shared/               # Shared types and utilities
├── docs/                 # Documentation
├── tests/                # Test suites
├── docker-compose.yml    # Docker orchestration
└── README.md
```

## Technology Stack

### Frontend
- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool
- **Lightweight Charts** - Professional charting library
- **Axios** - HTTP client

### Backend
- **Python 3.12** - Language
- **FastAPI** - Web framework
- **Pandas & NumPy** - Data analysis
- **TA-Lib** - Technical analysis
- **SQLAlchemy** - ORM
- **SQLite/PostgreSQL** - Database

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose (optional)

### Without Docker

#### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

The backend will run on `http://localhost:8000`

#### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will run on `http://localhost:3001`

#### 3. Run all quality checks (single command)

```bash
./scripts/check-all.sh
```

This runs:
- Backend tests (`pytest -q tests`)
- Frontend typecheck (`tsc --noEmit`)
- Frontend lint (if eslint is available)

### With Docker

```bash
docker-compose up
```

- Frontend: `http://localhost:3001`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

## API Endpoints

### Health Check
- `GET /health` - Check API health status

### Trading API (Phase 4c) ✅ IMPLEMENTED

**Signal Management**
- `GET /api/trading/signals` - Get pending signals
- `POST /api/trading/signals` - Create new signal

**Approval Workflow**
- `POST /api/trading/approve` - Approve signal for execution
- `POST /api/trading/reject` - Reject signal

**Trade Execution**
- `POST /api/trading/execute` - Execute approved trade
- `POST /api/trading/close` - Close trade with P&L calculation

**Monitoring**
- `GET /api/trading/trades/open` - Get open positions
- `GET /api/trading/trades/history` - Get closed trades with P&L

**Analytics**
- `GET /api/trading/stats` - Get performance statistics
- `GET /api/trading/dashboard` - Get complete dashboard
- `GET /api/trading/status` - Get system status

**See Also:**
- Interactive API docs: `http://localhost:8000/docs`
- Full API reference: [PHASE_4C_TRADING_API_COMPLETE.md](PHASE_4C_TRADING_API_COMPLETE.md)
- Quick start: [QUICK_START.md](QUICK_START.md)

### Market Data (to be implemented)
- `GET /api/stocks/{ticker}` - Get stock data
- `GET /api/watchlists` - List watchlists
- `POST /api/watchlists` - Create watchlist

### Signals (to be implemented)
- `GET /api/signals` - Get current signals
- `POST /api/signals/backtest` - Run backtest

### Risk (to be implemented)
- `GET /api/portfolio/risk` - Get portfolio risk metrics

## Configuration

Configuration is managed through environment variables. See `backend/.env.example` for all available options.

Key settings:
- `DATABASE_URL` - Database connection string
- `API_PORT` - Backend port (default: 8000)
- `MARKET_DATA_REFRESH_INTERVAL` - Data refresh frequency in seconds
- `VIX_THRESHOLD` - VIX level for market crash protection
- `DEFAULT_ACCOUNT_RISK_PERCENT` - Risk per trade (default: 1%)

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Structure Guidelines

- Keep modules focused and single-responsibility
- Use type hints in Python, TypeScript everywhere
- Write tests for new features
- Follow PEP 8 (Python) and Prettier formatting (TypeScript)
- Include error handling and logging

## Signal Engine Logic

### Entry Conditions (BUY)

A BUY signal is generated only if ALL conditions are met:

1. **Market Health**
   - SPY above 50-day moving average
   - VIX below threshold
   - No major macroeconomic events

2. **Stock Trend**
   - Price above 20-period EMA
   - 20 EMA above 50 EMA
   - Volume above average

3. **Momentum**
   - RSI between 45-65
   - MACD bullish crossover

### Exit Conditions (SELL)

A SELL signal is generated if ANY condition is met:

- Take-profit target reached
- Stop-loss triggered
- Market trend weakens significantly
- Abnormal volatility spike
- Bearish momentum detected

## Risk Management

- **Position Sizing**: Default 1% account risk per trade
- **Stop Loss**: 1.5x ATR below entry
- **Take Profit**: 2:1 reward/risk ratio
- **Correlation Check**: Prevent overexposure to correlated stocks
- **Portfolio Limits**: Configurable sector and total risk limits

## Development Phases

### Phase 1: Data Management ✅ COMPLETE
- [x] Auto-download from yfinance with caching
- [x] Multi-symbol batch downloads
- [x] CSV cache management

### Phase 2: Technical Indicators ✅ COMPLETE
- [x] RSI indicator (14-period standard)
- [x] MACD indicator (12,26,9 standard)
- [x] Multi-indicator signal confirmation
- [x] Confidence scoring

### Phase 3: Risk Management ✅ COMPLETE
- [x] Portfolio exposure tracking (50% max)
- [x] Position sizing (10% max per trade)
- [x] Daily portfolio limits
- [x] Constraint enforcement

### Phase 4: Backtesting Engine ✅ COMPLETE
- [x] Trade execution engine
- [x] P&L tracking and metrics
- [x] 20+ performance statistics

### Phase 4b: Strategy Simulator ✅ COMPLETE
- [x] Historical data loading
- [x] Signal generation (RSI + MACD + SMA)
- [x] Trade execution with constraints
- [x] Position exits (take profit/stop loss)
- [x] End-to-end backtesting

### Phase 4c: Trading REST API ✅ COMPLETE
- [x] 10+ REST endpoints
- [x] Manual trade approval workflow
- [x] No automatic execution
- [x] Trade record persistence
- [x] P&L tracking and analytics
- [x] FastAPI integration
- [x] Complete test suite (10/10 passing)

### Phase 4d: Reporting & Visualization ✅ COMPLETE
- [x] React dashboard (5 components)
- [x] Signal review interface
- [x] Trade history table
- [x] Performance charts (Recharts)
- [x] Open positions monitor
- [x] Real-time auto-refresh
- [x] Responsive design
- [x] TypeScript type safety

### Phase 5: Live Trading Integration (PLANNED)
- [ ] Broker API integration (Alpaca, Interactive Brokers)
- [ ] Real order execution
- [ ] Live position tracking
- [ ] Risk monitoring on live trades
- [ ] Order management

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/your-feature`
4. Submit pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on the project repository.

## Disclaimer

This application is for educational and research purposes. It is not financial advice. Past performance does not guarantee future results. Always do your own research and consult with financial professionals before making trading decisions.
# market_signals
