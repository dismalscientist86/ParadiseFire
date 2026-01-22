"""
05_synthetic_control.py
Implements synthetic control method for Paradise Fire analysis.

Creates a "synthetic Paradise" from weighted combination of other California
tracts that best match Paradise's pre-fire characteristics.
"""
import pandas as pd
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from pathlib import Path
from config import (
    DATA_DIR,
    GRAPHS_DIR,
    PARADISE_TRACTS,
    BUTTE_COUNTY_FIPS,
)

# Pre-treatment years (before Nov 2018 fire)
PRE_YEARS = [2013, 2014, 2015, 2016, 2017, 2018]
POST_YEARS = [2019, 2020, 2021, 2022, 2023]
FIRE_YEAR = 2018


def load_california_tract_data(data_type: str = "wac") -> pd.DataFrame:
    """
    Load and aggregate California LODES data to tract-year level.

    This processes the raw CSV files to get all California tracts,
    not just Butte County.
    """
    if data_type == "wac":
        data_dir = DATA_DIR / "lodes_wac"
        geocode_col = "w_geocode"
    else:
        data_dir = DATA_DIR / "lodes_rac"
        geocode_col = "h_geocode"

    all_data = []

    for year in range(2013, 2024):
        filepath = data_dir / f"ca_{data_type}_S000_JT00_{year}.csv"
        if not filepath.exists():
            print(f"  Skipping {year} - file not found")
            continue

        print(f"  Loading {year}...")
        df = pd.read_csv(filepath, dtype={geocode_col: str})
        df.columns = df.columns.str.lower()

        # Ensure geocode is properly formatted
        df[geocode_col] = df[geocode_col].str.zfill(15)

        # Extract tract (11 digits)
        tract_col = geocode_col.replace("geocode", "tract")
        df[tract_col] = df[geocode_col].str[:11]

        # Aggregate to tract level
        count_cols = [c for c in df.columns if c.startswith('c') and c != 'createdate']
        tract_agg = df.groupby(tract_col)[count_cols].sum().reset_index()
        tract_agg["year"] = year

        all_data.append(tract_agg)

    result = pd.concat(all_data, ignore_index=True)

    # Rename tract column consistently
    if "w_tract" in result.columns:
        result = result.rename(columns={"w_tract": "tract"})
    elif "h_tract" in result.columns:
        result = result.rename(columns={"h_tract": "tract"})

    return result


def prepare_synthetic_control_data(df: pd.DataFrame, outcome_var: str = "c000", normalize: bool = True):
    """
    Prepare data matrices for synthetic control estimation.

    Parameters:
    -----------
    normalize : bool - If True, normalize to index (base year = 100)

    Returns:
    --------
    treated : DataFrame - Paradise aggregate by year
    donors : DataFrame - Potential donor tracts (pivoted: tracts x years)
    """
    # Identify Paradise tracts
    df["is_paradise"] = df["tract"].isin(PARADISE_TRACTS).astype(int)

    # Aggregate Paradise tracts together
    paradise_df = df[df["is_paradise"] == 1].groupby("year")[outcome_var].sum().reset_index()
    paradise_df.columns = ["year", "paradise"]

    # Get donor pool (exclude Butte County to avoid spillovers)
    donor_df = df[
        (df["is_paradise"] == 0) &
        (~df["tract"].str.startswith(BUTTE_COUNTY_FIPS))
    ].copy()

    # Pivot donors to wide format (tract x year)
    donor_pivot = donor_df.pivot_table(
        index="tract",
        columns="year",
        values=outcome_var,
        aggfunc="sum"
    )

    # Keep only tracts with complete data and minimum job count
    donor_pivot = donor_pivot.dropna()
    # Filter out very small tracts (less than 50 jobs in base year)
    if 2017 in donor_pivot.columns:
        donor_pivot = donor_pivot[donor_pivot[2017] >= 50]

    if normalize:
        # Normalize to 2017 = 100 (year before fire)
        base_year = 2017
        if base_year in paradise_df["year"].values:
            paradise_base = paradise_df[paradise_df["year"] == base_year]["paradise"].values[0]
            paradise_df["paradise"] = 100 * paradise_df["paradise"] / paradise_base

        if base_year in donor_pivot.columns:
            donor_base = donor_pivot[base_year].values.reshape(-1, 1)
            for col in donor_pivot.columns:
                donor_pivot[col] = 100 * donor_pivot[col] / donor_base.flatten()
            # Remove tracts with inf/nan after normalization
            donor_pivot = donor_pivot.replace([np.inf, -np.inf], np.nan).dropna()

    print(f"Paradise years: {list(paradise_df['year'])}")
    print(f"Donor tracts with complete data: {len(donor_pivot)}")

    return paradise_df, donor_pivot


