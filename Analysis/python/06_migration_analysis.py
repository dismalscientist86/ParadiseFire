"""
06_migration_analysis.py
Analyzes IRS SOI county-to-county migration data to identify where
Butte County (Paradise) residents migrated after the Camp Fire.

Data source: IRS Statistics of Income County-to-County Migration Data
https://www.irs.gov/statistics/soi-tax-stats-migration-data
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import requests

from config import DATA_DIR, GRAPHS_MIGRATION

# IRS SOI County Outflow URLs
SOI_URLS = {
    "2012-2013": "https://www.irs.gov/pub/irs-soi/countyoutflow1213.csv",
    "2013-2014": "https://www.irs.gov/pub/irs-soi/countyoutflow1314.csv",
    "2014-2015": "https://www.irs.gov/pub/irs-soi/countyoutflow1415.csv",
    "2015-2016": "https://www.irs.gov/pub/irs-soi/countyoutflow1516.csv",
    "2016-2017": "https://www.irs.gov/pub/irs-soi/countyoutflow1617.csv",
    "2017-2018": "https://www.irs.gov/pub/irs-soi/countyoutflow1718.csv",
    "2018-2019": "https://www.irs.gov/pub/irs-soi/countyoutflow1819.csv",
    "2019-2020": "https://www.irs.gov/pub/irs-soi/countyoutflow1920.csv",
    "2020-2021": "https://www.irs.gov/pub/irs-soi/countyoutflow2021.csv",
    "2021-2022": "https://www.irs.gov/pub/irs-soi/countyoutflow2122.csv",
}

# Butte County FIPS
BUTTE_STATE_FIPS = "06"
BUTTE_COUNTY_FIPS = "007"

# Fire occurred November 2018, so 2018-2019 tax year captures immediate displacement
FIRE_YEAR = "2018-2019"
PRE_FIRE_YEARS = ["2015-2016", "2016-2017", "2017-2018"]
POST_FIRE_YEARS = ["2018-2019", "2019-2020", "2020-2021", "2021-2022"]

# Census regions by state FIPS code
# https://www2.census.gov/geo/pdfs/maps-data/maps/reference/us_regdiv.pdf
CENSUS_REGIONS = {
    # Northeast
    "09": "Northeast", "23": "Northeast", "25": "Northeast", "33": "Northeast",
    "44": "Northeast", "50": "Northeast", "34": "Northeast", "36": "Northeast",
    "42": "Northeast",
    # Midwest
    "17": "Midwest", "18": "Midwest", "26": "Midwest", "39": "Midwest",
    "55": "Midwest", "19": "Midwest", "20": "Midwest", "27": "Midwest",
    "29": "Midwest", "31": "Midwest", "38": "Midwest", "46": "Midwest",
    # South
    "10": "South", "11": "South", "12": "South", "13": "South", "24": "South",
    "37": "South", "45": "South", "51": "South", "54": "South", "01": "South",
    "21": "South", "28": "South", "47": "South", "05": "South", "22": "South",
    "40": "South", "48": "South",
    # West
    "04": "West", "08": "West", "16": "West", "30": "West", "32": "West",
    "35": "West", "49": "West", "56": "West", "02": "West", "06": "West",
    "15": "West", "41": "West", "53": "West",
}


def download_soi_data(years: list = None, force: bool = False) -> dict:
    """
    Download IRS SOI county outflow data for specified years.

    Returns dict of {year: DataFrame}
    """
    if years is None:
        years = list(SOI_URLS.keys())

    migration_dir = DATA_DIR / "migration" / "soi"
    migration_dir.mkdir(parents=True, exist_ok=True)

    data = {}

    for year in years:
        if year not in SOI_URLS:
            print(f"  No URL for {year}, skipping")
            continue

        filepath = migration_dir / f"countyoutflow_{year.replace('-', '_')}.csv"

        if filepath.exists() and not force:
            print(f"  {year}: Loading from cache")
            df = pd.read_csv(filepath, dtype=str, encoding="latin-1")
        else:
            print(f"  {year}: Downloading...")
            try:
                response = requests.get(SOI_URLS[year], timeout=60)
                response.raise_for_status()

                # Save raw file
                filepath.write_bytes(response.content)
                df = pd.read_csv(filepath, dtype=str, encoding="latin-1")
                print(f"    Downloaded {len(df):,} rows")
            except Exception as e:
                print(f"    Error downloading {year}: {e}")
                continue

        # Standardize column names (they vary slightly by year)
        df.columns = df.columns.str.lower().str.strip()

        # Add year column
        df["year"] = year
        data[year] = df

    return data


def process_butte_outflows(data: dict) -> pd.DataFrame:
    """
    Extract Butte County outflows to specific destination counties.

    Filters out summary rows (totals, same-state totals, regional aggregates, etc.)
    """
    all_outflows = []

    for year, df in data.items():
        # Filter to Butte County as origin
        # Column names: y1_statefips, y1_countyfips (origin)
        #               y2_statefips, y2_countyfips (destination)
        butte_out = df[
            (df["y1_statefips"].str.zfill(2) == BUTTE_STATE_FIPS) &
            (df["y1_countyfips"].str.zfill(3) == BUTTE_COUNTY_FIPS)
        ].copy()

        # Filter to actual county destinations (exclude summary rows)
        # Summary rows have y2_countyfips in [000, 001, 003] or y2_statefips in [96, 97, 98]
        butte_out = butte_out[
            ~butte_out["y2_statefips"].isin(["96", "97", "98"]) &
            ~butte_out["y2_countyfips"].isin(["000", "001", "003"])
        ]

        # Also exclude "non-migrants" (same county)
        butte_out = butte_out[
            ~((butte_out["y2_statefips"].str.zfill(2) == BUTTE_STATE_FIPS) &
              (butte_out["y2_countyfips"].str.zfill(3) == BUTTE_COUNTY_FIPS))
        ]

        # Exclude "Other flows" summary rows (regional aggregates)
        if "y2_countyname" in butte_out.columns:
            butte_out = butte_out[
                ~butte_out["y2_countyname"].str.lower().str.contains("other flows", na=False) &
                ~butte_out["y2_countyname"].str.lower().str.contains("total migration", na=False) &
                ~butte_out["y2_countyname"].str.lower().str.contains("non-migrants", na=False)
            ]

        all_outflows.append(butte_out)

    combined = pd.concat(all_outflows, ignore_index=True)

    # Convert numeric columns
    for col in ["n1", "n2", "agi"]:
        if col in combined.columns:
            combined[col] = pd.to_numeric(combined[col], errors="coerce")

    # Create destination FIPS code
    combined["dest_fips"] = (
        combined["y2_statefips"].str.zfill(2) +
        combined["y2_countyfips"].str.zfill(3)
    )

    # Create readable destination name
    if "y2_countyname" in combined.columns:
        combined["dest_name"] = combined["y2_countyname"]
    else:
        combined["dest_name"] = combined["dest_fips"]

    return combined


def analyze_migration_patterns(outflows: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze migration patterns by destination, comparing pre vs post fire.
    """
    # Aggregate by destination and year
    agg = outflows.groupby(["year", "dest_fips", "dest_name"]).agg({
        "n1": "sum",  # Number of returns (households)
        "n2": "sum",  # Number of exemptions (people)
        "agi": "sum"  # Adjusted gross income (thousands)
    }).reset_index()

    agg.columns = ["year", "dest_fips", "dest_name", "returns", "exemptions", "agi"]

    # Add period indicator
    agg["period"] = agg["year"].apply(
        lambda y: "pre_fire" if y in PRE_FIRE_YEARS else "post_fire"
    )

    return agg


