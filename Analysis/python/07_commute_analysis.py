"""
07_commute_analysis.py
Analyzes LODES Origin-Destination data to understand commute patterns
for Paradise residents before and after the Camp Fire.

Questions:
1. Where did Paradise residents work? (home in Paradise, work elsewhere)
2. Where did Paradise workers live? (work in Paradise, home elsewhere)
3. How did these patterns change after the fire?
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import requests
import gzip
import shutil

from config import DATA_DIR, GRAPHS_COMMUTE, PARADISE_TRACTS, BUTTE_COUNTY_FIPS, YEARS

# LODES OD data URL pattern
LODES_OD_URL = "https://lehd.ces.census.gov/data/lodes/LODES8/ca/od/ca_od_main_JT00_{year}.csv.gz"

# Key geographic areas for analysis
SACRAMENTO_COUNTY = "06067"
CHICO_TRACTS_PREFIX = "060070001"  # Chico area tracts (approximate)


def download_od_data(years: list = None, force: bool = False) -> dict:
    """
    Download LODES Origin-Destination data for California.
    """
    if years is None:
        years = YEARS

    od_dir = DATA_DIR / "lodes_od"
    od_dir.mkdir(parents=True, exist_ok=True)

    data = {}

    for year in years:
        csv_path = od_dir / f"ca_od_main_JT00_{year}.csv"
        gz_path = od_dir / f"ca_od_main_JT00_{year}.csv.gz"

        if csv_path.exists() and not force:
            print(f"  {year}: Loading from cache")
            # Load only needed columns to save memory
            df = pd.read_csv(csv_path, dtype={"w_geocode": str, "h_geocode": str},
                           usecols=["w_geocode", "h_geocode", "S000", "SA01", "SA02", "SA03",
                                   "SE01", "SE02", "SE03"])
        else:
            url = LODES_OD_URL.format(year=year)
            print(f"  {year}: Downloading from {url}...")
            try:
                response = requests.get(url, timeout=120, stream=True)
                response.raise_for_status()

                # Save gzipped file
                with open(gz_path, "wb") as f:
                    f.write(response.content)

                # Decompress
                with gzip.open(gz_path, "rb") as f_in:
                    with open(csv_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)

                df = pd.read_csv(csv_path, dtype={"w_geocode": str, "h_geocode": str},
                               usecols=["w_geocode", "h_geocode", "S000", "SA01", "SA02", "SA03",
                                       "SE01", "SE02", "SE03"])
                print(f"    Downloaded {len(df):,} OD pairs")

                # Clean up gz file
                gz_path.unlink(missing_ok=True)

            except Exception as e:
                print(f"    Error: {e}")
                continue

        df["year"] = year
        data[year] = df

    return data


def extract_tract(geocode: pd.Series) -> pd.Series:
    """Extract 11-digit tract from 15-digit block geocode."""
    return geocode.str.zfill(15).str[:11]


def classify_location(tract: str) -> str:
    """Classify a tract as Paradise, Butte County (non-Paradise), or Other."""
    if tract in PARADISE_TRACTS:
        return "Paradise"
    elif tract.startswith(BUTTE_COUNTY_FIPS):
        return "Butte (non-Paradise)"
    elif tract.startswith("06067"):  # Sacramento County
        return "Sacramento County"
    elif tract.startswith("06"):  # Other California
        return "Other California"
    else:
        return "Out of State"


def analyze_paradise_commutes(data: dict) -> tuple:
    """
    Analyze commute patterns for Paradise.

    Returns:
    - residents_df: Where Paradise residents work
    - workers_df: Where Paradise workers live
    """
    residents_results = []
    workers_results = []

    for year, df in data.items():
        print(f"  Processing {year}...")

        # Extract tracts
        df["h_tract"] = extract_tract(df["h_geocode"])
        df["w_tract"] = extract_tract(df["w_geocode"])

        # --- Where do Paradise RESIDENTS work? ---
        # (People who live in Paradise)
        paradise_residents = df[df["h_tract"].isin(PARADISE_TRACTS)].copy()
        paradise_residents["work_location"] = paradise_residents["w_tract"].apply(classify_location)

        residents_agg = paradise_residents.groupby("work_location").agg({
            "S000": "sum",  # Total jobs
            "SA01": "sum",  # Age 29 or younger
            "SA02": "sum",  # Age 30-54
            "SA03": "sum",  # Age 55+
        }).reset_index()
        residents_agg["year"] = year
        residents_agg["direction"] = "Paradise residents work in..."
        residents_results.append(residents_agg)

        # --- Where do Paradise WORKERS live? ---
        # (People who work in Paradise)
        paradise_workers = df[df["w_tract"].isin(PARADISE_TRACTS)].copy()
        paradise_workers["home_location"] = paradise_workers["h_tract"].apply(classify_location)

        workers_agg = paradise_workers.groupby("home_location").agg({
            "S000": "sum",
            "SA01": "sum",
            "SA02": "sum",
            "SA03": "sum",
        }).reset_index()
        workers_agg["year"] = year
        workers_agg["direction"] = "Paradise workers live in..."
        workers_results.append(workers_agg)

    residents_df = pd.concat(residents_results, ignore_index=True)
    workers_df = pd.concat(workers_results, ignore_index=True)

    return residents_df, workers_df


def summarize_commute_patterns(residents_df: pd.DataFrame, workers_df: pd.DataFrame):
    """Print summary of commute patterns."""

    print("\n" + "=" * 70)
    print("WHERE PARADISE RESIDENTS WORK")
    print("=" * 70)

    pivot_residents = residents_df.pivot_table(
        index="year", columns="work_location", values="S000", aggfunc="sum"
    ).fillna(0)

    # Reorder columns
    col_order = ["Paradise", "Butte (non-Paradise)", "Sacramento County", "Other California", "Out of State"]
    col_order = [c for c in col_order if c in pivot_residents.columns]
    pivot_residents = pivot_residents[col_order]
    pivot_residents["Total"] = pivot_residents.sum(axis=1)

    print(pivot_residents.astype(int).to_string())

    print("\n" + "=" * 70)
    print("WHERE PARADISE WORKERS LIVE")
    print("=" * 70)

    pivot_workers = workers_df.pivot_table(
        index="year", columns="home_location", values="S000", aggfunc="sum"
    ).fillna(0)

    col_order = ["Paradise", "Butte (non-Paradise)", "Sacramento County", "Other California", "Out of State"]
    col_order = [c for c in col_order if c in pivot_workers.columns]
    pivot_workers = pivot_workers[col_order]
    pivot_workers["Total"] = pivot_workers.sum(axis=1)

    print(pivot_workers.astype(int).to_string())

    return pivot_residents, pivot_workers


def plot_commute_patterns(residents_df: pd.DataFrame, workers_df: pd.DataFrame, save: bool = True):
    """Plot commute pattern changes over time."""

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Color scheme
    colors = {
        "Paradise": "#2ca02c",
        "Butte (non-Paradise)": "#1f77b4",
        "Sacramento County": "#ff7f0e",
        "Other California": "#d62728",
        "Out of State": "#9467bd",
    }

    years = sorted(residents_df["year"].unique())

    # --- Top Left: Where Paradise residents work (absolute) ---
    ax = axes[0, 0]
    pivot = residents_df.pivot_table(index="year", columns="work_location", values="S000", aggfunc="sum").fillna(0)
    for location in colors.keys():
        if location in pivot.columns:
            ax.plot(years, pivot.loc[years, location], "o-", color=colors[location],
                   linewidth=2, markersize=6, label=location)

    ax.axvline(x=2018.5, color="red", linestyle="--", linewidth=2, alpha=0.7, label="Camp Fire")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Jobs")
    ax.set_title("Where Paradise Residents Work")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    # --- Top Right: Where Paradise residents work (share) ---
    ax = axes[0, 1]
    pivot_share = pivot.div(pivot.sum(axis=1), axis=0) * 100
    for location in colors.keys():
        if location in pivot_share.columns:
            ax.plot(years, pivot_share.loc[years, location], "o-", color=colors[location],
                   linewidth=2, markersize=6, label=location)

    ax.axvline(x=2018.5, color="red", linestyle="--", linewidth=2, alpha=0.7, label="Camp Fire")
    ax.set_xlabel("Year")
    ax.set_ylabel("Share (%)")
    ax.set_title("Where Paradise Residents Work (Share)")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    # --- Bottom Left: Where Paradise workers live (absolute) ---
    ax = axes[1, 0]
    pivot = workers_df.pivot_table(index="year", columns="home_location", values="S000", aggfunc="sum").fillna(0)
    for location in colors.keys():
        if location in pivot.columns:
            ax.plot(years, pivot.loc[years, location], "o-", color=colors[location],
                   linewidth=2, markersize=6, label=location)

    ax.axvline(x=2018.5, color="red", linestyle="--", linewidth=2, alpha=0.7, label="Camp Fire")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Jobs")
    ax.set_title("Where Paradise Workers Live")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    # --- Bottom Right: Where Paradise workers live (share) ---
    ax = axes[1, 1]
    pivot_share = pivot.div(pivot.sum(axis=1), axis=0) * 100
    for location in colors.keys():
        if location in pivot_share.columns:
            ax.plot(years, pivot_share.loc[years, location], "o-", color=colors[location],
                   linewidth=2, markersize=6, label=location)

    ax.axvline(x=2018.5, color="red", linestyle="--", linewidth=2, alpha=0.7, label="Camp Fire")
    ax.set_xlabel("Year")
    ax.set_ylabel("Share (%)")
    ax.set_title("Where Paradise Workers Live (Share)")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save:
        filepath = GRAPHS_COMMUTE / "commute_patterns.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"Saved: {filepath}")

    return fig


def plot_live_work_balance(residents_df: pd.DataFrame, workers_df: pd.DataFrame, save: bool = True):
    """
    Plot the live-work balance: jobs held by Paradise residents vs jobs in Paradise.
    """
    years = sorted(residents_df["year"].unique())

    # Total jobs held by Paradise residents
    jobs_held = residents_df.groupby("year")["S000"].sum()

    # Total jobs located in Paradise
    jobs_in_paradise = workers_df.groupby("year")["S000"].sum()

    # Jobs held by Paradise residents that are IN Paradise
    live_work_paradise = residents_df[residents_df["work_location"] == "Paradise"].groupby("year")["S000"].sum()

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(years, jobs_held.loc[years], "o-", color="#1f77b4", linewidth=2.5,
            markersize=8, label="Jobs held by Paradise residents")
    ax.plot(years, jobs_in_paradise.loc[years], "s-", color="#ff7f0e", linewidth=2.5,
            markersize=8, label="Jobs located in Paradise")
    ax.plot(years, live_work_paradise.reindex(years, fill_value=0), "^-", color="#2ca02c", linewidth=2.5,
            markersize=8, label="Live AND work in Paradise")

    ax.axvline(x=2018.5, color="red", linestyle="--", linewidth=2, alpha=0.7, label="Camp Fire")

    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Number of Jobs", fontsize=12)
    ax.set_title("Paradise Employment: Residents vs Local Jobs", fontsize=14)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save:
        filepath = GRAPHS_COMMUTE / "live_work_balance.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"Saved: {filepath}")

    return fig


def run_commute_analysis():
    """Run full commute pattern analysis."""

    print("=" * 70)
    print("LODES Origin-Destination Commute Analysis")
    print("=" * 70)

    # Download OD data
    print("\nDownloading LODES OD data...")
    data = download_od_data()

    if not data:
        print("ERROR: No data downloaded")
        return None, None

    # Analyze commute patterns
    print("\nAnalyzing Paradise commute patterns...")
    residents_df, workers_df = analyze_paradise_commutes(data)

    # Summarize
    pivot_residents, pivot_workers = summarize_commute_patterns(residents_df, workers_df)

    # Generate plots
    print("\nGenerating visualizations...")
    plot_commute_patterns(residents_df, workers_df)
    plot_live_work_balance(residents_df, workers_df)

    # Save processed data
    output_dir = DATA_DIR / "commute"
    output_dir.mkdir(parents=True, exist_ok=True)

    residents_df.to_csv(output_dir / "paradise_residents_work_locations.csv", index=False)
    workers_df.to_csv(output_dir / "paradise_workers_home_locations.csv", index=False)
    print(f"\nData saved to {output_dir}")

    return residents_df, workers_df


if __name__ == "__main__":
    residents_df, workers_df = run_commute_analysis()
    plt.show()
