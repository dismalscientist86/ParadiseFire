"""
03_analysis.py
Aggregates data and performs difference-in-differences analysis.
Equivalent to Stata 07_difference_in_difference.do
"""
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from pathlib import Path
from config import (
    DATA_DIR,
    GRAPHS_DIR,
    TABLES_DIR,
    LODES_VARS,
    TOP_INDUSTRIES,
    TOP_INDUSTRY_NAMES,
)


def load_processed_data(data_type: str = "wac") -> pd.DataFrame:
    """Load processed parquet data."""
    filename = f"{data_type}_butte_all_years.parquet"
    filepath = DATA_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Data not found at {filepath}. Run 02_extract_process.py first.")
    return pd.read_parquet(filepath)


def aggregate_by_location_year(df: pd.DataFrame, value_cols: list = None) -> pd.DataFrame:
    """
    Aggregate data by Paradise/Not Paradise and year.

    Parameters:
    -----------
    df : DataFrame
        Processed LODES data with 'paradise' and 'year' columns
    value_cols : list, optional
        Columns to sum. If None, sums all numeric columns starting with 'c'.
    """
    if value_cols is None:
        # Get all count variables (start with 'c')
        value_cols = [col for col in df.columns if col.startswith("c") and col not in ["createdate"]]

    # Remove any non-numeric columns from the list
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    value_cols = [col for col in value_cols if col in numeric_cols]

    aggregated = df.groupby(["paradise", "year"])[value_cols].sum().reset_index()

    return aggregated


def calculate_percent_change(df: pd.DataFrame, base_year: int = 2017, value_cols: list = None) -> pd.DataFrame:
    """
    Calculate percent change from base year for each location group.

    Parameters:
    -----------
    df : DataFrame
        Aggregated data by paradise and year
    base_year : int
        Year to use as baseline (default 2017, year before fire)
    value_cols : list
        Columns to calculate percent change for
    """
    if value_cols is None:
        value_cols = [col for col in df.columns if col.startswith("c")]

    result = df.copy()

    for col in value_cols:
        base_col = f"{col}_{base_year}"
        pctchg_col = f"{col}_pctchg"

        # Get base year values for each paradise group
        base_values = df[df["year"] == base_year].set_index("paradise")[col]
        result[base_col] = result["paradise"].map(base_values)

        # Calculate percent change
        result[pctchg_col] = 100 * (result[col] - result[base_col]) / result[base_col]

    return result


def prepare_did_data(df: pd.DataFrame, treatment_year: int = 2018) -> pd.DataFrame:
    """
    Prepare data for difference-in-differences analysis.

    Parameters:
    -----------
    df : DataFrame
        Block-level data with 'paradise', 'year', and outcome variables
    treatment_year : int
        Year of treatment (fire occurred Nov 2018, so post = 2019+)
    """
    result = df.copy()

    # Post-treatment indicator (fire was Nov 2018, effects visible in 2019+)
    result["post"] = (result["year"] > treatment_year).astype(int)

    # Difference-in-differences interaction term
    result["did"] = result["post"] * result["paradise"]

    return result


def create_control_variables(df: pd.DataFrame, geocode_col: str, base_year: int = 2017) -> pd.DataFrame:
    """
    Create control variables based on base year characteristics.

    Parameters:
    -----------
    df : DataFrame
        Block-level data
    geocode_col : str
        Name of geocode column (w_geocode for WAC, h_geocode for RAC)
    base_year : int
        Year to use for baseline characteristics
    """
    result = df.copy()

    # Get base year data
    base_data = df[df["year"] == base_year].copy()

    # Calculate proportions in base year
    if "c000" in base_data.columns:
        # Proportion prime-age workers (30-54)
        if "ca02" in base_data.columns:
            base_data["age_pwork"] = base_data["ca02"] / base_data["c000"]

        # Proportion high school or more
        if all(col in base_data.columns for col in ["cd02", "cd03", "c000"]):
            base_data["ed_hsplus"] = (base_data["cd02"] + base_data["cd03"]) / base_data["c000"]

        # Proportion college educated
        if "cd04" in base_data.columns:
            base_data["ed_college"] = base_data["cd04"] / base_data["c000"]

        # Proportion female
        if "cs02" in base_data.columns:
            base_data["p_female"] = base_data["cs02"] / base_data["c000"]

    # Merge control variables back to main data
    control_cols = ["age_pwork", "ed_hsplus", "ed_college", "p_female"]
    control_cols = [col for col in control_cols if col in base_data.columns]

    if control_cols:
        base_controls = base_data[[geocode_col] + control_cols].drop_duplicates()
        result = result.merge(base_controls, on=geocode_col, how="left")

        # Fill missing with means
        for col in control_cols:
            result[col] = result[col].fillna(result[col].mean())

    return result


