import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

def load_and_process_data(file_path):
    """
    Load the price data and calculate spread and z-score
    """
    # Read the CSV file
    df = pd.read_csv(file_path, sep=';')
    
    # Convert timestamp to datetime (assuming it's in milliseconds)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Pivot the data to get prices for each product at each timestamp
    price_pivot = df.pivot_table(
        index=['day', 'timestamp', 'datetime'], 
        columns='product', 
        values='mid_price', 
        aggfunc='first'
    ).reset_index()
    
    # Calculate synthetic price: 4*chocolate + 6*strawberries + 1*rose
    price_pivot['synthetic'] = (
        4 * price_pivot['CHOCOLATE'] + 
        6 * price_pivot['STRAWBERRIES'] + 
        1 * price_pivot['ROSES']
    )
    
    # Calculate spread: basket - synthetic
    price_pivot['spread'] = price_pivot['GIFT_BASKET'] - price_pivot['synthetic']
    
    # Remove rows with NaN values
    price_pivot = price_pivot.dropna(subset=['spread'])
    
    return price_pivot

def calculate_modified_zscore(spread_values, hardcoded_mean=370, window_size=100):
    """
    Calculate modified z-score using hardcoded mean and rolling window standard deviation
    """
    # Calculate rolling standard deviation
    rolling_std = spread_values.rolling(window=window_size, min_periods=1).std()
    
    # Calculate z-score: (spread - hardcoded_mean) / rolling_std
    z_score = (spread_values - hardcoded_mean) / rolling_std
    
    return z_score

def calculate_returns(df, z_score_threshold=5.0):
    """
    Calculate trading returns based on z-score signals
    """
    # Identify trading signals
    df['signal'] = 0
    df.loc[df['z_score'] > z_score_threshold, 'signal'] = -1  # Sell spread
    df.loc[df['z_score'] < -z_score_threshold, 'signal'] = 1   # Buy spread
    
    # Calculate position changes
    df['position_change'] = df['signal'].diff()
    
    # Calculate cumulative position
    df['position'] = df['signal'].cumsum()
    
    # Calculate PnL (simplified - assuming we can trade at mid prices)
    df['pnl'] = df['position'].shift(1) * df['spread'].diff()
    df['cumulative_pnl'] = df['pnl'].cumsum()
    
    return df

def create_clean_visualization(df, z_score_threshold=5.0, start_idx=5000, end_idx=10000):
    """
    Create clean dual-axis visualization with returns plot
    """
    # Filter data to specified index range
    df_filtered = df.iloc[start_idx:end_idx].copy()
    df_filtered = df_filtered.reset_index(drop=True)
    
    # Calculate returns
    df_filtered = calculate_returns(df_filtered, z_score_threshold)
    
    # Set up the plot with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[2, 1])
    
    # Create second y-axis for the first subplot
    ax1_twin = ax1.twinx()
    
    # Plot spread on left axis
    line1 = ax1.plot(df_filtered.index, df_filtered['spread'], 'b-', linewidth=1, label='Spread', alpha=0.8)
    ax1.set_ylabel('Spread Price', fontsize=12, color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.grid(True, alpha=0.3)
    
    # Plot z-score on right axis
    line2 = ax1_twin.plot(df_filtered.index, df_filtered['z_score'], 'purple', linewidth=1, label='Z Score', alpha=0.8)
    ax1_twin.set_ylabel('Z-Score', fontsize=12, color='purple')
    ax1_twin.tick_params(axis='y', labelcolor='purple')
    
    # Add horizontal lines for thresholds and means
    # Z-score thresholds (teal lines)
    ax1_twin.axhline(y=z_score_threshold, color='teal', linestyle='-.', linewidth=2, alpha=0.8, label=f'Upper Threshold ({z_score_threshold})')
    ax1_twin.axhline(y=-z_score_threshold, color='teal', linestyle='-.', linewidth=2, alpha=0.8, label=f'Lower Threshold ({-z_score_threshold})')
    
    # Z-score mean (0)
    ax1_twin.axhline(y=0, color='lightblue', linestyle='--', linewidth=1.5, alpha=0.8, label='Z-score Mean (0)')
    
    # Spread mean (~370)
    spread_mean = 370
    ax1.axhline(y=spread_mean, color='lightblue', linestyle='--', linewidth=1.5, alpha=0.8, label=f'Spread Mean ({spread_mean})')
    
    # Create combined legend for first subplot
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)
    
    # Set title for first subplot
    ax1.set_title(f'Spread Prices and Modified Z-Score with Trading Thresholds\nRound 3 Gift Basket Mean Reversion Strategy - Threshold: ±{z_score_threshold}', 
                  fontsize=14, fontweight='bold', pad=20)
    
    # Plot cumulative returns on second subplot
    ax2.plot(df_filtered.index, df_filtered['cumulative_pnl'], 'g-', linewidth=2, label='Cumulative PnL', alpha=0.8)
    ax2.set_xlabel('Index', fontsize=12)
    ax2.set_ylabel('Cumulative PnL', fontsize=12, color='g')
    ax2.tick_params(axis='y', labelcolor='g')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left', fontsize=10)
    ax2.set_title('Cumulative Trading Returns', fontsize=12, fontweight='bold')
    fig.text(0.01,0.01,
    "Spread and modified z-score of the Round 3 gift basket mean-reversion strategy over time. " \
    "The top image shows the gift-basket spread (basket - synthetic value of 4xCHOCOLATE + 6xSTRAWBERRIES + 1xROSES) together with its modified z-score, " \
    "where horizontal lines mark the hard-coded spread mean (~370) and trading thresholds at ±5 standard deviations used to trigger buy/sell signals. " \
    "The bottom panel plots the cumulative PnL generated by following these mean-reversion signals, illustrating how extreme deviations of the spread from its long-run mean translate into trading performance." \
    " The Currency used in this simulation is Shells.",
    wrap=True
    )
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0.05, 1, 1])    
    return fig, df_filtered