def get_top_destinations(outflows: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    Get top destination counties by total outflow.
    """
    # Sum across all years
    totals = outflows.groupby(["dest_fips", "dest_name"]).agg({
        "n1": "sum",
        "n2": "sum",
        "agi": "sum"
    }).reset_index()

    totals.columns = ["dest_fips", "dest_name", "total_returns", "total_exemptions", "total_agi"]
    totals = totals.sort_values("total_returns", ascending=False)

    return totals.head(top_n)


def compare_pre_post_fire(outflows: pd.DataFrame, agg: pd.DataFrame) -> pd.DataFrame:
    """
    Compare migration to each destination before vs after the fire.
    """
    # Calculate average annual outflow by period
    period_avg = agg.groupby(["dest_fips", "dest_name", "period"]).agg({
        "returns": "mean",
        "exemptions": "mean",
        "agi": "mean"
    }).reset_index()

    # Pivot to wide format
    pre = period_avg[period_avg["period"] == "pre_fire"].copy()
    post = period_avg[period_avg["period"] == "post_fire"].copy()

    pre = pre.rename(columns={
        "returns": "pre_returns",
        "exemptions": "pre_exemptions",
        "agi": "pre_agi"
    })
    post = post.rename(columns={
        "returns": "post_returns",
        "exemptions": "post_exemptions",
        "agi": "post_agi"
    })

    # Merge
    comparison = pre[["dest_fips", "dest_name", "pre_returns", "pre_exemptions", "pre_agi"]].merge(
        post[["dest_fips", "dest_name", "post_returns", "post_exemptions", "post_agi"]],
        on=["dest_fips", "dest_name"],
        how="outer"
    ).fillna(0)

    # Calculate changes
    comparison["returns_change"] = comparison["post_returns"] - comparison["pre_returns"]
    comparison["returns_pct_change"] = (
        100 * comparison["returns_change"] / comparison["pre_returns"].replace(0, np.nan)
    )
    comparison["exemptions_change"] = comparison["post_exemptions"] - comparison["pre_exemptions"]

    return comparison.sort_values("returns_change", ascending=False)


def plot_top_destinations_by_year(agg: pd.DataFrame, top_n: int = 10, save: bool = True):
    """
    Plot migration to top destinations over time.
    """
    # Get top destinations overall
    top_dests = agg.groupby("dest_name")["returns"].sum().nlargest(top_n).index.tolist()

    # Filter to top destinations
    plot_data = agg[agg["dest_name"].isin(top_dests)].copy()

    # Create year order
    year_order = sorted(plot_data["year"].unique())

    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot each destination
    for dest in top_dests:
        dest_data = plot_data[plot_data["dest_name"] == dest].set_index("year")
        dest_data = dest_data.reindex(year_order)
        ax.plot(year_order, dest_data["returns"], "o-", label=dest, linewidth=2, markersize=6)

    # Add fire line
    ax.axvline(x="2018-2019", color="red", linestyle="--", linewidth=2, alpha=0.7, label="Camp Fire")

    ax.set_xlabel("Tax Year", fontsize=12)
    ax.set_ylabel("Number of Tax Returns (Households)", fontsize=12)
    ax.set_title("Migration from Butte County to Top Destination Counties", fontsize=14)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    if save:
        filepath = GRAPHS_MIGRATION / "migration_top_destinations_by_year.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"Saved: {filepath}")

    return fig


def plot_pre_post_comparison(comparison: pd.DataFrame, top_n: int = 15, save: bool = True):
    """
    Bar chart comparing pre-fire vs post-fire migration by destination.
    """
    # Get top destinations by post-fire outflow
    top_dests = comparison.nlargest(top_n, "post_returns")

    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    # Left: Absolute numbers
    ax = axes[0]
    x = np.arange(len(top_dests))
    width = 0.35

    ax.barh(x - width/2, top_dests["pre_returns"], width, label="Pre-Fire (avg)", color="steelblue", alpha=0.7)
    ax.barh(x + width/2, top_dests["post_returns"], width, label="Post-Fire (avg)", color="firebrick", alpha=0.7)

    ax.set_yticks(x)
    ax.set_yticklabels(top_dests["dest_name"])
    ax.set_xlabel("Average Annual Tax Returns (Households)")
    ax.set_title("Migration from Butte County: Pre vs Post Fire")
    ax.legend()
    ax.invert_yaxis()

    # Right: Change
    ax = axes[1]
    colors = ["firebrick" if c > 0 else "steelblue" for c in top_dests["returns_change"]]
    ax.barh(x, top_dests["returns_change"], color=colors, alpha=0.7)
    ax.set_yticks(x)
    ax.set_yticklabels(top_dests["dest_name"])
    ax.set_xlabel("Change in Average Annual Returns")
    ax.set_title("Change in Migration (Post - Pre Fire)")
    ax.axvline(x=0, color="black", linewidth=0.5)
    ax.invert_yaxis()

    plt.tight_layout()

    if save:
        filepath = GRAPHS_MIGRATION / "migration_pre_post_comparison.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"Saved: {filepath}")

    return fig


def plot_fire_year_spike(agg: pd.DataFrame, top_n: int = 10, save: bool = True):
    """
    Focus on the 2018-2019 fire year migration spike.
    """
    # Get fire year data
    fire_year = agg[agg["year"] == FIRE_YEAR].copy()
    fire_year = fire_year.nlargest(top_n, "returns")

    # Get comparison year (pre-fire)
    pre_year = agg[agg["year"] == "2017-2018"].copy()

    # Merge
    compare = fire_year[["dest_name", "returns"]].merge(
        pre_year[["dest_name", "returns"]],
        on="dest_name",
        how="left",
        suffixes=("_fire", "_pre")
    ).fillna(0)

    compare["increase"] = compare["returns_fire"] - compare["returns_pre"]
    compare["pct_increase"] = 100 * compare["increase"] / compare["returns_pre"].replace(0, np.nan)
    compare = compare.sort_values("returns_fire", ascending=True)

    fig, ax = plt.subplots(figsize=(12, 8))

    y = np.arange(len(compare))

    # Stacked bar: pre-fire base + increase
    ax.barh(y, compare["returns_pre"], label="2017-2018 (Pre-Fire)", color="steelblue", alpha=0.7)
    ax.barh(y, compare["increase"], left=compare["returns_pre"], label="Increase in 2018-2019", color="firebrick", alpha=0.7)

    ax.set_yticks(y)
    ax.set_yticklabels(compare["dest_name"])
    ax.set_xlabel("Number of Tax Returns (Households)")
    ax.set_title(f"Migration Spike in Fire Year (2018-2019) - Top {top_n} Destinations")
    ax.legend(loc="lower right")

    # Add percentage labels
    for i, (_, row) in enumerate(compare.iterrows()):
        if row["pct_increase"] > 0 and not np.isnan(row["pct_increase"]):
            ax.annotate(f"+{row['pct_increase']:.0f}%",
                       xy=(row["returns_fire"] + 5, i),
                       va="center", fontsize=9, color="firebrick")

    plt.tight_layout()

    if save:
        filepath = GRAPHS_MIGRATION / "migration_fire_year_spike.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"Saved: {filepath}")

    return fig


def aggregate_by_region(outflows: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate migration by California vs Census regions.
    """
    df = outflows.copy()

    # Get destination state FIPS (first 2 digits of dest_fips)
    df["dest_state"] = df["dest_fips"].str[:2]

    # Classify destinations
    def get_region(state_fips):
        if state_fips == "06":
            return "California"
        return CENSUS_REGIONS.get(state_fips, "Other")

    df["region"] = df["dest_state"].apply(get_region)

    # Aggregate by year and region
    region_agg = df.groupby(["year", "region"]).agg({
        "n1": "sum",
        "n2": "sum",
        "agi": "sum"
    }).reset_index()

    region_agg.columns = ["year", "region", "returns", "exemptions", "agi"]

    return region_agg


def plot_migration_by_region(outflows: pd.DataFrame, save: bool = True):
    """
    Plot migration trends: California vs out-of-state by Census region.
    """
    region_agg = aggregate_by_region(outflows)

    # Ensure consistent year ordering
    year_order = sorted(region_agg["year"].unique())

    # Define colors and styles for each region
    region_styles = {
        "California": {"color": "#1f77b4", "marker": "o", "linewidth": 3},
        "West": {"color": "#ff7f0e", "marker": "s", "linewidth": 2},
        "South": {"color": "#2ca02c", "marker": "^", "linewidth": 2},
        "Midwest": {"color": "#d62728", "marker": "D", "linewidth": 2},
        "Northeast": {"color": "#9467bd", "marker": "v", "linewidth": 2},
    }

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Left plot: Absolute numbers
    ax = axes[0]
    for region in ["California", "West", "South", "Midwest", "Northeast"]:
        region_data = region_agg[region_agg["region"] == region].set_index("year")
        region_data = region_data.reindex(year_order)
        style = region_styles.get(region, {"color": "gray", "marker": "x", "linewidth": 1})
        ax.plot(year_order, region_data["returns"],
                marker=style["marker"], color=style["color"],
                linewidth=style["linewidth"], markersize=7, label=region)

    ax.axvline(x="2018-2019", color="red", linestyle="--", linewidth=2, alpha=0.7, label="Camp Fire")
    ax.set_xlabel("Tax Year", fontsize=12)
    ax.set_ylabel("Number of Tax Returns (Households)", fontsize=12)
    ax.set_title("Migration from Butte County by Destination Region", fontsize=14)
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    plt.sca(ax)
    plt.xticks(rotation=45, ha="right")

    # Right plot: Share of out-migration
    ax = axes[1]

    # Calculate shares
    totals_by_year = region_agg.groupby("year")["returns"].sum()
    region_shares = region_agg.copy()
    region_shares["share"] = region_shares.apply(
        lambda row: 100 * row["returns"] / totals_by_year[row["year"]], axis=1
    )

    for region in ["California", "West", "South", "Midwest", "Northeast"]:
        region_data = region_shares[region_shares["region"] == region].set_index("year")
        region_data = region_data.reindex(year_order)
        style = region_styles.get(region, {"color": "gray", "marker": "x", "linewidth": 1})
        ax.plot(year_order, region_data["share"],
                marker=style["marker"], color=style["color"],
                linewidth=style["linewidth"], markersize=7, label=region)

    ax.axvline(x="2018-2019", color="red", linestyle="--", linewidth=2, alpha=0.7, label="Camp Fire")
    ax.set_xlabel("Tax Year", fontsize=12)
    ax.set_ylabel("Share of Out-Migration (%)", fontsize=12)
    ax.set_title("Share of Butte County Out-Migration by Destination Region", fontsize=14)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    plt.sca(ax)
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()

    if save:
        filepath = GRAPHS_MIGRATION / "migration_by_region.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"Saved: {filepath}")

    # Print summary table
    print("\nMigration by Region (Returns):")
    pivot = region_agg.pivot(index="year", columns="region", values="returns").fillna(0)
    # Only include columns that exist
    cols_order = [c for c in ["California", "West", "South", "Midwest", "Northeast"] if c in pivot.columns]
    pivot = pivot[cols_order]
    pivot["Total"] = pivot.sum(axis=1)
    print(pivot.to_string())

    return fig


def run_migration_analysis():
    """
    Run full migration analysis.
    """
    print("=" * 70)
    print("IRS SOI Migration Analysis - Butte County Outflows")
    print("=" * 70)

    # Download data
    print("\nDownloading IRS SOI data...")
    data = download_soi_data()

    # Process Butte County outflows
    print("\nProcessing Butte County outflows...")
    outflows = process_butte_outflows(data)
    print(f"Total outflow records: {len(outflows):,}")

    # Aggregate by year and destination
    print("\nAggregating migration patterns...")
    agg = analyze_migration_patterns(outflows)

    # Get top destinations
    print("\nTop 15 destination counties (all years):")
    top_dests = get_top_destinations(outflows, top_n=15)
    print(top_dests.to_string(index=False))

    # Compare pre vs post fire
    print("\n" + "-" * 70)
    print("Pre-Fire vs Post-Fire Comparison")
    print("-" * 70)
    comparison = compare_pre_post_fire(outflows, agg)

    print("\nLargest increases in migration (post-fire vs pre-fire):")
    top_increases = comparison.nlargest(10, "returns_change")[
        ["dest_name", "pre_returns", "post_returns", "returns_change", "returns_pct_change"]
    ]
    print(top_increases.to_string(index=False))

    # Total migration summary
    print("\n" + "-" * 70)
    print("Total Migration by Year")
    print("-" * 70)
    yearly_totals = agg.groupby("year").agg({
        "returns": "sum",
        "exemptions": "sum",
        "agi": "sum"
    }).reset_index()
    yearly_totals["agi_millions"] = yearly_totals["agi"] / 1000
    print(yearly_totals[["year", "returns", "exemptions", "agi_millions"]].to_string(index=False))

    # Generate plots
    print("\nGenerating visualizations...")
    plot_top_destinations_by_year(agg, top_n=10)
    plot_pre_post_comparison(comparison, top_n=15)
    plot_fire_year_spike(agg, top_n=10)
    plot_migration_by_region(outflows)

    # Save processed data
    output_path = DATA_DIR / "migration" / "butte_outflows_processed.csv"
    agg.to_csv(output_path, index=False)
    print(f"\nProcessed data saved to: {output_path}")

    comparison_path = DATA_DIR / "migration" / "butte_migration_comparison.csv"
    comparison.to_csv(comparison_path, index=False)
    print(f"Comparison data saved to: {comparison_path}")

    return agg, comparison


if __name__ == "__main__":
    agg, comparison = run_migration_analysis()
    plt.show()
