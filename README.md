https://github.com/ericcccsliu/imc-prosperity-2?tab=readme-ov-file#round-3%EF%B8%8F%E2%83%A3

stanford 2023:  
https://github.com/ShubhamAnandJain/IMC-Prosperity-2023-Stanford-Cardinal

## 1. Data Set

The dataset comes from the IMC Prosperity trading competition, an algorithmic trading challenge. Data is stored locally in the `imc-data/` directory, organized by round (round1 through round5)

## 2. Questions Answered

The visualizations address trading strategy questions:

- **Co-movement & volatility**: How do assets move relative to each other? Which instruments are more volatile?
- **Mispricing & mean-reversion**: Is GIFT_BASKET fairly priced relative to its synthetic value (4×CHOCOLATE + 6×STRAWBERRIES + 1×ROSE)? When does the spread z-score revert to mean?
- **Order-flow pressure**: Does microprice (volume-weighted bid/ask) predict future mid-price movements?
- **Volume imbalance**: Does top-of-book volume imbalance correlate with short-horizon returns?
- **Market quality**: What are typical spreads and liquidity depths, and do they widen during mispricings?

## 3. Intended Audience

**Primary**: Quantitative researchers, algorithmic trading engineers, trading competition participants, and students.

**Secondary**: Data scientists familiar with market data structures (order books, mid-prices, spreads).

## 4. Working Code Artifacts

This repository contains working Jupyter notebooks and Python scripts organized by round:

- **round4-vis/round4_data_visualization.ipynb**: Main Jupyter notebook analyzing Round 4 data with comprehensive visualizations
- **round3-vis/spread_zscore_clean.py**: Python script visualizing mean reversion strategy for gift basket spread trading
- **round1-vis/mean_reversion_strategy_visualization.py**: Python script for Round 1 strategy visualization
- **round1-vis/visualize_mid_price.py**: Python script for mid-price visualization

### Setup and Running

1. **Prerequisites**: Python 3.x with pandas, numpy, matplotlib
2. **Install dependencies**: `pip install pandas numpy matplotlib`

Data files are expected in `imc-data/round*/data/` directories relative to each script's location.