def print_analysis_summary(df_filtered, z_score_threshold):
    """
    Print analysis summary for the filtered data
    """
    print("=" * 60)
    print("ROUND 3 GIFT BASKET MEAN REVERSION STRATEGY ANALYSIS")
    print("=" * 60)
    
    # Basic statistics
    print(f"\nDATA RANGE: Index {df_filtered.index[0]} to {df_filtered.index[-1]}")
    print(f"Data points: {len(df_filtered):,}")
    print(f"Spread mean: {df_filtered['spread'].mean():.2f}")
    print(f"Spread std: {df_filtered['spread'].std():.2f}")
    print(f"Spread min: {df_filtered['spread'].min():.2f}")
    print(f"Spread max: {df_filtered['spread'].max():.2f}")
    
    # Trading signals
    buy_signals = len(df_filtered[df_filtered['signal'] == 1])
    sell_signals = len(df_filtered[df_filtered['signal'] == -1])
    total_signals = buy_signals + sell_signals
    
    print(f"\nTRADING SIGNALS (Threshold: ±{z_score_threshold}):")
    print(f"Buy signals: {buy_signals:,}")
    print(f"Sell signals: {sell_signals:,}")
    print(f"Total signals: {total_signals:,}")
    print(f"Signal frequency: {total_signals/len(df_filtered)*100:.2f}%")
    
    # Position analysis
    max_position = df_filtered['position'].max()
    min_position = df_filtered['position'].min()
    avg_position = df_filtered['position'].mean()
    
    print(f"\nPOSITION ANALYSIS:")
    print(f"Max position: {max_position}")
    print(f"Min position: {min_position}")
    print(f"Average position: {avg_position:.2f}")
    
    # PnL analysis
    final_pnl = df_filtered['cumulative_pnl'].iloc[-1]
    max_pnl = df_filtered['cumulative_pnl'].max()
    min_pnl = df_filtered['cumulative_pnl'].min()
    
    print(f"\nPROFIT & LOSS:")
    print(f"Final PnL: {final_pnl:.2f}")
    print(f"Max PnL: {max_pnl:.2f}")
    print(f"Min PnL: {min_pnl:.2f}")
    print(f"PnL range: {max_pnl - min_pnl:.2f}")
    
    # Risk metrics
    returns = df_filtered['pnl'].dropna()
    if len(returns) > 0 and returns.std() > 0:
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)
        print(f"\nRISK METRICS:")
        print(f"Daily return std: {returns.std():.2f}")
        print(f"Sharpe ratio (annualized): {sharpe_ratio:.2f}")
    
    print("\n" + "=" * 60)

def main():
    """
    Main function to run the clean visualization
    """
    # File path
    file_path = './data-vis-project/imc-data/round3/data/prices_round_3_day_0.csv'
    
    print("Loading and processing data...")
    df = load_and_process_data(file_path)
    
    print("Calculating modified z-score...")
    df['z_score'] = calculate_modified_zscore(df['spread'], hardcoded_mean=370, window_size=100)
    
    print("Creating clean visualization...")
    fig, df_filtered = create_clean_visualization(df, z_score_threshold=5.0, start_idx=5000, end_idx=10000)
    
    # Save the plot
    output_path = './data-vis-project/round3-vis/spread_zscore_clean.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Clean visualization saved to: {output_path}")
    
    # Print analysis summary
    print_analysis_summary(df_filtered, z_score_threshold=5.0)
    
    plt.show()

if __name__ == "__main__":
    main()

