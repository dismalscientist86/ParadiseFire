"""
04_visualizations.py
Creates visualizations for the Paradise Fire analysis.
Equivalent to Stata 05_Bar_graphs_subgroups.do and 06_Percent_change.do
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from config import (
    DATA_DIR,
    GRAPHS_DIR,
    LODES_VARS,
    TOP_INDUSTRIES,
    TOP_INDUSTRY_NAMES,
)

# Set style - use compatible style name
try:
    plt.style.use("seaborn-whitegrid")
except OSError:
    plt.style.use("ggplot")  # Fallback
sns.set_palette("colorblind")

# Fire year for vertical line
FIRE_YEAR = 2018


def load_aggregated_data(data_type: str = "wac") -> pd.DataFrame:
    """Load and aggregate processed data."""
    filepath = DATA_DIR / f"{data_type}_butte_all_years.parquet"
    if not filepath.exists():
        raise FileNotFoundError(f"Data not found. Run 02_extract_process.py first.")

    df = pd.read_parquet(filepath)

    # Get count columns
    count_cols = [col for col in df.columns if col.startswith("c") and col != "createdate"]
    count_cols = [col for col in count_cols if df[col].dtype in [np.int64, np.float64, int, float]]

    # Aggregate by paradise and year
    agg = df.groupby(["paradise", "year"])[count_cols].sum().reset_index()

    return agg


def plot_total_jobs_trend(data_type: str = "wac", save: bool = True):
    """Plot total jobs trend for Paradise vs Rest of Butte County."""
    agg = load_aggregated_data(data_type)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left plot: Absolute levels (two y-axes)
    ax1 = axes[0]
    ax2 = ax1.twinx()

    paradise = agg[agg["paradise"] == 1]
    rest = agg[agg["paradise"] == 0]

    line1 = ax1.plot(paradise["year"], paradise["c000"], "o-", color="tab:blue", label="Paradise", linewidth=2)
    line2 = ax2.plot(rest["year"], rest["c000"], "s-", color="tab:orange", label="Rest of Butte County", linewidth=2)

    ax1.axvline(x=FIRE_YEAR + 0.5, color="red", linestyle="--", alpha=0.7, label="Camp Fire")

    ax1.set_xlabel("Year")
    ax1.set_ylabel("Jobs (Paradise)", color="tab:blue")
    ax2.set_ylabel("Jobs (Rest of County)", color="tab:orange")
    ax1.tick_params(axis="y", labelcolor="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:orange")

    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper left")
    ax1.set_title("Total Jobs by Location")

    # Right plot: Percent change from 2017
    ax = axes[1]

    for paradise_val, label, marker in [(1, "Paradise", "o"), (0, "Rest of Butte County", "s")]:
        data = agg[agg["paradise"] == paradise_val].copy()
        base = data[data["year"] == 2017]["c000"].values[0] if 2017 in data["year"].values else data["c000"].iloc[0]
        data["pct_change"] = 100 * (data["c000"] - base) / base
        ax.plot(data["year"], data["pct_change"], f"{marker}-", label=label, linewidth=2)

    ax.axvline(x=FIRE_YEAR + 0.5, color="red", linestyle="--", alpha=0.7, label="Camp Fire")
    ax.axhline(y=0, color="gray", linestyle="-", alpha=0.3)

    ax.set_xlabel("Year")
    ax.set_ylabel("Percent Change from 2017")
    ax.legend()
    ax.set_title("Percent Change in Total Jobs")

    plt.tight_layout()

    if save:
        filepath = GRAPHS_DIR / f"total_jobs_trend_{data_type}.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"Saved: {filepath}")

    return fig


def plot_subgroup_bars(data_type: str = "wac", subgroup: str = "age", save: bool = True):
    """
    Create bar charts for subgroup comparisons (Paradise only).

    Parameters:
    -----------
    subgroup : str
        One of: 'age', 'earnings', 'industry', 'race', 'ethnicity', 'education', 'sex'
    """
    agg = load_aggregated_data(data_type)
    paradise = agg[agg["paradise"] == 1].copy()

    subgroup_vars = {
        "age": {
            "vars": ["ca01", "ca02", "ca03"],
            "labels": ["29 and younger", "30 to 54", "55 and older"],
            "title": "Jobs by Age Group",
        },
        "earnings": {
            "vars": ["ce01", "ce02", "ce03"],
            "labels": ["$1,250 or less", "$1,251-$3,333", "More than $3,333"],
            "title": "Jobs by Monthly Earnings",
        },
        "industry": {
            "vars": TOP_INDUSTRIES,
            "labels": list(TOP_INDUSTRY_NAMES.values()),
            "title": "Jobs by Industry (Top 6)",
        },
        "education": {
            "vars": ["cd01", "cd02", "cd03", "cd04"],
            "labels": ["Less than HS", "High School", "Some College", "Bachelor's+"],
            "title": "Jobs by Educational Attainment",
        },
        "sex": {
            "vars": ["cs01", "cs02"],
            "labels": ["Male", "Female"],
            "title": "Jobs by Sex",
        },
        "ethnicity": {
            "vars": ["ct01", "ct02"],
            "labels": ["Not Hispanic/Latino", "Hispanic/Latino"],
            "title": "Jobs by Ethnicity",
        },
    }

    if subgroup not in subgroup_vars:
        raise ValueError(f"Unknown subgroup: {subgroup}. Choose from {list(subgroup_vars.keys())}")

    config = subgroup_vars[subgroup]
    vars_to_plot = [v for v in config["vars"] if v in paradise.columns]
    labels = config["labels"][: len(vars_to_plot)]

    # Reshape for plotting
    plot_data = paradise.melt(
        id_vars=["year"],
        value_vars=vars_to_plot,
        var_name="category",
        value_name="jobs",
    )
    plot_data["category"] = plot_data["category"].map(dict(zip(vars_to_plot, labels)))

    fig, ax = plt.subplots(figsize=(12, 6))

    sns.barplot(data=plot_data, x="year", y="jobs", hue="category", ax=ax)

    # Add fire line
    years = sorted(paradise["year"].unique())
    if FIRE_YEAR in years:
        fire_idx = years.index(FIRE_YEAR)
        ax.axvline(x=fire_idx + 0.5, color="red", linestyle="--", alpha=0.7, linewidth=2)

    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Jobs")
    ax.set_title(f"Paradise: {config['title']}")
    ax.legend(title="", bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()

    if save:
        filepath = GRAPHS_DIR / f"bar_{subgroup}_{data_type}.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"Saved: {filepath}")

    return fig


def plot_percent_change_grid(data_type: str = "wac", subgroup: str = "industry", base_year: int = 2017, save: bool = True):
    """
    Create grid of percent change plots comparing Paradise to Rest of County.
    """
    agg = load_aggregated_data(data_type)

    subgroup_vars = {
        "age": {
            "vars": ["ca01", "ca02", "ca03"],
            "labels": ["29 and younger", "30 to 54", "55 and older"],
        },
        "earnings": {
            "vars": ["ce01", "ce02", "ce03"],
            "labels": ["$1,250 or less", "$1,251-$3,333", "More than $3,333"],
        },
        "industry": {
            "vars": TOP_INDUSTRIES,
            "labels": list(TOP_INDUSTRY_NAMES.values()),
        },
        "education": {
            "vars": ["cd01", "cd02", "cd03", "cd04"],
            "labels": ["Less than HS", "High School", "Some College", "Bachelor's+"],
        },
        "sex": {
            "vars": ["cs01", "cs02"],
            "labels": ["Male", "Female"],
        },
    }

    config = subgroup_vars[subgroup]
    vars_to_plot = [v for v in config["vars"] if v in agg.columns]
    labels = config["labels"][: len(vars_to_plot)]

    n_vars = len(vars_to_plot)
    n_cols = min(3, n_vars)
    n_rows = (n_vars + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows), squeeze=False)
    axes = axes.flatten()

    for idx, (var, label) in enumerate(zip(vars_to_plot, labels)):
        ax = axes[idx]

        for paradise_val, loc_label, marker, color in [
            (1, "Paradise", "o", "tab:blue"),
            (0, "Rest of Butte County", "s", "tab:orange"),
        ]:
            data = agg[agg["paradise"] == paradise_val].copy()
            base_val = data[data["year"] == base_year][var].values
            if len(base_val) > 0:
                base_val = base_val[0]
                data["pct_change"] = 100 * (data[var] - base_val) / base_val
                ax.plot(data["year"], data["pct_change"], f"{marker}-", label=loc_label, color=color, linewidth=1.5)

        ax.axvline(x=FIRE_YEAR + 0.5, color="red", linestyle="--", alpha=0.5)
        ax.axhline(y=0, color="gray", linestyle="-", alpha=0.3)
        ax.set_title(label)
        ax.set_xlabel("Year")
        ax.set_ylabel("% Change")

        if idx == 0:
            ax.legend(fontsize=8)

    # Hide unused axes
    for idx in range(len(vars_to_plot), len(axes)):
        axes[idx].set_visible(False)

    plt.suptitle(f"Percent Change from {base_year} by {subgroup.title()}", fontsize=14, y=1.02)
    plt.tight_layout()

    if save:
        filepath = GRAPHS_DIR / f"pctchg_{subgroup}_{data_type}.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"Saved: {filepath}")

    return fig


def plot_did_coefficients(results_df: pd.DataFrame = None, save: bool = True):
    """Plot DiD coefficients with confidence intervals."""
    if results_df is None:
        # Try to load from file
        filepath = DATA_DIR / "did_results_wac.csv"
        if filepath.exists():
            results_df = pd.read_csv(filepath)
        else:
            print("No results found. Run 03_analysis.py first.")
            return None

    results_df = results_df.dropna(subset=["did_coef"])

    fig, ax = plt.subplots(figsize=(10, 6))

    y_pos = range(len(results_df))
    colors = ["tab:red" if p < 0.05 else "tab:blue" for p in results_df["did_pvalue"]]

    ax.barh(y_pos, results_df["did_coef"], xerr=1.96 * results_df["did_se"], color=colors, alpha=0.7, capsize=3)

    ax.axvline(x=0, color="black", linestyle="-", linewidth=0.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(results_df["name"])
    ax.set_xlabel("DiD Coefficient (Treatment Effect)")
    ax.set_title("Difference-in-Differences Estimates\n(Red = p<0.05)")

    plt.tight_layout()

    if save:
        filepath = GRAPHS_DIR / "did_coefficients.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"Saved: {filepath}")

    return fig


def generate_all_visualizations(data_type: str = "wac"):
    """Generate all standard visualizations."""
    print("=" * 60)
    print(f"Generating Visualizations ({data_type.upper()})")
    print("=" * 60)

    # Create graphs directory if needed
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

    # Total jobs trend
    print("\n1. Total jobs trend...")
    plot_total_jobs_trend(data_type)

    # Bar charts by subgroup
    for subgroup in ["age", "earnings", "industry", "education", "sex"]:
        print(f"\n2. Bar chart: {subgroup}...")
        try:
            plot_subgroup_bars(data_type, subgroup)
        except Exception as e:
            print(f"   Skipped: {e}")

    # Percent change grids
    for subgroup in ["age", "earnings", "industry", "education"]:
        print(f"\n3. Percent change: {subgroup}...")
        try:
            plot_percent_change_grid(data_type, subgroup)
        except Exception as e:
            print(f"   Skipped: {e}")

    # DiD coefficients
    print("\n4. DiD coefficient plot...")
    try:
        plot_did_coefficients()
    except Exception as e:
        print(f"   Skipped: {e}")

    print("\n" + "=" * 60)
    print(f"Visualizations saved to {GRAPHS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Paradise Fire visualizations")
    parser.add_argument("--data", choices=["wac", "rac"], default="wac")
    parser.add_argument("--plot", choices=["all", "trend", "bars", "pctchg", "did"], default="all")
    parser.add_argument("--subgroup", default="industry")

    args = parser.parse_args()

    if args.plot == "all":
        generate_all_visualizations(args.data)
    elif args.plot == "trend":
        plot_total_jobs_trend(args.data)
    elif args.plot == "bars":
        plot_subgroup_bars(args.data, args.subgroup)
    elif args.plot == "pctchg":
        plot_percent_change_grid(args.data, args.subgroup)
    elif args.plot == "did":
        plot_did_coefficients()

    plt.show()
