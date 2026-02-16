#!/usr/bin/env python3
"""
Homelessness Point-in-Time (PIT) Count Analysis for Butte County

Analyzes HUD PIT count data to examine homelessness trends in the
Chico, Paradise/Butte County CoC (CA-519) before and after the Camp Fire.

Data source: HUD Annual Homeless Assessment Report (AHAR) PIT Counts by CoC
https://www.hudexchange.info/resource/3031/pit-and-hic-data-since-2007/

Usage:
    python 09_homelessness_analysis.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Paths
from config import GRAPHS_DIR, TABLES_DIR, ANALYSIS_DIR
DATA_FILE = ANALYSIS_DIR / "data" / "2007-2024-PIT-Counts-by-CoC.xlsb"

# Constants
BUTTE_COC = "CA-519"  # Chico, Paradise/Butte County CoC
CAMP_FIRE_YEAR = 2018  # Fire occurred November 2018; 2019 is first post-fire PIT count

# Comparison CoCs (Northern California)
COMPARISON_COCS = {
    'CA-519': 'Butte (Chico/Paradise)',
    'CA-516': 'Redding/Shasta',
    'CA-527': 'Tehama County',
    'CA-524': 'Yuba/Sutter Counties',
    'CA-525': 'El Dorado County'
}


def load_pit_data(years=None):
    """Load PIT count data for Butte County across all available years."""
    if years is None:
        years = list(range(2007, 2025))

    data = []
    for year in years:
        try:
            df = pd.read_excel(DATA_FILE, sheet_name=str(year), engine='pyxlsb')
            mask = df['CoC Number'] == BUTTE_COC
            if mask.any():
                row = df.loc[mask].iloc[0]
                data.append({
                    'year': year,
                    'coc_number': BUTTE_COC,
                    'coc_name': row['CoC Name'],
                    'total_homeless': row['Overall Homeless'],
                    'sheltered': row.get('Sheltered Total Homeless', None),
                    'unsheltered': row.get('Unsheltered Homeless', None),
                    'emergency_shelter': row.get('Sheltered ES Homeless', None),
                    'transitional_housing': row.get('Sheltered TH Homeless', None)
                })
        except Exception as e:
            print(f"Warning: Could not load year {year}: {e}")

    return pd.DataFrame(data)


def load_comparison_data(years=None):
    """Load PIT count data for comparison CoCs."""
    if years is None:
        years = [2015, 2016, 2017, 2018, 2019, 2020, 2022, 2023, 2024]

    data = []
    for year in years:
        try:
            df = pd.read_excel(DATA_FILE, sheet_name=str(year), engine='pyxlsb')
            for coc_num, coc_name in COMPARISON_COCS.items():
                mask = df['CoC Number'] == coc_num
                if mask.any():
                    val = df.loc[mask, 'Overall Homeless'].values[0]
                    data.append({'Year': year, 'CoC': coc_name, 'Homeless': val})
        except Exception as e:
            print(f"Warning: Could not load year {year}: {e}")

    return pd.DataFrame(data)


def load_california_totals(years=None):
    """Load total California homelessness counts."""
    if years is None:
        years = list(range(2007, 2025))

    data = []
    for year in years:
        try:
            df = pd.read_excel(DATA_FILE, sheet_name=str(year), engine='pyxlsb')
            ca_mask = df['CoC Number'].astype(str).str.startswith('CA-', na=False)
            if ca_mask.any():
                data.append({
                    'Year': year,
                    'CA_Total': df.loc[ca_mask, 'Overall Homeless'].sum()
                })
        except Exception as e:
            print(f"Warning: Could not load year {year}: {e}")

    return pd.DataFrame(data)


def plot_homelessness_trends(butte_df, ca_df, output_path):
    """Create main visualization of homelessness trends."""
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))

    years = butte_df['year'].tolist()

    # Plot 1: Butte County total homelessness bar chart
    ax1 = axes[0]
    colors = ['#1f77b4' if y <= CAMP_FIRE_YEAR else '#d62728' for y in butte_df['year']]
    ax1.bar(butte_df['year'], butte_df['total_homeless'], color=colors,
            edgecolor='black', linewidth=0.5)
    ax1.axvline(x=CAMP_FIRE_YEAR + 0.5, color='orange', linestyle='--',
                linewidth=2, label='Camp Fire (Nov 2018)')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Total Homeless Count')
    ax1.set_title('Point-in-Time Homelessness Count: Chico, Paradise/Butte County (CA-519)',
                  fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.set_xticks(years)
    ax1.set_xticklabels(years, rotation=45)

    # Annotate the 2021 anomaly (COVID - no unsheltered count)
    if 2021 in butte_df['year'].values:
        val_2021 = butte_df[butte_df['year'] == 2021]['total_homeless'].values[0]
        ax1.annotate('2021: No unsheltered\ncount (COVID)',
                     xy=(2021, val_2021), xytext=(2019, 200),
                     arrowprops=dict(arrowstyle='->', color='gray'),
                     fontsize=8, color='gray')

    # Add values on bars for key years
    for year in [2018, 2019, 2024]:
        if year in butte_df['year'].values:
            val = butte_df[butte_df['year'] == year]['total_homeless'].values[0]
            ax1.text(year, val + 30, f'{int(val)}', ha='center', fontsize=9, fontweight='bold')

    # Plot 2: Indexed comparison (2015 = 100)
    ax2 = axes[1]
    base_year = 2015

    butte_base = butte_df[butte_df['year'] == base_year]['total_homeless'].values[0]
    ca_base = ca_df[ca_df['Year'] == base_year]['CA_Total'].values[0]

    butte_df = butte_df.copy()
    butte_df['Indexed'] = 100 * butte_df['total_homeless'] / butte_base
    ca_df = ca_df.copy()
    ca_df['Indexed'] = 100 * ca_df['CA_Total'] / ca_base

    # Exclude 2021 from trend lines (unreliable count)
    butte_plot = butte_df[butte_df['year'] != 2021]
    ca_plot = ca_df[ca_df['Year'] != 2021]

    ax2.plot(butte_plot['year'], butte_plot['Indexed'], 'o-', color='#d62728',
             linewidth=2, markersize=6, label='Butte County (CA-519)')
    ax2.plot(ca_plot['Year'], ca_plot['Indexed'], 's--', color='#1f77b4',
             linewidth=2, markersize=5, label='California (all CoCs)')
    ax2.axvline(x=CAMP_FIRE_YEAR + 0.5, color='orange', linestyle='--',
                linewidth=2, label='Camp Fire')
    ax2.axhline(y=100, color='gray', linestyle=':', alpha=0.5)
    ax2.set_xlabel('Year')
    ax2.set_ylabel(f'Homeless Count (Index: {base_year}=100)')
    ax2.set_title('Butte County vs California Homelessness Trends (2021 excluded)',
                  fontsize=12, fontweight='bold')
    ax2.legend(loc='upper left')
    ax2.set_xticks(years)
    ax2.set_xticklabels(years, rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def print_summary_statistics(butte_df):
    """Print summary statistics on Camp Fire impact."""
    print("\n" + "=" * 60)
    print("SUMMARY: Camp Fire Impact on Homelessness in Butte County")
    print("=" * 60)

    # Pre vs post averages (excluding 2021)
    pre_fire = butte_df[(butte_df['year'] >= 2015) & (butte_df['year'] <= 2018)]
    post_fire = butte_df[(butte_df['year'] >= 2019) & (butte_df['year'] != 2021)]

    print(f"\nPre-fire average (2015-2018): {pre_fire['total_homeless'].mean():.0f}")
    print(f"Post-fire average (2019-2024, excl 2021): {post_fire['total_homeless'].mean():.0f}")

    # Year-over-year changes
    y2018 = butte_df[butte_df['year'] == 2018]['total_homeless'].values[0]
    y2019 = butte_df[butte_df['year'] == 2019]['total_homeless'].values[0]
    y2024 = butte_df[butte_df['year'] == 2024]['total_homeless'].values[0]

    print(f"\n2018 (pre-fire):  {y2018:.0f}")
    print(f"2019 (post-fire): {y2019:.0f}  (change: {y2019-y2018:+.0f}, {100*(y2019-y2018)/y2018:+.1f}%)")
    print(f"2024 (latest):    {y2024:.0f}  (change: {y2024-y2018:+.0f}, {100*(y2024-y2018)/y2018:+.1f}%)")

    # Shelter capacity changes
    es_2018 = butte_df[butte_df['year'] == 2018]['emergency_shelter'].values[0]
    es_2024 = butte_df[butte_df['year'] == 2024]['emergency_shelter'].values[0]

    print(f"\nEmergency Shelter Capacity:")
    print(f"  2018: {es_2018:.0f}")
    print(f"  2024: {es_2024:.0f}  (change: {es_2024-es_2018:+.0f}, {100*(es_2024-es_2018)/es_2018:+.1f}%)")


def print_comparison_table(comparison_df):
    """Print comparison with neighboring CoCs."""
    print("\n" + "=" * 60)
    print("Comparison: Butte County vs Neighboring Northern CA CoCs")
    print("=" * 60)

    pivot = comparison_df.pivot(index='Year', columns='CoC', values='Homeless')
    col_order = ['Butte (Chico/Paradise)', 'Redding/Shasta', 'Yuba/Sutter Counties',
                 'El Dorado County', 'Tehama County']
    pivot = pivot[[c for c in col_order if c in pivot.columns]]

    print(f"\n{pivot.to_string()}")

    # Percent changes
    print("\nPercent change 2018 -> 2019:")
    print("-" * 40)
    for coc in pivot.columns:
        try:
            y18 = pivot.loc[2018, coc]
            y19 = pivot.loc[2019, coc]
            pct = 100 * (y19 - y18) / y18
            print(f"  {coc}: {pct:+.1f}%")
        except:
            pass

    print("\nPercent change 2018 -> 2024:")
    print("-" * 40)
    for coc in pivot.columns:
        try:
            y18 = pivot.loc[2018, coc]
            y24 = pivot.loc[2024, coc]
            pct = 100 * (y24 - y18) / y18
            print(f"  {coc}: {pct:+.1f}%")
        except:
            pass


def main():
    """Run the full homelessness analysis."""
    print("=" * 60)
    print("Homelessness PIT Count Analysis - Butte County (CA-519)")
    print("=" * 60)

    # Check for data file
    if not DATA_FILE.exists():
        print(f"\nError: Data file not found: {DATA_FILE}")
        print("Download from: https://www.hudexchange.info/resource/3031/pit-and-hic-data-since-2007/")
        return

    # Load data
    print("\nLoading PIT count data...")
    butte_df = load_pit_data()
    ca_df = load_california_totals()
    comparison_df = load_comparison_data()

    print(f"  Loaded {len(butte_df)} years of Butte County data")

    # Save extracted data
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    output_csv = TABLES_DIR / "homelessness_pit_butte_county.csv"
    butte_df.to_csv(output_csv, index=False)
    print(f"  Saved: {output_csv}")

    # Create visualization
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    output_png = GRAPHS_DIR / "homelessness_pit_counts.png"
    plot_homelessness_trends(butte_df.copy(), ca_df.copy(), output_png)

    # Print summary statistics
    print_summary_statistics(butte_df)
    print_comparison_table(comparison_df)

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
