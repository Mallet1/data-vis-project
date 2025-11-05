https://github.com/ericcccsliu/imc-prosperity-2?tab=readme-ov-file#round-3%EF%B8%8F%E2%83%A3

stanford 2023:  
https://github.com/ShubhamAnandJain/IMC-Prosperity-2023-Stanford-Cardinal

# Market Microstructure Mini-Study - Basket Fair Value, Mispricing, and Order-Flow Signals

This repo analyzes intraday pricing and order book dynamics for four instruments:
**CHOCOLATE, STRAWBERRIES, ROSES,** and **GIFT_BASKET** (a bundle of the first three).
We explore co-movement, basket fair value, mispricing (spread & z-score), and simple
order-flow signals (microprice and volume imbalance).

## Files
- `imc-data` - This folder contains all csv files with the stock data
- `round4_data_visualization.ipynb` - Reproducible notebook with all plots and commentary.
- `prices_round_3_day_0.csv` - Semicolon-delimited L1–L3 quotes and mid prices for one trading day.
- `round3-vis` - Contains python files and visualization for round 3 basket visualization.
- `mid_price_day_.png` - Contains mid price changes for amethysts and starfruits pertaining to round 0.
- `mean_reversion_strategy_STARFRUIT_day_-2.png` - Visualization that shows a strategy for trading on starfruits and the profits associated with the strategy. 

## Data Schema (selected columns)

- `day`, `timestamp` (ms)
- `product` - {CHOCOLATE, STRAWBERRIES, ROSES, GIFT_BASKET}
- `bid_price_1..3`, `bid_volume_1..3`
- `ask_price_1..3`, `ask_volume_1..3`
- `mid_price`
- `profit_and_loss`

## Questions We Answer With Visuals

1. **Co-movement & Volatility** - Rebased price paths to compare trend and variance.
2. **Fair Value Check** - Does GIFT_BASKET align with a synthetic basket of its components?
3. **Mispricing & Z-Score** - Spread time series and z-score bands (|z| > 2) for mean-reversion cues.
4. **Order-Flow Pressure** - Microprice tendencies relative to bid/ask volume weights.
5. **Impact Curve** - Top-of-book volume imbalance vs. short-horizon future returns.
6. **Market Quality** - Typical spreads and depth asymmetry when mispricing is elevated.

## Intended audience:

- Primary: Quantitative researchers, algorithmic trading engineers, and data-driven market microstructure analysts (e.g., trading-competition or market-making coursework).
- Secondary: Data scientists with market data (order books, mid-price, spreads).
