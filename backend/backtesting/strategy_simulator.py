"""
Phase 4b: Strategy Simulator - End-to-End Backtesting
Coordinates Phase 1 data, Phase 2 signals, and Phase 4 engine for complete strategy simulation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

from backend.backtesting.backtest_engine import BacktestEngine, Trade
from backend.signals.indicators import RSI, MACD
from backend.data.data_loader import DataLoader

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for strategy simulation"""
    initial_capital: float = 100000
    max_portfolio_exposure: float = 0.50
    max_position_size: float = 0.10
    max_open_positions: int = 5
    risk_per_trade: float = 0.02
    commission_percent: float = 0.001
    
    # Simulation parameters
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    symbols: List[str] = field(default_factory=lambda: ["AAPL", "TSLA", "MSFT"])
    
    # Signal parameters
    use_rsi: bool = True
    use_macd: bool = True
    use_bollinger: bool = True
    lookback_period: int = 30


@dataclass
class BacktestResult:
    """Complete backtest results and metrics"""
    config: BacktestConfig
    start_date: datetime
    end_date: datetime
    
    # Portfolio performance
    initial_capital: float
    final_capital: float
    total_return_percent: float
    max_drawdown_percent: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_percent: float
    
    # Profitability
    gross_wins: float
    gross_losses: float
    net_pnl: float
    profit_factor: float
    
    # Trade details
    avg_winner: float
    avg_loser: float
    largest_win: float
    largest_loss: float
    avg_duration_days: float
    
    # Risk metrics
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    
    # History
    trades: List[Trade] = field(default_factory=list)
    daily_returns: List[float] = field(default_factory=list)
    equity_curve: List[Tuple[datetime, float]] = field(default_factory=list)


