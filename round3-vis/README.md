# Round 3 Gift Basket Mean Reversion Strategy Visualization

This folder contains the clean visualization code for the Round 3 gift basket mean reversion strategy analysis from the IMC Trading Competition.

## Overview

In Round 3, gift baskets were introduced with the composition:
- 4 chocolate bars
- 6 strawberries  
- 1 rose

The strategy focused on trading the **spread** between the gift basket price and its synthetic equivalent:
```
spread = basket_price - synthetic_price
where synthetic_price = 4 × chocolate + 6 × strawberries + 1 × rose
```

## Strategy Details

The mean reversion strategy was based on two key observations:

1. **Mean Reversion**: The spread price oscillated around ~370 across all three days of historical data
2. **Modified Z-Score**: Used a hardcoded mean (370) and rolling window standard deviation to create adaptive trading signals

### Trading Logic

- **Buy spreads** (long basket, short synthetic) when z-score < -5.0
- **Sell spreads** (short basket, long synthetic) when z-score > +5.0

**Optimal Threshold**: After analysis, ±5.0 provides the best balance of signal frequency (23.08%) and performance, avoiding both over-trading and under-trading.

The modified z-score calculation:
```
z_score = (spread - 370) / rolling_std(window_size=100)
```

## Files

- `spread_zscore_clean.py`: Main visualization script with optimal thresholds
- `spread_zscore_clean.png`: Clean dual-axis plot showing spread prices, z-score, and cumulative returns
- `README.md`: This documentation

## Data Statistics (Index Range 5000-10000)

- **Data points**: 5,000
- **Spread mean**: 384.85
- **Spread std**: 74.02
- **Spread range**: 180.00 - 542.00
- **Trading signals**: 1,154 (23.08% frequency)
- **Final PnL**: 109,302.50
- **Max PnL**: 193,285.00
- **Sharpe ratio**: 0.10

## Visualization Features

The plot shows:
- **Top panel**: 
  - Blue line: Spread prices (left y-axis)
  - Purple line: Modified z-score (right y-axis)
  - Teal dash-dot lines: Trading thresholds at ±5.0
  - Light blue dashed lines: Mean values (spread mean at 370, z-score mean at 0)
- **Bottom panel**: 
  - Green line: Cumulative trading returns

## Running the Code

```bash
python spread_zscore_clean.py
```

The script will:
1. Load the Round 3 price data
2. Calculate the basket spread
3. Compute the modified z-score
4. Generate the clean dual-axis visualization with returns
5. Save the plot as PNG
6. Display statistics for the selected index range

## Performance Analysis

### Threshold Optimization Results
- **±2**: 62.71% frequency, 578,058 PnL (too noisy)
- **±3**: 46.92% frequency, 494,443 PnL (still noisy)
- **±5**: 26.24% frequency, 353,283 PnL (optimal balance)
- **±7**: 12.68% frequency, 187,379 PnL (reasonable)
- **±15**: 0.81% frequency, 17,344 PnL (too conservative)

### Historical Performance (Original Analysis)
- **Backtest PnL**: ~135k seashells
- **Actual PnL**: 111k seashells (significant slippage)
- **Rank**: #2 overall in Round 3

**Key Insight**: The optimal threshold of ±5.0 provides a good balance between signal frequency and performance, avoiding both over-trading (too tight thresholds) and under-trading (too wide thresholds).