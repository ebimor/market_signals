"""
Technical Indicators Module

Implements various technical indicators used for trading signal generation:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- EMA (Exponential Moving Average)
- ATR (Average True Range)
- Bollinger Bands
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class RSI:
    """
    Relative Strength Index (RSI) Indicator
    
    RSI measures momentum by comparing the magnitude of recent gains to recent losses.
    RSI ranges from 0 to 100:
    - Above 70: Overbought (potential sell signal)
    - Below 30: Oversold (potential buy signal)
    - 30-70: Neutral zone
    
    Formula:
        RS = Average Gain / Average Loss
        RSI = 100 - (100 / (1 + RS))
    
    Standard: 14-period RSI
    """
    
    def __init__(self, period: int = 14):
        """
        Initialize RSI calculator.
        
        Args:
            period: Number of periods for RSI calculation (default: 14)
        """
        self.period = period
        logger.info(f"RSI initialized with period={period}")
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        """
        Calculate RSI for a series of prices.
        
        Args:
            prices: pd.Series of closing prices, sorted by date ascending
            
        Returns:
            pd.Series of RSI values (same length as input)
            
        Example:
            >>> prices = pd.Series([44, 44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84])
            >>> rsi = RSI(14)
            >>> rsi_values = rsi.calculate(prices)
        """
        if len(prices) < self.period + 1:
            logger.warning(f"Not enough data for RSI calculation. Need {self.period + 1}, got {len(prices)}")
            return pd.Series([np.nan] * len(prices), index=prices.index)
        
        # Calculate price changes
        deltas = prices.diff()
        
        # Separate gains and losses
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)
        
        # Calculate average gains and losses using exponential smoothing
        # First average (simple average)
        avg_gain = gains.rolling(window=self.period).mean()
        avg_loss = losses.rolling(window=self.period).mean()
        
        # Subsequent averages (exponential smoothing)
        for i in range(self.period, len(prices)):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (self.period - 1) + gains.iloc[i]) / self.period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (self.period - 1) + losses.iloc[i]) / self.period
        
        # Calculate RS (Relative Strength)
        rs = avg_gain / avg_loss
        
        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))
        
        # Replace inf and -inf with NaN
        rsi = rsi.replace([np.inf, -np.inf], np.nan)
        
        logger.debug(f"RSI calculated for {len(prices)} price points")
        return rsi
    
    def get_signal(self, rsi_value: float) -> str:
        """
        Get trading signal based on RSI value.
        
        Args:
            rsi_value: RSI value (0-100)
            
        Returns:
            Signal: 'BUY' (RSI < 30), 'SELL' (RSI > 70), or 'HOLD' (30-70)
        """
        if pd.isna(rsi_value):
            return 'HOLD'
        elif rsi_value < 30:
            return 'BUY'
        elif rsi_value > 70:
            return 'SELL'
        else:
            return 'HOLD'
    
    def get_confidence(self, rsi_value: float) -> float:
        """
        Get confidence score (0-100) based on RSI extremity.
        
        Args:
            rsi_value: RSI value (0-100)
            
        Returns:
            Confidence score (0-100)
            - Extreme values (< 20 or > 80) = High confidence (80-100)
            - Strong signals (< 30 or > 70) = Medium confidence (60-80)
            - Weak signals (30-70) = Low confidence (0-40)
        """
        if pd.isna(rsi_value):
            return 0.0
        
        if rsi_value < 20 or rsi_value > 80:
            return min(100, 80 + (abs(rsi_value - 50) - 30))
        elif rsi_value < 30 or rsi_value > 70:
            return min(100, 60 + abs(rsi_value - 50) / 2)
        else:
            return max(0, 40 - abs(rsi_value - 50) / 2)


class EMA:
    """
    Exponential Moving Average (EMA)
    
    EMA gives more weight to recent prices, reacting faster to price changes
    compared to Simple Moving Average (SMA).
    
    Uses: Trend identification and confirmation
    """
    
    def __init__(self, period: int = 20):
        """
        Initialize EMA calculator.
        
        Args:
            period: Number of periods for EMA calculation (default: 20)
        """
        self.period = period
        self.multiplier = 2 / (period + 1)
        logger.info(f"EMA initialized with period={period}, multiplier={self.multiplier:.6f}")
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        """
        Calculate EMA for a series of prices.
        
        Args:
            prices: pd.Series of closing prices, sorted by date ascending
            
        Returns:
            pd.Series of EMA values
        """
        if len(prices) < self.period:
            logger.warning(f"Not enough data for EMA calculation. Need {self.period}, got {len(prices)}")
            return pd.Series([np.nan] * len(prices), index=prices.index)
        
        ema = prices.ewm(span=self.period, adjust=False).mean()
        logger.debug(f"EMA calculated for {len(prices)} price points")
        return ema


class ATR:
    """
    Average True Range (ATR)
    
    ATR measures volatility by calculating the average of true ranges over a period.
    Higher ATR = Higher volatility
    Lower ATR = Lower volatility
    
    Uses: Position sizing, stop-loss calculation
    """
    
    def __init__(self, period: int = 14):
        """
        Initialize ATR calculator.
        
        Args:
            period: Number of periods for ATR calculation (default: 14)
        """
        self.period = period
        logger.info(f"ATR initialized with period={period}")
    
    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """
        Calculate ATR for price data.
        
        Args:
            high: pd.Series of high prices
            low: pd.Series of low prices
            close: pd.Series of close prices
            
        Returns:
            pd.Series of ATR values
        """
        if len(high) < self.period:
            logger.warning(f"Not enough data for ATR. Need {self.period}, got {len(high)}")
            return pd.Series([np.nan] * len(high), index=high.index)
        
        # Calculate True Range
        # TR = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR as EMA of TR
        atr = tr.ewm(span=self.period, adjust=False).mean()
        logger.debug(f"ATR calculated for {len(high)} price points")
        return atr


class BollingerBands:
    """
    Bollinger Bands
    
    Consists of:
    - Middle Band: 20-period SMA
    - Upper Band: Middle Band + (2 * Standard Deviation)
    - Lower Band: Middle Band - (2 * Standard Deviation)
    
    Uses: Support/Resistance levels, volatility measurement
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        """
        Initialize Bollinger Bands calculator.
        
        Args:
            period: Number of periods for SMA (default: 20)
            std_dev: Number of standard deviations (default: 2.0)
        """
        self.period = period
        self.std_dev = std_dev
        logger.info(f"Bollinger Bands initialized with period={period}, std_dev={std_dev}")
    
    def calculate(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands for a series of prices.
        
        Args:
            prices: pd.Series of closing prices
            
        Returns:
            Tuple of (upper_band, middle_band, lower_band) as pd.Series
        """
        if len(prices) < self.period:
            logger.warning(f"Not enough data for Bollinger Bands. Need {self.period}, got {len(prices)}")
            empty = pd.Series([np.nan] * len(prices), index=prices.index)
            return empty, empty, empty
        
        # Middle band (SMA)
        middle = prices.rolling(window=self.period).mean()
        
        # Standard deviation
        std = prices.rolling(window=self.period).std()
        
        # Upper and lower bands
        upper = middle + (std * self.std_dev)
        lower = middle - (std * self.std_dev)
        
        logger.debug(f"Bollinger Bands calculated for {len(prices)} price points")
        return upper, middle, lower


class MACD:
    """
    MACD (Moving Average Convergence Divergence)
    
    Consists of:
    - MACD Line: 12-period EMA - 26-period EMA
    - Signal Line: 9-period EMA of MACD Line
    - Histogram: MACD Line - Signal Line
    
    Uses: Trend confirmation, momentum measurement
    """
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        """
        Initialize MACD calculator.
        
        Args:
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line EMA period (default: 9)
        """
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.fast_ema = EMA(fast)
        self.slow_ema = EMA(slow)
        self.signal_ema = EMA(signal)
        logger.info(f"MACD initialized with fast={fast}, slow={slow}, signal={signal}")
    
    def calculate(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD for a series of prices.
        
        Args:
            prices: pd.Series of closing prices
            
        Returns:
            Tuple of (macd_line, signal_line, histogram) as pd.Series
        """
        if len(prices) < self.slow + 1:
            logger.warning(f"Not enough data for MACD. Need {self.slow + 1}, got {len(prices)}")
            empty = pd.Series([np.nan] * len(prices), index=prices.index)
            return empty, empty, empty
        
        # Calculate EMAs
        fast_ema = self.fast_ema.calculate(prices)
        slow_ema = self.slow_ema.calculate(prices)
        
        # MACD Line
        macd_line = fast_ema - slow_ema
        
        # Signal Line
        signal_line = self.signal_ema.calculate(macd_line)
        
        # Histogram
        histogram = macd_line - signal_line
        
        logger.debug(f"MACD calculated for {len(prices)} price points")
        return macd_line, signal_line, histogram


class SignalGenerator:
    """
    Composite Signal Generator
    
    Combines all 5 technical indicators (RSI, MACD, EMA, ATR, Bollinger Bands)
    to generate composite trading signals with confidence scoring.
    
    Uses a voting system where each indicator "votes" for BUY, SELL, or HOLD.
    The final signal is determined by majority vote, with confidence based on
    indicator agreement.
    """
    
    def __init__(self):
        """Initialize signal generator with all indicators."""
        self.rsi = RSI(period=14)
        self.macd = MACD(fast=12, slow=26, signal=9)
        self.ema = EMA(period=20)
        self.atr = ATR(period=14)
        self.bb = BollingerBands(period=20, std_dev=2.0)
        logger.info("SignalGenerator initialized with all indicators")
    
    def generate_signal(self, data: pd.DataFrame) -> Dict[str, any]:
        """
        Generate composite signal from price data.
        
        Args:
            data: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
            
        Returns:
            Dictionary with composite signal and component analysis
            
        Example:
            >>> generator = SignalGenerator()
            >>> signal = generator.generate_signal(price_data)
            >>> print(signal['signal'])  # 'BUY', 'SELL', or 'HOLD'
            >>> print(signal['confidence'])  # 0-100
        """
        if len(data) < 30:
            logger.warning(f"Insufficient data for signal generation. Need 30+, got {len(data)}")
            return {
                "signal": "HOLD",
                "confidence": 0,
                "error": "Insufficient data"
            }
        
        # Calculate all indicators
        rsi_values = self.rsi.calculate(data['Close'])
        macd_line, signal_line, histogram = self.macd.calculate(data['Close'])
        ema_values = self.ema.calculate(data['Close'])
        atr_values = self.atr.calculate(data['High'], data['Low'], data['Close'])
        upper_bb, middle_bb, lower_bb = self.bb.calculate(data['Close'])
        
        # Get current values
        current_price = float(data['Close'].iloc[-1])
        current_rsi = float(rsi_values.iloc[-1]) if not pd.isna(rsi_values.iloc[-1]) else None
        current_macd = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None
        current_signal_line = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None
        current_histogram = float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None
        current_ema = float(ema_values.iloc[-1]) if not pd.isna(ema_values.iloc[-1]) else None
        current_atr = float(atr_values.iloc[-1]) if not pd.isna(atr_values.iloc[-1]) else None
        current_upper = float(upper_bb.iloc[-1]) if not pd.isna(upper_bb.iloc[-1]) else None
        current_middle = float(middle_bb.iloc[-1]) if not pd.isna(middle_bb.iloc[-1]) else None
        current_lower = float(lower_bb.iloc[-1]) if not pd.isna(lower_bb.iloc[-1]) else None
        
        # Get individual signals (voting)
        votes = {"BUY": 0, "SELL": 0, "HOLD": 0}
        scores = {}
        
        # RSI vote (weight: 20%)
        rsi_signal = self.rsi.get_signal(current_rsi) if current_rsi else "HOLD"
        rsi_confidence = self.rsi.get_confidence(current_rsi) if current_rsi else 0
        votes[rsi_signal] += 1
        scores["rsi"] = {
            "value": round(current_rsi, 2) if current_rsi else None,
            "signal": rsi_signal,
            "confidence": round(rsi_confidence, 1)
        }
        
        # MACD vote (weight: 20%)
        if current_histogram is not None:
            if current_histogram > 0 and current_macd > current_signal_line:
                macd_signal = "BUY"
                macd_confidence = min(100, abs(current_histogram) * 100 + 30)
            elif current_histogram < 0 and current_macd < current_signal_line:
                macd_signal = "SELL"
                macd_confidence = min(100, abs(current_histogram) * 100 + 30)
            else:
                macd_signal = "HOLD"
                macd_confidence = abs(current_histogram) * 50
        else:
            macd_signal = "HOLD"
            macd_confidence = 0
        
        votes[macd_signal] += 1
        scores["macd"] = {
            "value": round(current_histogram, 4) if current_histogram else None,
            "signal": macd_signal,
            "confidence": round(macd_confidence, 1)
        }
        
        # EMA vote (weight: 20%)
        if current_ema:
            price_diff = current_price - current_ema
            price_diff_pct = (price_diff / current_ema) * 100
            if price_diff_pct > 2:
                ema_signal = "BUY"
                ema_confidence = min(100, price_diff_pct * 10)
            elif price_diff_pct < -2:
                ema_signal = "SELL"
                ema_confidence = min(100, abs(price_diff_pct) * 10)
            else:
                ema_signal = "HOLD"
                ema_confidence = abs(price_diff_pct) * 20
        else:
            ema_signal = "HOLD"
            ema_confidence = 0
        
        votes[ema_signal] += 1
        scores["ema"] = {
            "value": round(current_ema, 2) if current_ema else None,
            "signal": ema_signal,
            "confidence": round(ema_confidence, 1)
        }
        
        # Bollinger Bands vote (weight: 20%)
        if current_upper and current_lower:
            bb_range = current_upper - current_lower
            price_position = (current_price - current_lower) / bb_range
            
            if price_position > 0.8:
                bb_signal = "SELL"
                bb_confidence = min(100, (price_position - 0.8) * 500)
            elif price_position < 0.2:
                bb_signal = "BUY"
                bb_confidence = min(100, (0.2 - price_position) * 500)
            else:
                bb_signal = "HOLD"
                bb_confidence = abs(price_position - 0.5) * 100
        else:
            bb_signal = "HOLD"
            bb_confidence = 0
        
        votes[bb_signal] += 1
        scores["bb"] = {
            "value": round(price_position * 100, 1) if current_upper and current_lower else None,
            "signal": bb_signal,
            "confidence": round(bb_confidence, 1)
        }
        
        # ATR doesn't vote on direction, but influences confidence (volatility factor)
        if current_atr and current_price:
            atr_pct = (current_atr / current_price) * 100
            volatility_factor = 0.7 if atr_pct < 2 else 1.0 if atr_pct < 3 else 1.3
        else:
            volatility_factor = 1.0
        
        scores["atr"] = {
            "value": round(current_atr, 2) if current_atr else None,
            "atr_pct": round(atr_pct, 2) if current_atr and current_price else None,
            "volatility_factor": round(volatility_factor, 2)
        }
        
        # Determine final signal from votes
        max_votes = max(votes.values())
        final_signals = [signal for signal, count in votes.items() if count == max_votes]
        
        if "BUY" in final_signals or (len(final_signals) > 1 and "HOLD" in final_signals):
            final_signal = "BUY" if "BUY" in final_signals else "HOLD"
        elif "SELL" in final_signals:
            final_signal = "SELL"
        else:
            final_signal = "HOLD"
        
        # Calculate confidence
        avg_confidence = (scores["rsi"]["confidence"] + scores["macd"]["confidence"] + 
                         scores["ema"]["confidence"] + scores["bb"]["confidence"]) / 4
        
        # Agreement bonus: if all indicators agree, boost confidence
        if len(final_signals) == 1:
            agreement_bonus = 20
        elif len(final_signals) == 2:
            agreement_bonus = 10
        else:
            agreement_bonus = 0
        
        final_confidence = min(100, avg_confidence + agreement_bonus)
        final_confidence *= volatility_factor
        final_confidence = min(100, final_confidence)
        
        logger.debug(f"Signal generated: {final_signal} ({final_confidence:.1f}% confidence)")
        
        return {
            "signal": final_signal,
            "confidence": round(final_confidence, 1),
            "votes": votes,
            "components": scores,
            "volatility_factor": round(volatility_factor, 2),
        }


# Convenience functions for quick access


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Quick RSI calculation."""
    rsi_calc = RSI(period)
    return rsi_calc.calculate(prices)


def calculate_ema(prices: pd.Series, period: int = 20) -> pd.Series:
    """Quick EMA calculation."""
    ema_calc = EMA(period)
    return ema_calc.calculate(prices)


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Quick ATR calculation."""
    atr_calc = ATR(period)
    return atr_calc.calculate(high, low, close)


def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Quick Bollinger Bands calculation."""
    bb = BollingerBands(period, std_dev)
    return bb.calculate(prices)


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Quick MACD calculation."""
    macd_calc = MACD(fast, slow, signal)
    return macd_calc.calculate(prices)