class StrategySimulator:
    """
    End-to-end strategy simulator combining:
    - Phase 1: Historical market data
    - Phase 2: Signal generation
    - Phase 3: Risk management
    - Phase 4: Trade execution and backtesting
    """
    
    def __init__(self, config: BacktestConfig):
        """Initialize strategy simulator"""
        self.config = config
        self.engine = BacktestEngine(
            initial_capital=config.initial_capital,
            max_portfolio_exposure=config.max_portfolio_exposure,
            max_position_size=config.max_position_size,
            max_open_positions=config.max_open_positions,
            risk_per_trade=config.risk_per_trade,
            commission_percent=config.commission_percent
        )
        
        # Data storage
        self.price_data: Dict[str, pd.DataFrame] = {}
        self.signals_history: List[Dict] = []
        self.trades_executed: List[Trade] = []
        
    def load_historical_data(self, symbol: str, data: pd.DataFrame) -> None:
        """
        Load historical price data for a symbol.
        
        Args:
            symbol: Ticker symbol
            data: DataFrame with OHLCV columns
        """
        if not all(col in data.columns for col in ['Close', 'High', 'Low', 'Volume']):
            raise ValueError("Data must contain Close, High, Low, Volume columns")
        
        self.price_data[symbol] = data.copy()
        logger.info(f"Loaded {len(data)} candles for {symbol}")
    
    def download_data(
        self,
        symbol: str,
        period: str = "1y",
        force_refresh: bool = False
    ) -> None:
        """
        Auto-download and load historical data from yfinance.
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL')
            period: Time period ('1d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            force_refresh: Force re-download even if cached
        """
        logger.info(f"📥 Fetching {symbol} data...")
        df = DataLoader.download_data(
            symbol,
            period=period,
            force_refresh=force_refresh
        )
        self.load_historical_data(symbol, df)
    
    def download_multiple(
        self,
        symbols: List[str],
        period: str = "1y",
        force_refresh: bool = False
    ) -> None:
        """
        Auto-download data for multiple symbols.
        
        Args:
            symbols: List of tickers
            period: Time period
            force_refresh: Force re-download
        """
        data = DataLoader.download_multiple(
            symbols,
            period=period,
            force_refresh=force_refresh
        )
        for symbol, df in data.items():
            if df is not None:
                self.load_historical_data(symbol, df)
    
    def generate_mock_data(self, symbol: str, days: int = 252) -> pd.DataFrame:
        """
        Generate synthetic historical data for testing.
        
        Args:
            symbol: Ticker symbol
            days: Number of days to generate
            
        Returns:
            DataFrame with OHLCV data
        """
        base_prices = {
            'AAPL': 150, 'TSLA': 250, 'MSFT': 380, 
            'GOOGL': 140, 'AMZN': 170
        }
        
        base = base_prices.get(symbol.upper(), 100)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Generate prices with trend and noise
        trend = np.linspace(0, base * 0.2, len(dates))
        noise = np.random.normal(0, base * 0.02, len(dates))
        close_prices = base + trend + noise
        
        df = pd.DataFrame({
            'Date': dates,
            'Open': close_prices * np.random.uniform(0.98, 1.00, len(dates)),
            'High': close_prices * np.random.uniform(1.00, 1.03, len(dates)),
            'Low': close_prices * np.random.uniform(0.97, 0.99, len(dates)),
            'Close': close_prices,
            'Volume': np.random.randint(1000000, 100000000, len(dates))
        })
        df.set_index('Date', inplace=True)
        df = df.sort_index()
        
        logger.info(f"Generated {len(df)} days of mock data for {symbol}")
        return df
    
    def run_simulation(self, verbose: bool = False) -> BacktestResult:
        """
        Run complete strategy simulation.
        
        Args:
            verbose: Print detailed progress
            
        Returns:
            BacktestResult with all metrics
        """
        # Initialize or load data
        if not self.price_data:
            logger.info("No data loaded - generating mock data for all symbols")
            for symbol in self.config.symbols:
                data = self.generate_mock_data(symbol, self.config.lookback_period)
                self.load_historical_data(symbol, data)
        
        # Determine date range
        all_dates = []
        for df in self.price_data.values():
            all_dates.extend(df.index)
        all_dates = sorted(set(all_dates))
        
        start_date = self.config.start_date or all_dates[0]
        end_date = self.config.end_date or all_dates[-1]
        
        if verbose:
            print(f"🔄 Running backtest: {start_date.date()} to {end_date.date()}")
            print(f"📊 Symbols: {', '.join(self.config.symbols)}")
            print(f"💰 Initial capital: ${self.engine.initial_capital:,.2f}")
        
        # Simulation loop - process each day
        for current_date in all_dates:
            if current_date < start_date or current_date > end_date:
                continue
            
            # Get current prices for all symbols
            current_prices = {}
            for symbol in self.config.symbols:
                if symbol in self.price_data:
                    df = self.price_data[symbol]
                    if current_date in df.index:
                        current_prices[symbol] = df.loc[current_date, 'Close']
            
            if not current_prices:
                continue
            
            # Update portfolio with current prices
            self.engine.mark_to_market(current_date, current_prices)
            
            # Generate and execute signals
            signals = self._generate_signals(current_date, current_prices)
            self._execute_signals(current_date, signals)
            
            # Handle exits from existing positions
            self._process_exits(current_date, current_prices)
            
            # Record daily state
            self.engine.record_snapshot(current_date)
        
        # Calculate final metrics
        result = self._calculate_results(start_date, end_date)
        
        if verbose:
            self._print_results(result)
        
        return result
    
    def _generate_signals(self, date: datetime, prices: Dict[str, float]) -> List[Dict]:
        """Generate trading signals for current date"""
        signals = []
        
        for symbol in self.config.symbols:
            if symbol not in self.price_data:
                continue
            
            df = self.price_data[symbol]
            if date not in df.index:
                continue
            
            # Get lookback data
            try:
                idx = df.index.get_loc(date)
                lookback = min(30, idx + 1)  # Up to 30 days
                lookback_data = df.iloc[idx - lookback:idx + 1]
            except:
                continue
            
            if len(lookback_data) < 10:
                continue
            
            # Generate signal (mock implementation - in real use with Phase 2)
            signal = self._generate_mock_signal(symbol, lookback_data)
            if signal:
                signals.append(signal)
        
        return signals
    
    def _generate_mock_signal(self, symbol: str, data: pd.DataFrame) -> Optional[Dict]:
        """
        Generate trading signal based on RSI and MACD indicators (Phase 2).
        
        Combines:
        - RSI (14): Overbought/Oversold momentum
        - MACD: Trend and momentum convergence/divergence
        - SMA: Trend confirmation
        """
        close = data['Close']
        
        if len(close) < 30:
            return None
        
        try:
            # Calculate RSI (14-period standard)
            rsi_calc = RSI(period=14)
            rsi_values = rsi_calc.calculate(close)
            current_rsi = float(rsi_values.iloc[-1]) if not np.isnan(rsi_values.iloc[-1]) else None
            
            # Calculate MACD (12, 26, 9)
            macd_calc = MACD(fast=12, slow=26, signal=9)
            macd_line, signal_line, histogram = macd_calc.calculate(close)
            current_macd = float(macd_line.iloc[-1]) if not np.isnan(macd_line.iloc[-1]) else None
            current_signal = float(signal_line.iloc[-1]) if not np.isnan(signal_line.iloc[-1]) else None
            current_histogram = float(histogram.iloc[-1]) if not np.isnan(histogram.iloc[-1]) else None
            
            # SMA trend confirmation
            sma_20 = close.rolling(20).mean().iloc[-1]
            sma_50 = close.rolling(50).mean().iloc[-1]
            current_price = close.iloc[-1]
            
            # BUY Signal: Multiple confirmations
            # - MACD histogram positive (bullish)
            # - RSI 30-70 (not extreme, has room to run)
            # - Price above SMA20 (in uptrend)
            if (current_macd is not None and current_signal is not None and 
                current_histogram is not None and current_rsi is not None):
                
                macd_bullish = current_macd > current_signal and current_histogram > 0
                rsi_bullish = 30 < current_rsi < 70
                price_above_ma = current_price > sma_20 > sma_50
                
                if macd_bullish and rsi_bullish and price_above_ma:
                    confidence = 75 if current_rsi < 50 else 65  # Higher confidence if RSI not too high
                    return {
                        'symbol': symbol,
                        'action': 'BUY',
                        'price': current_price,
                        'confidence': confidence,
                        'atr': (data['High'].iloc[-1] - data['Low'].iloc[-1]) * 0.5 or 1,
                        'reason': f'MACD Bull + RSI {current_rsi:.0f} + Price>{sma_20:.0f}'
                    }
                
                # SELL Signal: Multiple confirmations
                # - MACD histogram negative (bearish)
                # - RSI in 30-70 range (not extreme)
                # - Price below SMA20 (in downtrend)
                macd_bearish = current_macd < current_signal and current_histogram < 0
                rsi_bearish = 30 < current_rsi < 70
                price_below_ma = current_price < sma_20 < sma_50
                
                if macd_bearish and rsi_bearish and price_below_ma:
                    return {
                        'symbol': symbol,
                        'action': 'SELL',
                        'price': current_price,
                        'confidence': 70,
                        'atr': (data['High'].iloc[-1] - data['Low'].iloc[-1]) * 0.5 or 1,
                        'reason': f'MACD Bear + RSI {current_rsi:.0f} + Price<{sma_20:.0f}'
                    }
        
        except Exception as e:
            logger.warning(f"Signal generation error for {symbol}: {e}")
        
        return None
    
    def _execute_signals(self, date: datetime, signals: List[Dict]) -> None:
        """Execute trading signals"""
        for signal in signals:
            if signal['action'] == 'BUY':
                trade = self.engine.open_trade(
                    ticker=signal['symbol'],
                    date=date,
                    entry_price=signal['price'],
                    signal='BUY',
                    confidence=signal.get('confidence', 50),
                    atr=signal.get('atr', 1)
                )
                if trade:
                    self.trades_executed.append(trade)
                    self.signals_history.append({
                        'date': date,
                        'type': 'BUY',
                        'symbol': signal['symbol'],
                        'price': signal['price'],
                        'reason': signal.get('reason', 'Unknown')
                    })
    
    def _process_exits(self, date: datetime, prices: Dict[str, float]) -> None:
        """
        Process exits from existing positions.
        
        In production would use:
        - Take profit levels
        - Stop loss orders
        - Trailing stops
        - Exit signals from Phase 2
        """
        # Mock: Exit trades at 5% profit or 2% loss
        for ticker in list(self.engine.open_trades.keys()):
            trade = self.engine.open_trades[ticker]
            current_price = prices.get(ticker)
            
            if current_price is None:
                continue
            
            pnl_percent = ((current_price - trade.entry_price) / trade.entry_price) * 100
            
            # Take profit at 5%
            if pnl_percent >= 5:
                closed = self.engine.close_trade(
                    ticker=ticker,
                    date=date,
                    exit_price=current_price,
                    reason='Take Profit'
                )
                if closed:
                    self.signals_history.append({
                        'date': date,
                        'type': 'SELL',
                        'symbol': ticker,
                        'price': current_price,
                        'reason': 'Take Profit',
                        'pnl': closed.pnl
                    })
            
            # Stop loss at -2%
            elif pnl_percent <= -2:
                closed = self.engine.close_trade(
                    ticker=ticker,
                    date=date,
                    exit_price=current_price,
                    reason='Stop Loss'
                )
                if closed:
                    self.signals_history.append({
                        'date': date,
                        'type': 'SELL',
                        'symbol': ticker,
                        'price': current_price,
                        'reason': 'Stop Loss',
                        'pnl': closed.pnl
                    })
    
    def _calculate_results(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """Calculate final backtest results"""
        metrics = self.engine.get_performance_metrics()
        
        # Equity curve
        equity_curve = [
            (snap.date, snap.total_value) 
            for snap in self.engine.portfolio_history
        ]
        
        # Calculate drawdown
        if equity_curve:
            values = [v[1] for v in equity_curve]
            peak = max(values)
            trough = min(values)
            max_drawdown = ((peak - trough) / peak * 100) if peak > 0 else 0
        else:
            max_drawdown = 0
        
        # Daily returns
        daily_returns = []
        if len(self.engine.portfolio_history) > 1:
            for i in range(1, len(self.engine.portfolio_history)):
                prev_value = self.engine.portfolio_history[i-1].total_value
                curr_value = self.engine.portfolio_history[i].total_value
                ret = (curr_value - prev_value) / prev_value if prev_value > 0 else 0
                daily_returns.append(ret)
        
        # Sharpe ratio (assuming 252 trading days and 0% risk-free rate)
        if daily_returns and np.std(daily_returns) > 0:
            avg_daily_return = np.mean(daily_returns)
            sharpe = (avg_daily_return * 252) / (np.std(daily_returns) * np.sqrt(252))
        else:
            sharpe = None
        
        final_value = self.engine.get_portfolio_value()
        total_return = ((final_value - self.config.initial_capital) / self.config.initial_capital * 100)
        
        return BacktestResult(
            config=self.config,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.config.initial_capital,
            final_capital=final_value,
            total_return_percent=total_return,
            max_drawdown_percent=max_drawdown,
            total_trades=metrics.get('total_trades', 0),
            winning_trades=metrics.get('winning_trades', 0),
            losing_trades=metrics.get('losing_trades', 0),
            win_rate_percent=metrics.get('win_rate_percent', 0),
            gross_wins=metrics.get('gross_wins', 0),
            gross_losses=metrics.get('gross_losses', 0),
            net_pnl=metrics.get('total_pnl', 0),
            profit_factor=metrics.get('profit_factor', 0),
            avg_winner=metrics.get('avg_winner', 0),
            avg_loser=metrics.get('avg_loser', 0),
            largest_win=metrics.get('largest_win', 0),
            largest_loss=metrics.get('largest_loss', 0),
            avg_duration_days=metrics.get('avg_duration_days', 0),
            sharpe_ratio=sharpe,
            trades=self.engine.closed_trades,
            daily_returns=daily_returns,
            equity_curve=equity_curve
        )
    
    def _print_results(self, result: BacktestResult) -> None:
        """Print backtest results"""
        print("\n" + "="*80)
        print("BACKTEST RESULTS")
        print("="*80)
        
        print(f"\n📊 Performance:")
        print(f"  Initial Capital:    ${result.initial_capital:>15,.2f}")
        print(f"  Final Capital:      ${result.final_capital:>15,.2f}")
        print(f"  Total Return:       {result.total_return_percent:>15.2f}%")
        print(f"  Max Drawdown:       {result.max_drawdown_percent:>15.2f}%")
        if result.sharpe_ratio:
            print(f"  Sharpe Ratio:       {result.sharpe_ratio:>15.2f}")
        
        print(f"\n📈 Trade Statistics:")
        print(f"  Total Trades:       {result.total_trades:>15}")
        print(f"  Winning Trades:     {result.winning_trades:>15}")
        print(f"  Losing Trades:      {result.losing_trades:>15}")
        print(f"  Win Rate:           {result.win_rate_percent:>15.1f}%")
        
        print(f"\n💹 Profitability:")
        print(f"  Gross Wins:         ${result.gross_wins:>15,.2f}")
        print(f"  Gross Losses:       ${result.gross_losses:>15,.2f}")
        print(f"  Net P&L:            ${result.net_pnl:>15,.2f}")
        print(f"  Profit Factor:      {result.profit_factor:>15.2f}")
        
        print(f"\n🎯 Trade Details:")
        print(f"  Avg Winner:         ${result.avg_winner:>15,.2f}")
        print(f"  Avg Loser:          ${result.avg_loser:>15,.2f}")
        print(f"  Largest Win:        ${result.largest_win:>15,.2f}")
        print(f"  Largest Loss:       ${result.largest_loss:>15,.2f}")
        print(f"  Avg Duration:       {result.avg_duration_days:>15.1f} days")
        
        print("\n" + "="*80)
    
    def get_summary(self) -> Dict:
        """Get simulation summary"""
        final_value = self.engine.get_portfolio_value()
        metrics = self.engine.get_performance_metrics()
        
        return {
            'initial_capital': self.config.initial_capital,
            'final_capital': final_value,
            'total_return': ((final_value - self.config.initial_capital) / self.config.initial_capital * 100),
            'total_trades': metrics.get('total_trades', 0),
            'win_rate': metrics.get('win_rate_percent', 0),
            'profit_factor': metrics.get('profit_factor', 0),
            'trades': self.engine.closed_trades,
            'signals_count': len(self.signals_history)
        }
