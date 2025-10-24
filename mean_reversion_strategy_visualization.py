#!/usr/bin/env python3
"""
Trading Strategy Visualization for IMC round1 data.
Implements a simple mean reversion strategy and visualizes buy/sell signals.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def load_data():
    """Load and combine all three CSV files from round1/data directory."""
    data_dir = Path("imc-data/round1/data")
    
    csv_files = [
        "prices_round_1_day_-2.csv",
        "prices_round_1_day_-1.csv", 
        "prices_round_1_day_0.csv"
    ]
    
    all_data = []
    
    for file in csv_files:
        file_path = data_dir / file
        print(f"Loading {file}...")
        df = pd.read_csv(file_path, sep=';')
        df['source_file'] = file
        all_data.append(df)
    
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"Combined dataset shape: {combined_df.shape}")
    return combined_df

def ultra_conservative_strategy(data, product, window=200, threshold=3.0, min_gap=200):
    """
    Ultra-conservative mean reversion strategy with very strict filtering:
    - Much larger rolling window and higher threshold for fewer signals
    - Much larger minimum gap between signals
    - Only trade on significant price deviations
    """
    product_data = data[data['product'] == product].copy()
    product_data = product_data.sort_values(['day', 'timestamp'])
    
    # Calculate rolling statistics with larger window
    product_data['rolling_mean'] = product_data['mid_price'].rolling(window=window, min_periods=50).mean()
    product_data['rolling_std'] = product_data['mid_price'].rolling(window=window, min_periods=50).std()
    
    # Generate initial signals with higher threshold
    product_data['buy_condition'] = product_data['mid_price'] < (product_data['rolling_mean'] - threshold * product_data['rolling_std'])
    product_data['sell_condition'] = product_data['mid_price'] > (product_data['rolling_mean'] + threshold * product_data['rolling_std'])
    
    # Filter signals to avoid clustering with much larger gap
    product_data['buy_signal'] = False
    product_data['sell_signal'] = False
    
    last_signal_time = -min_gap  # Initialize to allow first signal
    
    for i, row in product_data.iterrows():
        current_time = row['timestamp']
        
        # Only generate new signal if enough time has passed (much larger gap)
        if current_time - last_signal_time >= min_gap:
            if row['buy_condition'] and not row['sell_condition']:
                product_data.loc[i, 'buy_signal'] = True
                last_signal_time = current_time
            elif row['sell_condition'] and not row['buy_condition']:
                product_data.loc[i, 'sell_signal'] = True
                last_signal_time = current_time
    
    return product_data

def calculate_profit(strategy_data):
    """
    Calculate profit/loss from the trading strategy.
    Assumes we start with no position and track completed trades.
    """
    buy_signals = strategy_data[strategy_data['buy_signal']]
    sell_signals = strategy_data[strategy_data['sell_signal']]
    
    total_profit = 0.0
    position = 0  # 0 = no position, 1 = long position
    buy_price = 0.0
    
    # Combine all signals and sort by timestamp
    all_signals = []
    
    for _, signal in buy_signals.iterrows():
        all_signals.append((signal['timestamp'], 'buy', signal['mid_price']))
    
    for _, signal in sell_signals.iterrows():
        all_signals.append((signal['timestamp'], 'sell', signal['mid_price']))
    
    # Sort by timestamp
    all_signals.sort(key=lambda x: x[0])
    
    trades = []
    
    for timestamp, signal_type, price in all_signals:
        if signal_type == 'buy' and position == 0:
            # Enter long position
            position = 1
            buy_price = price
            print(f"BUY at {price:.2f} (timestamp: {timestamp})")
            
        elif signal_type == 'sell' and position == 1:
            # Close long position
            profit = price - buy_price
            total_profit += profit
            trades.append(profit)
            print(f"SELL at {price:.2f} (timestamp: {timestamp}) - Profit: {profit:.2f}")
            position = 0
    
    # Handle any remaining open position
    if position == 1:
        final_price = strategy_data['mid_price'].iloc[-1]
        profit = final_price - buy_price
        total_profit += profit
        trades.append(profit)
        print(f"Final SELL at {final_price:.2f} (end of data) - Profit: {profit:.2f}")
    
    return total_profit, trades

def create_strategy_visualization(data, product, day, start_time=200000, end_time=400000):
    """Create visualization with buy/sell signals for a specific product and day within a time range."""
    
    # Filter data for specific day and product
    day_data = data[(data['day'] == day) & (data['product'] == product)].copy()
    day_data = day_data.sort_values('timestamp')
    
    # Apply strategy
    strategy_data = ultra_conservative_strategy(day_data, product)
    
    # Filter to specific time range
    strategy_data = strategy_data[
        (strategy_data['timestamp'] >= start_time) & 
        (strategy_data['timestamp'] <= end_time)
    ].copy()
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Plot the price line
    ax.plot(strategy_data['timestamp'], strategy_data['mid_price'], 
            color='orange', linewidth=2, label='Price', alpha=0.8)
    
    # Plot buy signals (green arrows) - make them more prominent
    buy_points = strategy_data[strategy_data['buy_signal']]
    if len(buy_points) > 0:
        ax.scatter(buy_points['timestamp'], buy_points['mid_price'], 
                  color='green', marker='^', s=200, label='Buy', zorder=5, edgecolors='darkgreen', linewidth=2)
        # Add arrows for buy signals
        for _, point in buy_points.iterrows():
            ax.annotate('↑', xy=(point['timestamp'], point['mid_price']), 
                       xytext=(point['timestamp'], point['mid_price'] + 8),
                       ha='center', va='bottom', fontsize=16, color='green', fontweight='bold')
    
    # Plot sell signals (red arrows) - make them more prominent
    sell_points = strategy_data[strategy_data['sell_signal']]
    if len(sell_points) > 0:
        ax.scatter(sell_points['timestamp'], sell_points['mid_price'], 
                  color='red', marker='v', s=200, label='Sell', zorder=5, edgecolors='darkred', linewidth=2)
        # Add arrows for sell signals
        for _, point in sell_points.iterrows():
            ax.annotate('↓', xy=(point['timestamp'], point['mid_price']), 
                       xytext=(point['timestamp'], point['mid_price'] - 8),
                       ha='center', va='top', fontsize=16, color='red', fontweight='bold')
    
    # Plot rolling mean
    ax.plot(strategy_data['timestamp'], strategy_data['rolling_mean'], 
            color='blue', linestyle='--', alpha=0.7, label='Rolling Mean')
    
    # Add threshold lines
    upper_threshold = strategy_data['rolling_mean'] + 1.5 * strategy_data['rolling_std']
    lower_threshold = strategy_data['rolling_mean'] - 1.5 * strategy_data['rolling_std']
    ax.plot(strategy_data['timestamp'], upper_threshold, 
            color='red', linestyle=':', alpha=0.5, label='Upper Threshold')
    ax.plot(strategy_data['timestamp'], lower_threshold, 
            color='green', linestyle=':', alpha=0.5, label='Lower Threshold')
    
    # Customize the plot
    ax.set_title(f'{product} Trading Strategy - Day {day} (Time: {start_time}-{end_time})\nBuys (green ↑), Sells (red ↓)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Price', fontsize=12)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Format x-axis to show time more clearly
    ax.tick_params(axis='x', rotation=45)
    
    # Add some statistics
    total_signals = len(buy_points) + len(sell_points)
    profit_potential = len(buy_points) - len(sell_points)  # Simple metric
    
    stats_text = f'Total Signals: {total_signals}\nBuy Signals: {len(buy_points)}\nSell Signals: {len(sell_points)}'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    return fig

def main():
    """Main function to create trading strategy visualizations."""
    print("Loading IMC round1 data...")
    df = load_data()
    
    print("\nCreating trading strategy visualization for STARFRUIT - Day -2...")
    
    # Focus only on STARFRUIT for day -2
    product = 'STARFRUIT'
    day = -2
    
    print(f"Creating strategy visualization for {product} - Day {day}...")
    
    # Create visualization for specific time range
    fig = create_strategy_visualization(df, product, day, start_time=200000, end_time=400000)
    
    # Save the plot
    output_file = f"strategy_{product}_day_{day}.png"
    fig.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Strategy visualization saved as: {output_file}")
    
    # Show the plot
    plt.show()
    
    # Calculate and print strategy statistics and profit
    day_data = df[(df['day'] == day) & (df['product'] == product)].copy()
    strategy_data = ultra_conservative_strategy(day_data, product)
    
    buy_count = strategy_data['buy_signal'].sum()
    sell_count = strategy_data['sell_signal'].sum()
    
    print(f"\n  Strategy Statistics for {product} - Day {day}:")
    print(f"    Buy signals: {buy_count}")
    print(f"    Sell signals: {sell_count}")
    print(f"    Total signals: {buy_count + sell_count}")
    print(f"    Signal frequency: {(buy_count + sell_count) / len(day_data) * 100:.2f}% of data points")
    
    # Calculate profit
    print(f"\n  Trading Execution:")
    total_profit, trades = calculate_profit(strategy_data)
    
    print(f"\n  Profit Summary:")
    print(f"    Total Profit: {total_profit:.2f}")
    print(f"    Number of completed trades: {len(trades)}")
    if len(trades) > 0:
        print(f"    Average profit per trade: {total_profit/len(trades):.2f}")
        print(f"    Best trade: {max(trades):.2f}")
        print(f"    Worst trade: {min(trades):.2f}")
        print(f"    Winning trades: {sum(1 for t in trades if t > 0)}")
        print(f"    Losing trades: {sum(1 for t in trades if t < 0)}")

if __name__ == "__main__":
    main()