def synthetic_control_weights(
    treated_pre: np.ndarray,
    donors_pre: np.ndarray,
    treated_covariates: np.ndarray = None,
    donor_covariates: np.ndarray = None,
) -> np.ndarray:
    """
    Find optimal weights for synthetic control.

    Minimizes the mean squared error between treated unit and
    weighted combination of donors in pre-treatment period.

    Parameters:
    -----------
    treated_pre : array (T_pre,) - Treated unit outcomes in pre-period
    donors_pre : array (N_donors, T_pre) - Donor outcomes in pre-period

    Returns:
    --------
    weights : array (N_donors,) - Optimal weights (sum to 1, non-negative)
    """
    n_donors = donors_pre.shape[0]

    def objective(w):
        """MSE between treated and synthetic control"""
        synthetic = donors_pre.T @ w  # (T_pre,)
        return np.mean((treated_pre - synthetic) ** 2)

    # Constraints: weights sum to 1, non-negative
    constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1},
    ]
    bounds = [(0, 1) for _ in range(n_donors)]

    # Initial guess: equal weights
    w0 = np.ones(n_donors) / n_donors

    # Optimize
    result = minimize(
        objective,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-10}
    )

    return result.x


def run_synthetic_control(
    data_type: str = "wac",
    outcome_var: str = "c000",
    max_donors: int = 1000,
    normalize: bool = True,
):
    """
    Run full synthetic control analysis.

    Parameters:
    -----------
    data_type : str - "wac" or "rac"
    outcome_var : str - Outcome variable (e.g., "c000" for total jobs)
    max_donors : int - Maximum number of donor tracts to consider
    normalize : bool - If True, normalize data to index (2017=100)
    """
    print("=" * 70)
    print(f"Synthetic Control Analysis ({data_type.upper()})")
    print("=" * 70)

    # Load data
    print("\nLoading California tract-level data...")
    df = load_california_tract_data(data_type)
    print(f"Total tract-years: {len(df):,}")
    print(f"Unique tracts: {df['tract'].nunique():,}")

    # Prepare data
    print("\nPreparing synthetic control data...")
    paradise_df, donor_pivot = prepare_synthetic_control_data(df, outcome_var)

    # Select donors based on pre-treatment similarity
    print(f"Selecting best donor matches from {len(donor_pivot)} available...")

    # Calculate Paradise per-tract average (4 tracts)
    paradise_per_tract = paradise_df[paradise_df["year"].isin(PRE_YEARS)]["paradise"].mean() / 4

    # Calculate pre-treatment characteristics for each donor
    pre_cols = [c for c in PRE_YEARS if c in donor_pivot.columns]
    donor_pre_means = donor_pivot[pre_cols].mean(axis=1)
    donor_pre_trends = donor_pivot[pre_cols].apply(
        lambda row: np.polyfit(range(len(pre_cols)), row.values, 1)[0] if row.notna().all() else 0,
        axis=1
    )

    # Paradise trend
    paradise_pre = paradise_df[paradise_df["year"].isin(PRE_YEARS)]["paradise"].values
    paradise_trend = np.polyfit(range(len(paradise_pre)), paradise_pre, 1)[0] / 4

    # Score donors by similarity (lower is better)
    # Normalize each component
    mean_diff = np.abs(donor_pre_means - paradise_per_tract) / paradise_per_tract
    trend_diff = np.abs(donor_pre_trends - paradise_trend) / (np.abs(paradise_trend) + 1)

    # Combined score
    similarity_score = mean_diff + 0.5 * trend_diff

    # Select top donors by similarity
    n_select = min(max_donors, len(donor_pivot))
    best_donors = similarity_score.nsmallest(n_select).index
    donor_pivot = donor_pivot.loc[best_donors]
    print(f"Selected {len(donor_pivot)} most similar donors")

    # Extract pre-treatment data
    pre_years_available = [y for y in PRE_YEARS if y in paradise_df["year"].values]
    post_years_available = [y for y in POST_YEARS if y in paradise_df["year"].values]

    treated_pre = paradise_df[paradise_df["year"].isin(pre_years_available)]["paradise"].values
    donors_pre = donor_pivot[pre_years_available].values  # (N_donors, T_pre)

    print(f"\nPre-treatment years: {pre_years_available}")
    print(f"Post-treatment years: {post_years_available}")
    print(f"Paradise pre-treatment mean: {treated_pre.mean():,.0f}")

    # Find optimal weights
    print("\nFinding optimal synthetic control weights...")
    weights = synthetic_control_weights(treated_pre, donors_pre)

    # Get top donors
    top_n = 10
    top_indices = np.argsort(weights)[-top_n:][::-1]
    top_weights = weights[top_indices]
    top_tracts = donor_pivot.index[top_indices]

    print(f"\nTop {top_n} donor tracts:")
    for tract, w in zip(top_tracts, top_weights):
        if w > 0.001:
            print(f"  {tract}: {w:.4f}")

    # Calculate synthetic control for all years
    all_years = sorted(paradise_df["year"].unique())
    donors_all = donor_pivot[all_years].values
    synthetic_all = donors_all.T @ weights

    # Create results DataFrame
    results = pd.DataFrame({
        "year": all_years,
        "paradise": paradise_df.set_index("year").loc[all_years, "paradise"].values,
        "synthetic": synthetic_all,
    })
    results["gap"] = results["paradise"] - results["synthetic"]
    results["period"] = results["year"].apply(lambda y: "pre" if y <= FIRE_YEAR else "post")

    # Calculate treatment effect
    pre_gap = results[results["period"] == "pre"]["gap"].mean()
    post_gap = results[results["period"] == "post"]["gap"].mean()
    treatment_effect = post_gap - pre_gap

    print("\n" + "-" * 70)
    print("Results")
    print("-" * 70)
    print(f"Pre-treatment gap (Paradise - Synthetic): {pre_gap:,.1f}")
    print(f"Post-treatment gap (Paradise - Synthetic): {post_gap:,.1f}")
    print(f"Treatment Effect (Synthetic DiD): {treatment_effect:,.1f}")

    # Pre-treatment fit
    pre_mse = np.mean((results[results["period"] == "pre"]["gap"]) ** 2)
    pre_rmse = np.sqrt(pre_mse)
    print(f"Pre-treatment RMSE: {pre_rmse:,.1f}")

    # Save results
    results_path = DATA_DIR / f"synthetic_control_{data_type}_{outcome_var}.csv"
    results.to_csv(results_path, index=False)
    print(f"\nResults saved to {results_path}")

    # Save weights
    weights_df = pd.DataFrame({
        "tract": donor_pivot.index,
        "weight": weights
    })
    weights_df = weights_df[weights_df["weight"] > 0.001].sort_values("weight", ascending=False)
    weights_path = DATA_DIR / f"synthetic_weights_{data_type}_{outcome_var}.csv"
    weights_df.to_csv(weights_path, index=False)

    return results, weights, treatment_effect


