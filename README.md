# SafeSwing Trader

Conservative Stock Market Monitoring & Swing Trade Assistant

## Overview

SafeSwing Trader is a desktop application designed to help retail investors identify lower-risk swing-trading opportunities while minimizing exposure to major market crashes. The system prioritizes capital preservation, controlled downside risk, and disciplined exit management over aggressive profit maximization.

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

The frontend will run on `http://localhost:3000`

### With Docker

```bash
docker-compose up
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

## API Endpoints

### Health Check
- `GET /health` - Check API health status

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

## Roadmap

### Phase 1 (MVP)
- [x] Project setup and structure
- [ ] Market data collector
- [ ] Charting interface
- [ ] Watchlist management
- [ ] Technical indicators
- [ ] Signal generation
- [ ] Basic backtesting

### Phase 2
- [ ] Broker integration (Alpaca)
- [ ] Paper trading
- [ ] Advanced alerting
- [ ] Mobile app companion

### Phase 3
- [ ] ML-based trade ranking
- [ ] Reinforcement learning research
- [ ] Portfolio optimization

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
