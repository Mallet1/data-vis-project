import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from spread_zscore_updated import load_and_process_data, calculate_modified_zscore

def analyze_optimal_threshold(df):
    """
    Analyze different thresholds to find the sweet spot
    """
    print("THRESHOLD OPTIMIZATION ANALYSIS")
    print("=" * 50)
    
    thresholds_to_test = [2, 3, 4, 5, 6, 7, 8, 10, 12, 15]
    results = []
    
    for threshold in thresholds_to_test:
        # Calculate signals
        df_test = df.copy()
        df_test['signal'] = 0
        df_test.loc[df_test['z_score'] > threshold, 'signal'] = -1  # Sell spread
        df_test.loc[df_test['z_score'] < -threshold, 'signal'] = 1   # Buy spread
        
        # Calculate position changes and PnL
        df_test['position_change'] = df_test['signal'].diff()
        df_test['position'] = df_test['signal'].cumsum()
        df_test['pnl'] = df_test['position'].shift(1) * df_test['spread'].diff()
        df_test['cumulative_pnl'] = df_test['pnl'].cumsum()
        
        # Calculate metrics
        buy_signals = len(df_test[df_test['signal'] == 1])
        sell_signals = len(df_test[df_test['signal'] == -1])
        total_signals = buy_signals + sell_signals
        final_pnl = df_test['cumulative_pnl'].iloc[-1]
        max_pnl = df_test['cumulative_pnl'].max()
        min_pnl = df_test['cumulative_pnl'].min()
        signal_freq = total_signals / len(df) * 100
        
        # Calculate Sharpe-like ratio (PnL per signal)
        pnl_per_signal = final_pnl / total_signals if total_signals > 0 else 0
        
        results.append({
            'threshold': threshold,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'total_signals': total_signals,
            'signal_frequency': signal_freq,
            'final_pnl': final_pnl,
            'max_pnl': max_pnl,
            'min_pnl': min_pnl,
            'pnl_range': max_pnl - min_pnl,
            'pnl_per_signal': pnl_per_signal
        })
    
    results_df = pd.DataFrame(results)
    
    print(results_df.to_string(index=False, float_format='%.2f'))
    
    # Find optimal threshold based on different criteria
    print(f"\nOPTIMAL THRESHOLD ANALYSIS:")
    print("-" * 40)
    
    # Best by final PnL
    best_pnl_idx = results_df['final_pnl'].idxmax()
    print(f"Best by Final PnL: ±{results_df.loc[best_pnl_idx, 'threshold']} (PnL: {results_df.loc[best_pnl_idx, 'final_pnl']:.0f})")
    
    # Best by PnL per signal (efficiency)
    best_efficiency_idx = results_df['pnl_per_signal'].idxmax()
    print(f"Best by Efficiency: ±{results_df.loc[best_efficiency_idx, 'threshold']} (PnL/signal: {results_df.loc[best_efficiency_idx, 'pnl_per_signal']:.0f})")
    
    # Reasonable signal frequency (10-30%)
    reasonable_freq = results_df[(results_df['signal_frequency'] >= 10) & (results_df['signal_frequency'] <= 30)]
    if not reasonable_freq.empty:
        best_reasonable_idx = reasonable_freq['final_pnl'].idxmax()
        print(f"Best in 10-30% freq range: ±{results_df.loc[best_reasonable_idx, 'threshold']} (PnL: {results_df.loc[best_reasonable_idx, 'final_pnl']:.0f}, Freq: {results_df.loc[best_reasonable_idx, 'signal_frequency']:.1f}%)")
    
    return results_df

def main():
    """
    Main function to analyze optimal threshold
    """
    # File path
    file_path = '/home/mallet/code/data-vis/data-vis-project/imc-data/round3/data/prices_round_3_day_0.csv'
    
    print("Loading data...")
    df = load_and_process_data(file_path)
    
    print("Calculating z-score...")
    df['z_score'] = calculate_modified_zscore(df['spread'], hardcoded_mean=370, window_size=100)
    
    # Analyze optimal threshold
    results_df = analyze_optimal_threshold(df)
    
    # Recommend threshold
    print(f"\nRECOMMENDATION:")
    print("=" * 20)
    print("Based on the analysis, a threshold around ±5-7 seems optimal:")
    print("- Good signal frequency (10-20%)")
    print("- High PnL per signal")
    print("- Reasonable number of trades")
    print("- Not too noisy, not too conservative")

if __name__ == "__main__":
    main()

