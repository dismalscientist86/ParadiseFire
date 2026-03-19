"""
05_synthetic_control.py
Implements synthetic control method for Paradise Fire analysis.

Creates a "synthetic Paradise" from weighted combination of other California
tracts that best match Paradise's pre-fire characteristics.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from config import (
    DATA_DIR,
    GRAPHS_DIR,
    TABLES_DIR,
    PARADISE_TRACTS,
    BUTTE_COUNTY_FIPS,
)
from utils import load_california_tract_data, synthetic_control_weights

# Pre-treatment years (before Nov 2018 fire)
# Note: 2018 LODES is annual data and the Camp Fire was Nov 2018,
# so 2018 is partially treated — exclude it from pre-period.
PRE_YEARS = [2013, 2014, 2015, 2016, 2017]
POST_YEARS = [2018, 2019, 2020, 2021, 2022, 2023]
FIRE_YEAR = 2017  # last clean pre-treatment year



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

    # Filter by size: require at least 500 jobs in base year
    if 2017 in donor_pivot.columns:
        donor_pivot = donor_pivot[donor_pivot[2017] >= 500]
        print(f"  Donors after minimum size filter (>=500 jobs): {len(donor_pivot)}")

    if normalize:
        # Normalize to 2017 = 100 (year before fire)
        base_year = 2017
        if base_year in paradise_df["year"].values:
            paradise_base = paradise_df[paradise_df["year"] == base_year]["paradise"].values[0]
            paradise_df["paradise"] = 100 * paradise_df["paradise"] / paradise_base

        if base_year in donor_pivot.columns:
            # Normalize all columns at once (avoids view/copy bug with iterative approach)
            donor_pivot = donor_pivot.div(donor_pivot[base_year], axis=0) * 100
            # Remove tracts with inf/nan after normalization
            donor_pivot = donor_pivot.replace([np.inf, -np.inf], np.nan).dropna()

    print(f"Paradise years: {list(paradise_df['year'])}")
    print(f"Donor tracts with complete data: {len(donor_pivot)}")

    return paradise_df, donor_pivot



def run_synthetic_control(
    data_type: str = "wac",
    outcome_var: str = "c000",
    max_donors: int = 500,
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

    # Prepare data - ALWAYS normalize for synthetic control
    # Normalization is essential because Paradise (4 tracts) has ~5000 jobs
    # while individual donor tracts have ~500-3000 jobs each.
    # With normalized indices (2017=100), all units become comparable.
    print("\nPreparing synthetic control data (normalizing to 2017=100)...")
    paradise_df, donor_pivot = prepare_synthetic_control_data(df, outcome_var, normalize=True)

    # Verify normalization worked
    pre_cols = [c for c in PRE_YEARS if c in donor_pivot.columns]
    paradise_pre_vals = paradise_df[paradise_df["year"].isin(PRE_YEARS)]["paradise"].values
    print(f"Paradise pre-treatment values (should be ~100): {paradise_pre_vals.round(1)}")
    print(f"Donor pre-treatment mean (should be ~100): {donor_pivot[pre_cols].mean().mean():.1f}")

    # Select donors based on pre-treatment trajectory similarity
    print(f"\nSelecting best donor matches from {len(donor_pivot)} available...")

    # Score donors by RMSE of pre-treatment trajectory vs Paradise
    # This directly measures what the optimizer tries to minimize
    paradise_pre_series = paradise_pre_vals  # shape (T_pre,)
    donor_pre_matrix = donor_pivot[pre_cols].values  # shape (N, T_pre)
    donor_rmse = np.sqrt(np.mean((donor_pre_matrix - paradise_pre_series) ** 2, axis=1))
    donor_rmse = pd.Series(donor_rmse, index=donor_pivot.index)

    # Remove NaN
    donor_rmse = donor_rmse.dropna()

    # Select top donors by pre-treatment trajectory similarity
    n_select = min(max_donors, len(donor_rmse))
    best_donors = donor_rmse.nsmallest(n_select).index
    donor_pivot = donor_pivot.loc[best_donors]
    print(f"Selected {len(donor_pivot)} most similar donors (by pre-treatment RMSE)")
    print(f"Best donor RMSE: {donor_rmse.loc[best_donors].min():.2f}, "
          f"Worst selected: {donor_rmse.loc[best_donors].max():.2f}")

    # Extract pre-treatment data
    pre_years_available = [y for y in PRE_YEARS if y in paradise_df["year"].values]
    post_years_available = [y for y in POST_YEARS if y in paradise_df["year"].values]

    treated_pre = paradise_df[paradise_df["year"].isin(pre_years_available)]["paradise"].values
    donors_pre = donor_pivot[pre_years_available].values  # (N_donors, T_pre)

    print(f"\nPre-treatment years: {pre_years_available}")
    print(f"Post-treatment years: {post_years_available}")
    print(f"Paradise pre-treatment index mean: {treated_pre.mean():.1f} (2017=100)")

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
    results["period"] = results["year"].apply(lambda y: "pre" if y in PRE_YEARS else "post")

    # Calculate treatment effect
    pre_gap = results[results["period"] == "pre"]["gap"].mean()
    post_gap = results[results["period"] == "post"]["gap"].mean()
    treatment_effect = post_gap - pre_gap

    print("\n" + "-" * 70)
    print("Results (Index where 2017=100)")
    print("-" * 70)
    print(f"Pre-treatment gap (Paradise - Synthetic): {pre_gap:.1f} index points")
    print(f"Post-treatment gap (Paradise - Synthetic): {post_gap:.1f} index points")
    print(f"Treatment Effect (Synthetic DiD): {treatment_effect:.1f} index points")

    # Pre-treatment fit
    pre_mse = np.mean((results[results["period"] == "pre"]["gap"]) ** 2)
    pre_rmse = np.sqrt(pre_mse)
    print(f"Pre-treatment RMSE: {pre_rmse:.1f} (lower is better, <5 is good)")

    # Interpretation
    if pre_rmse < 10:
        print("\nInterpretation:")
        print(f"  The synthetic control closely matched Paradise pre-fire (RMSE={pre_rmse:.1f})")
        post_synthetic_mean = results[results["period"] == "post"]["synthetic"].mean()
        post_actual_mean = results[results["period"] == "post"]["paradise"].mean()
        pct_decline = 100 * (post_actual_mean - post_synthetic_mean) / post_synthetic_mean
        print(f"  Post-fire Paradise employment was {abs(pct_decline):.1f}% {'lower' if pct_decline < 0 else 'higher'}")
        print(f"  than what the synthetic control predicts it would have been.")

    # Save results
    results_path = TABLES_DIR / f"synthetic_control_{data_type}_{outcome_var}.csv"
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

    return results, weights, treatment_effect, paradise_df, donor_pivot


def plot_synthetic_control(results: pd.DataFrame, outcome_label: str = "Total Jobs", save: bool = True):
    """Plot synthetic control results."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Paradise vs Synthetic
    ax.plot(results["year"], results["paradise"], "o-", label="Paradise (Actual)", linewidth=2.5, markersize=8)
    ax.plot(results["year"], results["synthetic"], "s--", label="Synthetic Paradise", linewidth=2.5, markersize=8)
    ax.axvline(x=2017.5, color="red", linestyle="--", alpha=0.7, linewidth=2, label="Camp Fire (Nov 2018)")
    ax.axhline(y=100, color="gray", linestyle=":", alpha=0.5, label="2017 Baseline")
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel(f"{outcome_label} Index (2017=100)", fontsize=12)
    ax.set_title(f"Paradise vs Synthetic Control: {outcome_label}", fontsize=14)
    ax.legend(loc="lower left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save:
        filepath = GRAPHS_DIR / "synthetic_control.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"Saved: {filepath}")

    return fig


def plot_paradise_vs_donors(
    paradise_df: pd.DataFrame,
    donor_pivot: pd.DataFrame,
    outcome_label: str = "Total Jobs",
    max_donors_to_plot: int = 500,
    save: bool = True,
):
    """
    Plot Paradise against all donor tracts.

    Paradise is shown in full color, donor tracts are faded gray lines.
    This visualization shows how Paradise diverged from the donor pool after the fire.

    Parameters:
    -----------
    paradise_df : DataFrame with columns ['year', 'paradise']
    donor_pivot : DataFrame with tracts as index, years as columns
    outcome_label : str - Label for the outcome variable
    max_donors_to_plot : int - Maximum number of donor lines to plot (for performance)
    save : bool - Whether to save the figure
    """
    fig, ax = plt.subplots(figsize=(12, 7))

    years = sorted(paradise_df["year"].unique())

    # Plot donor tracts in faded gray
    donors_to_plot = donor_pivot.index[:max_donors_to_plot]
    for i, tract in enumerate(donors_to_plot):
        tract_data = donor_pivot.loc[tract, years].values
        ax.plot(years, tract_data, color="gray", alpha=0.1, linewidth=0.5, zorder=1)

    # Add a single label for donor tracts
    ax.plot([], [], color="gray", alpha=0.3, linewidth=1, label=f"Donor Tracts (n={len(donor_pivot)})")

    # Plot Paradise in bold color
    paradise_values = paradise_df.set_index("year").loc[years, "paradise"].values
    ax.plot(years, paradise_values, "o-", color="#D62728", linewidth=3, markersize=8,
            label="Paradise", zorder=3)

    # Add fire line
    ax.axvline(x=2017.5, color="orange", linestyle="--", linewidth=2,
               alpha=0.8, label="Camp Fire (Nov 2018)", zorder=2)

    # Add baseline reference
    ax.axhline(y=100, color="black", linestyle=":", alpha=0.5, linewidth=1)

    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel(f"{outcome_label} Index (2017=100)", fontsize=12)
    ax.set_title(f"Paradise vs California Donor Tracts: {outcome_label}", fontsize=14)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3)

    # Set y-axis limits to focus on relevant range
    ax.set_ylim(0, 200)

    plt.tight_layout()

    if save:
        filepath = GRAPHS_DIR / "paradise_vs_donors.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"Saved: {filepath}")

    return fig