def run_did_regression(df: pd.DataFrame, outcome: str, controls: list = None) -> dict:
    """
    Run difference-in-differences regression.

    Parameters:
    -----------
    df : DataFrame
        Prepared data with did, paradise, post, year columns
    outcome : str
        Outcome variable name
    controls : list, optional
        Control variable names

    Returns:
    --------
    dict with regression results
    """
    # Build formula
    formula = f"{outcome} ~ did + paradise + C(year)"
    if controls:
        formula += " + " + " + ".join(controls)

    try:
        model = smf.ols(formula, data=df).fit(cov_type="HC1")  # Robust standard errors

        return {
            "outcome": outcome,
            "did_coef": model.params.get("did", np.nan),
            "did_se": model.bse.get("did", np.nan),
            "did_pvalue": model.pvalues.get("did", np.nan),
            "paradise_coef": model.params.get("paradise", np.nan),
            "r_squared": model.rsquared,
            "n_obs": int(model.nobs),
            "model": model,
        }
    except Exception as e:
        print(f"  Error running regression for {outcome}: {e}")
        return {
            "outcome": outcome,
            "did_coef": np.nan,
            "did_se": np.nan,
            "did_pvalue": np.nan,
            "paradise_coef": np.nan,
            "r_squared": np.nan,
            "n_obs": 0,
            "model": None,
        }


def run_full_did_analysis(data_type: str = "wac"):
    """
    Run complete difference-in-differences analysis.

    Parameters:
    -----------
    data_type : str
        'wac' for workplace, 'rac' for residence
    """
    print("=" * 70)
    print(f"Difference-in-Differences Analysis ({data_type.upper()})")
    print("=" * 70)

    # Load data
    df = load_processed_data(data_type)
    geocode_col = "w_geocode" if data_type == "wac" else "h_geocode"

    print(f"\nLoaded {len(df):,} observations")
    print(f"Years: {sorted(df['year'].unique())}")
    print(f"Paradise observations: {df['paradise'].sum():,}")

    # Prepare DiD data
    df = prepare_did_data(df)

    # Add control variables
    df = create_control_variables(df, geocode_col)

    # Define outcomes to analyze
    outcomes = {
        "Total Jobs": "c000",
        "Construction": "cns04",
        "Retail Trade": "cns07",
        "Educational Services": "cns15",
        "Health Care": "cns16",
        "Accommodation & Food": "cns18",
        "Public Administration": "cns20",
        "Low Earnings": "ce01",
        "Medium Earnings": "ce02",
        "High Earnings": "ce03",
    }

    controls = ["age_pwork", "ed_hsplus", "ed_college", "p_female"]
    controls = [c for c in controls if c in df.columns]

    results = []

    print("\n" + "-" * 70)
    print("Regression Results (DiD coefficient = treatment effect)")
    print("-" * 70)
    print(f"{'Outcome':<25} {'DiD Coef':>12} {'Std Err':>10} {'P-value':>10} {'N':>8}")
    print("-" * 70)

    for name, var in outcomes.items():
        if var not in df.columns:
            continue

        result = run_did_regression(df, var, controls)
        results.append({"name": name, **result})

        sig = ""
        if result["did_pvalue"] < 0.01:
            sig = "***"
        elif result["did_pvalue"] < 0.05:
            sig = "**"
        elif result["did_pvalue"] < 0.1:
            sig = "*"

        print(
            f"{name:<25} {result['did_coef']:>12.2f} {result['did_se']:>10.2f} "
            f"{result['did_pvalue']:>9.3f}{sig} {result['n_obs']:>7,}"
        )

    print("-" * 70)
    print("Significance: *** p<0.01, ** p<0.05, * p<0.1")
    print(f"Controls: {', '.join(controls) if controls else 'None'}")

    # Save results
    results_df = pd.DataFrame(results)
    results_path = TABLES_DIR / f"did_results_{data_type}.csv"
    results_df.drop(columns=["model"], errors="ignore").to_csv(results_path, index=False)
    print(f"\nResults saved to {results_path}")

    return results_df


def generate_summary_statistics(data_type: str = "wac"):
    """Generate summary statistics by Paradise/Not Paradise and pre/post fire."""
    df = load_processed_data(data_type)
    df = prepare_did_data(df)

    # Aggregate by location and period
    agg = aggregate_by_location_year(df)

    # Pre-fire (2013-2018) vs Post-fire (2019+)
    agg["period"] = agg["year"].apply(lambda x: "Pre-Fire (2013-2018)" if x <= 2018 else "Post-Fire (2019+)")

    summary = agg.groupby(["paradise", "period"]).agg(
        {"c000": ["mean", "std"], "year": "count"}
    ).round(2)

    print("\n" + "=" * 70)
    print("Summary Statistics: Total Jobs (c000)")
    print("=" * 70)
    print(summary)

    return agg


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Paradise Fire DiD analysis")
    parser.add_argument("--data", choices=["wac", "rac", "both"], default="wac", help="Data type to analyze")
    parser.add_argument("--summary", action="store_true", help="Generate summary statistics only")

    args = parser.parse_args()

    if args.summary:
        if args.data in ["wac", "both"]:
            generate_summary_statistics("wac")
        if args.data in ["rac", "both"]:
            generate_summary_statistics("rac")
    else:
        if args.data in ["wac", "both"]:
            run_full_did_analysis("wac")
        if args.data in ["rac", "both"]:
            run_full_did_analysis("rac")