def plot_synthetic_control(results: pd.DataFrame, outcome_label: str = "Total Jobs", save: bool = True):
    """Plot synthetic control results."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: Paradise vs Synthetic
    ax = axes[0]
    ax.plot(results["year"], results["paradise"], "o-", label="Paradise (Actual)", linewidth=2)
    ax.plot(results["year"], results["synthetic"], "s--", label="Synthetic Paradise", linewidth=2)
    ax.axvline(x=FIRE_YEAR + 0.5, color="red", linestyle="--", alpha=0.7, label="Camp Fire")
    ax.set_xlabel("Year")
    ax.set_ylabel(outcome_label)
    ax.set_title(f"Paradise vs Synthetic Control: {outcome_label}")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Right: Gap (Treatment Effect)
    ax = axes[1]
    colors = ["blue" if p == "pre" else "red" for p in results["period"]]
    ax.bar(results["year"], results["gap"], color=colors, alpha=0.7)
    ax.axvline(x=FIRE_YEAR + 0.5, color="red", linestyle="--", alpha=0.7)
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax.set_xlabel("Year")
    ax.set_ylabel("Gap (Paradise - Synthetic)")
    ax.set_title("Treatment Effect: Gap Between Actual and Synthetic")
    ax.grid(True, alpha=0.3)

    # Add legend for colors
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="blue", alpha=0.7, label="Pre-Fire"),
        Patch(facecolor="red", alpha=0.7, label="Post-Fire"),
    ]
    ax.legend(handles=legend_elements)

    plt.tight_layout()

    if save:
        filepath = GRAPHS_DIR / "synthetic_control.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"Saved: {filepath}")

    return fig


def run_placebo_tests(
    data_type: str = "wac",
    outcome_var: str = "c000",
    n_placebos: int = 50,
):
    """
    Run placebo tests by applying synthetic control to donor tracts.

    This helps assess whether the Paradise effect is unusual compared
    to what we'd expect by chance.
    """
    print("=" * 70)
    print("Placebo Tests")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    df = load_california_tract_data(data_type)

    # Get Paradise results first
    paradise_df, donor_pivot = prepare_synthetic_control_data(df, outcome_var)

    # Sample placebo tracts
    placebo_tracts = np.random.choice(donor_pivot.index, size=min(n_placebos, len(donor_pivot)), replace=False)

    placebo_effects = []

    print(f"\nRunning {len(placebo_tracts)} placebo tests...")
    for i, placebo_tract in enumerate(placebo_tracts):
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{len(placebo_tracts)}")

        # Treat this tract as if it were treated
        placebo_outcome = donor_pivot.loc[placebo_tract].values

        # Create donor pool excluding this tract
        other_donors = donor_pivot.drop(placebo_tract)

        pre_years = [y for y in PRE_YEARS if y in donor_pivot.columns]
        post_years = [y for y in POST_YEARS if y in donor_pivot.columns]

        placebo_pre = donor_pivot.loc[placebo_tract, pre_years].values
        donors_pre = other_donors[pre_years].values

        # Find weights
        try:
            weights = synthetic_control_weights(placebo_pre, donors_pre)

            # Calculate effect
            donors_all = other_donors[pre_years + post_years].values
            synthetic_all = donors_all.T @ weights
            actual_all = donor_pivot.loc[placebo_tract, pre_years + post_years].values

            gap = actual_all - synthetic_all
            pre_gap = gap[:len(pre_years)].mean()
            post_gap = gap[len(pre_years):].mean()
            effect = post_gap - pre_gap

            placebo_effects.append(effect)
        except:
            continue

    placebo_effects = np.array(placebo_effects)

    # Compare Paradise effect to placebos
    # (Need to run Paradise analysis to get its effect)

    print(f"\nPlacebo effect distribution:")
    print(f"  Mean: {np.mean(placebo_effects):,.1f}")
    print(f"  Std: {np.std(placebo_effects):,.1f}")
    print(f"  Min: {np.min(placebo_effects):,.1f}")
    print(f"  Max: {np.max(placebo_effects):,.1f}")

    return placebo_effects


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Synthetic Control Analysis")
    parser.add_argument("--data", choices=["wac", "rac"], default="wac")
    parser.add_argument("--outcome", default="c000", help="Outcome variable")
    parser.add_argument("--max-donors", type=int, default=1000)
    parser.add_argument("--placebo", action="store_true", help="Run placebo tests")

    args = parser.parse_args()

    if args.placebo:
        run_placebo_tests(args.data, args.outcome)
    else:
        results, weights, effect = run_synthetic_control(
            args.data,
            args.outcome,
            args.max_donors
        )
        plot_synthetic_control(results)
        plt.show()
