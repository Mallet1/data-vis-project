#!/usr/bin/env python3
"""
Visualization script for mid_price data from IMC round1 data.
Combines all three CSV files and creates a time series plot of mid_price over time.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def load_and_combine_data():
    """Load and combine all three CSV files from round1/data directory."""
    data_dir = Path("imc-data/round1/data")
    
    # List of CSV files to combine
    csv_files = [
        "prices_round_1_day_-2.csv",
        "prices_round_1_day_-1.csv", 
        "prices_round_1_day_0.csv"
    ]
    
    all_data = []
    
    for file in csv_files:
        file_path = data_dir / file
        print(f"Loading {file}...")
        
        # Read CSV with semicolon separator
        df = pd.read_csv(file_path, sep=';')
        
        # Add source file information
        df['source_file'] = file
        
        all_data.append(df)
    
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    
    print(f"Combined dataset shape: {combined_df.shape}")
    print(f"Columns: {list(combined_df.columns)}")
    
    return combined_df

def create_visualization(df):
    """Create separate time series visualizations for each day."""
    
    # Get unique days and products
    days = sorted(df['day'].unique())
    products = df['product'].unique()
    
    figures = []
    
    for day in days:
        print(f"\nCreating visualization for Day {day}...")
        
        # Filter data for this day
        day_data = df[df['day'] == day].copy()
        
        # Create figure with subplots for each product
        fig, axes = plt.subplots(len(products), 1, figsize=(15, 5 * len(products)))
        if len(products) == 1:
            axes = [axes]
        
        for i, product in enumerate(products):
            ax = axes[i]
            
            # Filter data for this product on this day
            product_data = day_data[day_data['product'] == product].copy()
            
            # Sort by timestamp
            product_data = product_data.sort_values('timestamp')
            
            # Plot mid_price over time
            ax.plot(product_data['timestamp'], product_data['mid_price'], 
                    linewidth=1, alpha=0.7, label=f'{product} Mid Price')
            
            ax.set_title(f'{product} Mid Price - Day {day}', fontsize=14, fontweight='bold')
            ax.set_xlabel('Timestamp', fontsize=12)
            ax.set_ylabel('Mid Price', fontsize=12)
            
            # For AMETHYSTS, set y-axis to show actual price range
            if product == 'AMETHYSTS':
                min_price = product_data['mid_price'].min()
                max_price = product_data['mid_price'].max()
                # Set y-axis limits to show the actual price range with some padding
                price_range = max_price - min_price
                ax.set_ylim(min_price - 0.1 * price_range, max_price + 0.1 * price_range)
                # Format y-axis to show actual price values
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}'))
            
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # Add some statistics
            mean_price = product_data['mid_price'].mean()
            std_price = product_data['mid_price'].std()
            ax.axhline(y=mean_price, color='red', linestyle='--', alpha=0.7, 
                      label=f'Mean: {mean_price:.2f}')
            ax.axhline(y=mean_price + std_price, color='orange', linestyle=':', alpha=0.7)
            ax.axhline(y=mean_price - std_price, color='orange', linestyle=':', alpha=0.7)
            
            print(f"  {product} Statistics for Day {day}:")
            print(f"    Mean mid_price: {mean_price:.2f}")
            print(f"    Std mid_price: {std_price:.2f}")
            print(f"    Min mid_price: {product_data['mid_price'].min():.2f}")
            print(f"    Max mid_price: {product_data['mid_price'].max():.2f}")
            print(f"    Data points: {len(product_data)}")
        
        plt.tight_layout()
        figures.append(fig)
    
    return figures

def main():
    """Main function to load data and create visualization."""
    print("Loading and combining IMC round1 data...")
    
    # Load and combine data
    df = load_and_combine_data()
    
    print("\nDataset overview:")
    print(f"Total records: {len(df)}")
    print(f"Products: {df['product'].unique()}")
    print(f"Days: {sorted(df['day'].unique())}")
    print(f"Timestamp range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    print("\nCreating visualizations...")
    
    # Create visualizations
    figures = create_visualization(df)
    
    # Save each plot separately
    for i, fig in enumerate(figures):
        day = sorted(df['day'].unique())[i]
        output_file = f"mid_price_day_{day}.png"
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Visualization for Day {day} saved as: {output_file}")
    
    # Show all plots
    plt.show()

if __name__ == "__main__":
    main()