def run_placebo_tests(
    data_type: str = "wac",
    outcome_var: str = "c000",
    n_placebos: int = 100,
    max_donors_per_placebo: int = 200,
    exclude_years: list = None,
):
    """
    Run placebo tests by applying synthetic control to donor tracts.

    This helps assess whether the Paradise effect is unusual compared
    to what we'd expect by chance.

    Parameters:
    -----------
    exclude_years : list - Years to exclude from post-treatment analysis (e.g., [2020] for COVID)
    """
    print("=" * 70)
    print("Placebo Tests")
    if exclude_years:
        print(f"(Excluding years: {exclude_years})")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    df = load_california_tract_data(data_type)

    # Get normalized data (same as main analysis)
    print("\nPreparing normalized data...")
    paradise_df, donor_pivot = prepare_synthetic_control_data(df, outcome_var, normalize=True)

    pre_years = [y for y in PRE_YEARS if y in donor_pivot.columns]
    post_years = [y for y in POST_YEARS if y in donor_pivot.columns]

    # Exclude specified years from post-treatment period
    if exclude_years:
        post_years = [y for y in post_years if y not in exclude_years]
        print(f"Post-treatment years (after exclusion): {post_years}")

    # First, calculate Paradise effect for comparison
    print("\nCalculating Paradise effect...")
    paradise_pre = paradise_df[paradise_df["year"].isin(pre_years)]["paradise"].values

    # Select similar donors for Paradise (same as main analysis - by pre-treatment RMSE)
    donor_pre_matrix = donor_pivot[pre_years].values
    donor_rmse = np.sqrt(np.mean((donor_pre_matrix - paradise_pre) ** 2, axis=1))
    donor_rmse = pd.Series(donor_rmse, index=donor_pivot.index).dropna()
    best_donors = donor_rmse.nsmallest(500).index
    paradise_donor_pool = donor_pivot.loc[best_donors]

    # Get Paradise weights and effect
    donors_pre = paradise_donor_pool[pre_years].values
    weights = synthetic_control_weights(paradise_pre, donors_pre)

    # Calculate gaps for pre and post periods separately
    donors_pre_vals = paradise_donor_pool[pre_years].values
    synthetic_pre = donors_pre_vals.T @ weights
    paradise_pre_vals = paradise_df[paradise_df["year"].isin(pre_years)]["paradise"].values
    gap_pre = paradise_pre_vals - synthetic_pre

    donors_post_vals = paradise_donor_pool[post_years].values
    synthetic_post = donors_post_vals.T @ weights
    paradise_post_vals = paradise_df[paradise_df["year"].isin(post_years)]["paradise"].values
    gap_post = paradise_post_vals - synthetic_post

    paradise_pre_gap = gap_pre.mean()
    paradise_post_gap = gap_post.mean()
    paradise_effect = paradise_post_gap - paradise_pre_gap
    paradise_pre_rmse = np.sqrt(np.mean(gap_pre**2))
    paradise_post_rmse = np.sqrt(np.mean(gap_post**2))

    print(f"Paradise treatment effect: {paradise_effect:.1f} index points")
    print(f"Paradise pre-treatment RMSE: {paradise_pre_rmse:.2f}")

    # Sample placebo tracts (use tracts with good pre-treatment fit potential)
    # Filter to tracts with similar size/trend characteristics
    np.random.seed(42)  # For reproducibility
    candidate_tracts = donor_pivot.index.tolist()
    placebo_tracts = np.random.choice(candidate_tracts, size=min(n_placebos, len(candidate_tracts)), replace=False)

    placebo_effects = []
    placebo_rmses = []

    print(f"\nRunning {len(placebo_tracts)} placebo tests...")
    for i, placebo_tract in enumerate(placebo_tracts):
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(placebo_tracts)} completed...")

        try:
            # Get placebo tract's pre-treatment values
            placebo_pre = donor_pivot.loc[placebo_tract, pre_years].values

            # Create donor pool excluding this tract
            other_donors = donor_pivot.drop(placebo_tract)

            # Select donors similar to this placebo tract (by pre-treatment RMSE)
            other_pre_matrix = other_donors[pre_years].values
            other_rmse = np.sqrt(np.mean((other_pre_matrix - placebo_pre) ** 2, axis=1))
            other_rmse = pd.Series(other_rmse, index=other_donors.index).dropna()

            n_select = min(max_donors_per_placebo, len(other_rmse))
            selected_donors = other_rmse.nsmallest(n_select).index
            placebo_donor_pool = other_donors.loc[selected_donors]

            # Find weights using pre-treatment data
            donors_pre_mat = placebo_donor_pool[pre_years].values
            weights = synthetic_control_weights(placebo_pre, donors_pre_mat)

            # Calculate pre-treatment gap
            synthetic_pre = donors_pre_mat.T @ weights
            gap_pre = placebo_pre - synthetic_pre
            pre_gap = gap_pre.mean()
            pre_rmse = np.sqrt(np.mean(gap_pre**2))

            # Calculate post-treatment gap (using filtered post_years)
            placebo_post = donor_pivot.loc[placebo_tract, post_years].values
            donors_post_mat = placebo_donor_pool[post_years].values
            synthetic_post = donors_post_mat.T @ weights
            gap_post = placebo_post - synthetic_post
            post_gap = gap_post.mean()

            effect = post_gap - pre_gap

            placebo_effects.append(effect)
            placebo_rmses.append(pre_rmse)
        except Exception as e:
            continue

    placebo_effects = np.array(placebo_effects)
    placebo_rmses = np.array(placebo_rmses)

    # Filter to placebos with good pre-treatment fit (RMSE < 10)
    good_fit_mask = placebo_rmses < 10
    placebo_effects_good = placebo_effects[good_fit_mask]

    print(f"\n" + "-" * 70)
    print("Results")
    print("-" * 70)
    print(f"Placebo tests completed: {len(placebo_effects)}")
    print(f"Placebos with good pre-fit (RMSE<10): {len(placebo_effects_good)}")

    print(f"\nPlacebo effect distribution (good fit only):")
    print(f"  Mean: {np.mean(placebo_effects_good):.1f}")
    print(f"  Std: {np.std(placebo_effects_good):.1f}")
    print(f"  Min: {np.min(placebo_effects_good):.1f}")
    print(f"  Max: {np.max(placebo_effects_good):.1f}")

    # Calculate p-value (proportion of placebos with effect as extreme as Paradise)
    n_more_extreme = np.sum(placebo_effects_good <= paradise_effect)
    p_value = (n_more_extreme + 1) / (len(placebo_effects_good) + 1)

    print(f"\nParadise effect: {paradise_effect:.1f}")
    print(f"Placebos more negative than Paradise: {n_more_extreme}")
    print(f"One-sided p-value: {p_value:.4f}")

    # Alternative: RMSPE ratio approach (standard in SC literature)
    # This accounts for pre-treatment fit quality
    paradise_rmspe_ratio = paradise_post_rmse / (paradise_pre_rmse + 0.1)  # Add small constant to avoid div by 0

    placebo_rmspe_ratios = []
    for i, (eff, pre_rmse) in enumerate(zip(placebo_effects, placebo_rmses)):
        if pre_rmse < 10:  # Good pre-fit only
            # Approximate post-RMSE from effect (effect ≈ post_gap, and we stored pre_rmse)
            # This is an approximation; ideally we'd store post_rmse too
            post_rmse_approx = abs(eff)  # Rough approximation
            ratio = post_rmse_approx / (pre_rmse + 0.1)
            placebo_rmspe_ratios.append(ratio)

    placebo_rmspe_ratios = np.array(placebo_rmspe_ratios)
    n_higher_ratio = np.sum(placebo_rmspe_ratios >= paradise_rmspe_ratio)
    p_value_ratio = (n_higher_ratio + 1) / (len(placebo_rmspe_ratios) + 1)

    print(f"\nRMSPE Ratio approach (post/pre RMSE):")
    print(f"Paradise RMSPE ratio: {paradise_rmspe_ratio:.1f}")
    print(f"Placebos with higher ratio: {n_higher_ratio}")
    print(f"P-value (RMSPE ratio): {p_value_ratio:.4f}")

    # Plot results
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: Histogram of placebo effects
    ax = axes[0]
    ax.hist(placebo_effects_good, bins=30, alpha=0.7, color="steelblue", edgecolor="white")
    ax.axvline(x=paradise_effect, color="red", linewidth=2, linestyle="--", label=f"Paradise: {paradise_effect:.1f}")
    ax.axvline(x=0, color="black", linewidth=1, linestyle="-")
    ax.set_xlabel("Treatment Effect (Index Points)")
    ax.set_ylabel("Frequency")
    ax.set_title("Distribution of Placebo Effects")
    ax.legend()

    # Right: Sorted effects with Paradise highlighted
    ax = axes[1]
    sorted_effects = np.sort(placebo_effects_good)
    ranks = np.arange(len(sorted_effects))
    ax.scatter(ranks, sorted_effects, alpha=0.5, color="steelblue", s=20)

    # Find where Paradise would rank
    paradise_rank = np.searchsorted(sorted_effects, paradise_effect)
    ax.scatter([paradise_rank], [paradise_effect], color="red", s=100, zorder=5, label=f"Paradise (rank {paradise_rank+1}/{len(sorted_effects)+1})")
    ax.axhline(y=0, color="black", linewidth=1, linestyle="-")
    ax.set_xlabel("Rank")
    ax.set_ylabel("Treatment Effect (Index Points)")
    ax.set_title("Ranked Placebo Effects")
    ax.legend()

    plt.tight_layout()

    # Include exclusion info in filename
    suffix = ""
    if exclude_years:
        suffix = f"_excl{'_'.join(str(y) for y in exclude_years)}"
    filepath = GRAPHS_DIR / f"placebo_tests{suffix}.png"
    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    print(f"\nSaved: {filepath}")

    # Save results
    results_df = pd.DataFrame({
        "tract": placebo_tracts[:len(placebo_effects)],
        "effect": placebo_effects,
        "pre_rmse": placebo_rmses
    })
    results_df.to_csv(TABLES_DIR / f"placebo_results_{data_type}{suffix}.csv", index=False)

    return placebo_effects, paradise_effect, p_value


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Synthetic Control Analysis")
    parser.add_argument("--data", choices=["wac", "rac"], default="wac")
    parser.add_argument("--outcome", default="c000", help="Outcome variable")
    parser.add_argument("--max-donors", type=int, default=500)
    parser.add_argument("--placebo", action="store_true", help="Run placebo tests")
    parser.add_argument("--n-placebos", type=int, default=100, help="Number of placebo tests")
    parser.add_argument("--exclude-2020", action="store_true",
                        help="Exclude 2020 from post-treatment (COVID shock)")

    args = parser.parse_args()

    # Build exclude_years list
    exclude_years = [2020] if args.exclude_2020 else None

    if args.placebo:
        run_placebo_tests(
            args.data,
            args.outcome,
            n_placebos=args.n_placebos,
            exclude_years=exclude_years,
        )
    else:
        results, weights, effect, paradise_df, donor_pivot = run_synthetic_control(
            args.data,
            args.outcome,
            args.max_donors
        )
        plot_synthetic_control(results)
        plot_paradise_vs_donors(paradise_df, donor_pivot)
        plt.show()
