"""
08_spillover_analysis.py
Estimates employment and housing vacancy spillover effects from the
Camp Fire on neighboring Butte County communities (especially Chico).

Tests whether non-Paradise Butte County tracts gained employment post-fire,
whether gains occurred in the same industries where Paradise lost jobs,
and quantifies the potential bias in the main DiD estimates.

Also analyzes USPS vacancy data to track residential and business vacancy
dynamics across zones before and after the fire.
"""
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import zipfile
import tempfile

from config import (
    DATA_DIR,
    GRAPHS_DIR,
    TABLES_DIR,
    PARADISE_TRACTS,
    BUTTE_COUNTY_FIPS,
    YEARS,
    LODES_VARS,
    TOP_INDUSTRIES,
    TOP_INDUSTRY_NAMES,
)
from utils import load_california_tract_data, synthetic_control_weights

# ============================================================================
# Constants
# ============================================================================

# Chico city tracts identified from LODES crosswalk (ca_xwalk.csv, stplcname = "Chico city, CA")
CHICO_TRACTS = [
    "06007000102", "06007000103", "06007000104",
    "06007000201", "06007000202",
    "06007000300",
    "06007000401", "06007000403", "06007000404",
    "06007000501", "06007000502",
    "06007000601", "06007000603", "06007000604",
    "06007000700", "06007000800",
    "06007000901", "06007000903", "06007000904",
    "06007001000", "06007001100", "06007001200",
    "06007001300", "06007001400",
    "06007001602",
]
FIRE_YEAR = 2017  # last clean pre-treatment year
PRE_YEARS = [2013, 2014, 2015, 2016, 2017]
POST_YEARS = [2018, 2019, 2020, 2021, 2022, 2023]

ZONE_NAMES = {
    0: "Paradise",
    1: "Chico",
    2: "Other Butte",
    3: "Rest of CA",
}

# USPS vacancy data location
USPS_DIR = Path("M:/USPS_Vacancy")
USPS_TEMP_DIR = DATA_DIR / "usps_temp"


# ============================================================================
# Part A: Employment Spillovers (LODES WAC)
# ============================================================================


def classify_tracts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign each tract to a geographic zone.

    Zones:
        0 - Paradise (4 tracts in PARADISE_TRACTS)
        1 - Chico-area Butte County (tracts starting with CHICO_TRACTS_PREFIX)
        2 - Other non-Paradise Butte County
        3 - Rest of California
    """
    df = df.copy()

    conditions = [
        df["tract"].isin(PARADISE_TRACTS),
        df["tract"].isin(CHICO_TRACTS),
        df["tract"].str.startswith(BUTTE_COUNTY_FIPS),
    ]
    choices = [0, 1, 2]
    df["zone"] = np.select(conditions, choices, default=3)
    df["zone_name"] = df["zone"].map(ZONE_NAMES)

    return df


def aggregate_by_zone_year(
    df: pd.DataFrame,
    outcome_vars: list = None,
) -> pd.DataFrame:
    """
    Aggregate tract-level data to zone-year totals.

    Parameters
    ----------
    df : pd.DataFrame
        Classified tract-year data from classify_tracts().
    outcome_vars : list, optional
        Variables to aggregate. Defaults to c000 + TOP_INDUSTRIES.
    """
    if outcome_vars is None:
        outcome_vars = ["c000"] + TOP_INDUSTRIES
    # Keep only vars that exist in the data
    outcome_vars = [v for v in outcome_vars if v in df.columns]

    agg = df.groupby(["zone", "zone_name", "year"])[outcome_vars].sum().reset_index()
    return agg


def build_spillover_synthetic_control(
    df: pd.DataFrame,
    target_zone: int = 1,
    outcome_var: str = "c000",
    max_donors: int = 1000,
) -> tuple:
    """
    Build synthetic control for Chico or Other Butte using non-Butte CA donors.

    Aggregates all tracts in the target zone, normalizes to 2017=100,
    then finds optimal weights from zone 3 (Rest of CA) donor tracts.

    Parameters
    ----------
    df : pd.DataFrame
        Full California tract-year data with 'zone' column.
    target_zone : int
        Zone to build synthetic control for (1=Chico, 2=Other Butte).
    outcome_var : str
        LODES variable to match on.
    max_donors : int
        Maximum donor tracts to consider.

    Returns
    -------
    results : pd.DataFrame
        Columns: [year, actual, synthetic, gap, period].
    weights_df : pd.DataFrame
        Donor tract weights.
    treatment_effect : float
        Post-pre difference in gap.
    """
    zone_name = ZONE_NAMES[target_zone]

    # Aggregate target zone tracts
    target_df = (
        df[df["zone"] == target_zone]
        .groupby("year")[outcome_var]
        .sum()
        .reset_index()
    )
    target_df.columns = ["year", "actual"]

    # Normalize to 2017 = 100
    base_val = target_df.loc[target_df["year"] == 2017, "actual"].values[0]
    target_df["actual"] = 100 * target_df["actual"] / base_val

    # Build donor pool from zone 3 (rest of CA)
    donor_df = df[df["zone"] == 3].copy()
    donor_pivot = donor_df.pivot_table(
        index="tract", columns="year", values=outcome_var, aggfunc="sum"
    )
    donor_pivot = donor_pivot.dropna()

    # Filter out very small tracts
    if 2017 in donor_pivot.columns:
        donor_pivot = donor_pivot[donor_pivot[2017] >= 500]

    # Normalize donors to 2017 = 100
    if 2017 in donor_pivot.columns:
        donor_pivot = donor_pivot.div(donor_pivot[2017], axis=0) * 100
        donor_pivot = donor_pivot.replace([np.inf, -np.inf], np.nan).dropna()

    # Select donors by pre-treatment trajectory RMSE
    pre_cols = [y for y in PRE_YEARS if y in donor_pivot.columns]
    target_pre = target_df[target_df["year"].isin(PRE_YEARS)]["actual"].values

    donor_pre_matrix = donor_pivot[pre_cols].values
    donor_rmse = np.sqrt(np.mean((donor_pre_matrix - target_pre) ** 2, axis=1))
    donor_rmse = pd.Series(donor_rmse, index=donor_pivot.index).dropna()

    n_select = min(max_donors, len(donor_rmse))
    best_donors = donor_rmse.nsmallest(n_select).index
    donor_pivot = donor_pivot.loc[best_donors]

    print(f"  {zone_name}: {len(donor_pivot)} donors selected")

    # Optimize weights
    donors_pre = donor_pivot[pre_cols].values
    weights = synthetic_control_weights(target_pre, donors_pre)

    # Compute synthetic for all years
    all_years = sorted(target_df["year"].unique())
    donors_all = donor_pivot[all_years].values
    synthetic_all = donors_all.T @ weights

    results = pd.DataFrame({
        "year": all_years,
        "actual": target_df.set_index("year").loc[all_years, "actual"].values,
        "synthetic": synthetic_all,
    })
    results["gap"] = results["actual"] - results["synthetic"]
    results["period"] = results["year"].apply(
        lambda y: "pre" if y in PRE_YEARS else "post"
    )

    pre_gap = results[results["period"] == "pre"]["gap"].mean()
    post_gap = results[results["period"] == "post"]["gap"].mean()
    treatment_effect = post_gap - pre_gap

    # Save weights
    weights_df = pd.DataFrame({"tract": donor_pivot.index, "weight": weights})
    weights_df = weights_df[weights_df["weight"] > 0.001].sort_values(
        "weight", ascending=False
    )

    return results, weights_df, treatment_effect



def run_event_study(
    df: pd.DataFrame,
    treatment_zone: int = 1,
    control_zone: int = 3,
    outcome_var: str = "c000",
    base_year: int = 2017,
) -> pd.DataFrame:
    """
    Run event study regression for spillover tracts.

    Estimates year-by-year treatment effects for the treatment zone
    relative to the control zone, with base_year omitted.

    Uses cluster-robust standard errors at the tract level.

    Parameters
    ----------
    df : pd.DataFrame
        Tract-year level data with 'zone' column.
    treatment_zone : int
        Zone treated by spillover (1=Chico, 2=Other Butte).
    control_zone : int
        Control zone (3=Rest of CA).
    outcome_var : str
        Outcome variable.
    base_year : int
        Omitted year for event study (2017).

    Returns
    -------
    pd.DataFrame
        Columns: [year, coef, se, ci_lower, ci_upper, pvalue].
    """
    # Filter to treatment and control zones
    es_df = df[df["zone"].isin([treatment_zone, control_zone])].copy()
    es_df["treated"] = (es_df["zone"] == treatment_zone).astype(int)

    # Create interaction terms for each year except base year
    years = sorted(es_df["year"].unique())
    interaction_vars = []
    for y in years:
        if y == base_year:
            continue
        varname = f"treated_{y}"
        es_df[varname] = (es_df["treated"] * (es_df["year"] == y)).astype(int)
        interaction_vars.append(varname)

    # Regression
    formula = f"{outcome_var} ~ treated + C(year) + " + " + ".join(interaction_vars)
    model = smf.ols(formula, data=es_df).fit(
        cov_type="cluster", cov_kwds={"groups": es_df["tract"]}
    )

    # Extract year-by-year coefficients
    rows = []
    for y in years:
        if y == base_year:
            rows.append({
                "year": y, "coef": 0.0, "se": 0.0,
                "ci_lower": 0.0, "ci_upper": 0.0, "pvalue": np.nan,
            })
        else:
            varname = f"treated_{y}"
            coef = model.params.get(varname, np.nan)
            se = model.bse.get(varname, np.nan)
            pval = model.pvalues.get(varname, np.nan)
            rows.append({
                "year": y, "coef": coef, "se": se,
                "ci_lower": coef - 1.96 * se,
                "ci_upper": coef + 1.96 * se,
                "pvalue": pval,
            })

    return pd.DataFrame(rows)


def decompose_by_industry(zone_year_df: pd.DataFrame, industries: list = None) -> pd.DataFrame:
    """
    Compare Paradise job losses with Chico/Butte gains by industry.

    For each industry, calculates pre-to-post change for Paradise,
    Chico, and Other Butte zones, plus the offset ratio
    (Chico gain / |Paradise loss|).
    """
    if industries is None:
        industries = TOP_INDUSTRIES
    industries = [i for i in industries if i in zone_year_df.columns]

    rows = []
    for ind in industries:
        for zone_id, zone_name in [(0, "Paradise"), (1, "Chico"), (2, "Other Butte")]:
            zone_data = zone_year_df[zone_year_df["zone"] == zone_id]
            pre_mean = zone_data[zone_data["year"].isin(PRE_YEARS)][ind].mean()
            post_mean = zone_data[zone_data["year"].isin(POST_YEARS)][ind].mean()
            rows.append({
                "industry": ind,
                "industry_name": TOP_INDUSTRY_NAMES.get(ind, ind),
                "zone": zone_name,
                "pre_mean": pre_mean,
                "post_mean": post_mean,
                "change": post_mean - pre_mean,
            })

    decomp = pd.DataFrame(rows)

    # Pivot to compute offset ratio
    pivot = decomp.pivot(index="industry", columns="zone", values="change")
    if "Paradise" in pivot.columns and "Chico" in pivot.columns:
        pivot["offset_ratio"] = np.where(
            pivot["Paradise"] != 0,
            pivot["Chico"] / np.abs(pivot["Paradise"]),
            np.nan,
        )
        # Merge offset_ratio back
        decomp = decomp.merge(
            pivot[["offset_ratio"]].reset_index(),
            on="industry", how="left",
        )

    return decomp


def quantify_did_bias(df_california: pd.DataFrame) -> pd.DataFrame:
    """
    Re-estimate Paradise DiD using non-Butte California as control,
    then compare to original Butte-control estimates to quantify bias.

    If positive spillovers inflated the Butte control, the Butte-control
    DiD underestimates Paradise's loss. Bias = Butte_DiD - CA_DiD.
    """
    # DiD with California control: Paradise (zone 0) vs Rest of CA (zone 3)
    ca_df = df_california[df_california["zone"].isin([0, 3])].copy()
    ca_df["paradise"] = (ca_df["zone"] == 0).astype(int)
    ca_df["post"] = ca_df["year"].isin(POST_YEARS).astype(int)
    ca_df["did"] = ca_df["post"] * ca_df["paradise"]

    outcomes = {
        "Total Jobs": "c000",
        "Construction": "cns04",
        "Retail Trade": "cns07",
        "Educational Services": "cns15",
        "Health Care": "cns16",
        "Accommodation & Food": "cns18",
        "Public Administration": "cns20",
    }

    ca_results = []
    for name, var in outcomes.items():
        if var not in ca_df.columns:
            continue
        formula = f"{var} ~ did + paradise + C(year)"
        try:
            model = smf.ols(formula, data=ca_df).fit(cov_type="HC1")
            ca_results.append({
                "outcome": name,
                "variable": var,
                "did_ca_control": model.params.get("did", np.nan),
                "se_ca_control": model.bse.get("did", np.nan),
                "pval_ca_control": model.pvalues.get("did", np.nan),
            })
        except Exception as e:
            print(f"  Error for {name}: {e}")

    ca_results_df = pd.DataFrame(ca_results)

    # Load original Butte-control results if available (saved by 03_analysis.py)
    butte_results_path = TABLES_DIR / "did_results_wac.csv"
    if butte_results_path.exists():
        butte_df = pd.read_csv(butte_results_path)
        # Merge
        merged = ca_results_df.merge(
            butte_df[["name", "did_coef", "did_se"]].rename(columns={
                "name": "outcome", "did_coef": "did_butte_control", "did_se": "se_butte_control"
            }),
            on="outcome", how="left",
        )
        merged["bias_estimate"] = merged["did_butte_control"] - merged["did_ca_control"]
    else:
        print("  Original DiD results not found. Running Butte-control DiD...")
        butte_df = df_california[df_california["zone"].isin([0, 1, 2])].copy()
        butte_df["paradise"] = (butte_df["zone"] == 0).astype(int)
        butte_df["post"] = butte_df["year"].isin(POST_YEARS).astype(int)
        butte_df["did"] = butte_df["post"] * butte_df["paradise"]

        butte_results = []
        for name, var in outcomes.items():
            if var not in butte_df.columns:
                continue
            formula = f"{var} ~ did + paradise + C(year)"
            try:
                model = smf.ols(formula, data=butte_df).fit(cov_type="HC1")
                butte_results.append({
                    "outcome": name,
                    "did_butte_control": model.params.get("did", np.nan),
                    "se_butte_control": model.bse.get("did", np.nan),
                })
            except Exception:
                pass

        butte_results_df = pd.DataFrame(butte_results)
        merged = ca_results_df.merge(butte_results_df, on="outcome", how="left")
        merged["bias_estimate"] = merged["did_butte_control"] - merged["did_ca_control"]

    return merged


# ============================================================================
# Part B: Housing Vacancy Spillovers (USPS)
# ============================================================================

def load_usps_vacancy_data(
    filter_state: str = "06",
    comparison_counties: list = None,
) -> pd.DataFrame:
    """
    Load USPS vacancy data from ZIP-archived DBF files.

    Reads all quarterly files from M:/USPS_Vacancy/, extracts the DBF,
    and filters to California tracts plus optional comparison counties.

    Parameters
    ----------
    filter_state : str
        State FIPS to filter to (default "06" for California).
    comparison_counties : list, optional
        Additional county FIPS codes to include. If None, keeps all
        tracts in the filter_state.
    """
    from dbfread import DBF

    USPS_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    all_quarters = []
    zip_files = sorted(USPS_DIR.glob("usps_vac_*_tractsum_2kx.zip"))

    if not zip_files:
        raise FileNotFoundError(f"No USPS vacancy ZIP files found in {USPS_DIR}")

    print(f"  Found {len(zip_files)} quarterly files")

    for zf_path in zip_files:
        # Parse quarter/year from filename: usps_vac_MMYYYY_tractsum_2kx.zip
        parts = zf_path.stem.split("_")
        date_str = parts[2]  # MMYYYY
        month = int(date_str[:2])
        year = int(date_str[2:])
        quarter = (month - 1) // 3 + 1

        print(f"  Loading {year} Q{quarter}...")

        with zipfile.ZipFile(zf_path, "r") as zf:
            # Find the DBF file inside the ZIP
            dbf_names = [n for n in zf.namelist() if n.lower().endswith(".dbf")]
            if not dbf_names:
                print(f"    No DBF file found in {zf_path.name}, skipping")
                continue

            # Extract to temp on M: drive
            temp_dbf = USPS_TEMP_DIR / dbf_names[0]
            zf.extract(dbf_names[0], USPS_TEMP_DIR)

            # Read DBF
            table = DBF(str(temp_dbf), encoding="latin-1")
            records = [record for record in table]
            df = pd.DataFrame(records)

            # Clean up temp file
            temp_dbf.unlink(missing_ok=True)

        if df.empty:
            continue

        # Standardize column names to lowercase
        df.columns = df.columns.str.lower()

        # Ensure geoid is string
        df["geoid"] = df["geoid"].astype(str).str.zfill(11)

        # Filter to state
        if filter_state:
            df = df[df["geoid"].str[:2] == filter_state]

        df["year"] = year
        df["quarter"] = quarter
        df["year_quarter"] = year + (quarter - 1) / 4  # For plotting

        all_quarters.append(df)

    result = pd.concat(all_quarters, ignore_index=True)
    print(f"  Total records: {len(result):,}")

    return result


def compute_vacancy_rates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate vacancy rates from raw address and vacancy counts.

    Adds res_vacancy_rate, bus_vacancy_rate columns.
    """
    df = df.copy()
    df["res_vacancy_rate"] = np.where(
        df["ams_res"] > 0, 100 * df["res_vac"] / df["ams_res"], np.nan
    )
    df["bus_vacancy_rate"] = np.where(
        df["ams_bus"] > 0, 100 * df["bus_vac"] / df["ams_bus"], np.nan
    )
    return df


def classify_vacancy_tracts(df: pd.DataFrame) -> pd.DataFrame:
    """Assign USPS vacancy tracts to geographic zones using geoid."""
    df = df.copy()

    conditions = [
        df["geoid"].isin(PARADISE_TRACTS),
        df["geoid"].isin(CHICO_TRACTS),
        df["geoid"].str.startswith(BUTTE_COUNTY_FIPS),
    ]
    choices = [0, 1, 2]
    df["zone"] = np.select(conditions, choices, default=3)
    df["zone_name"] = df["zone"].map(ZONE_NAMES)

    return df


def aggregate_vacancy_by_zone(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate vacancy data by zone and quarter.

    Sums addresses and vacancies, then computes zone-level rates.
    """
    agg = df.groupby(["zone", "zone_name", "year", "quarter", "year_quarter"]).agg(
        ams_res=("ams_res", "sum"),
        ams_bus=("ams_bus", "sum"),
        res_vac=("res_vac", "sum"),
        bus_vac=("bus_vac", "sum"),
        n_tracts=("geoid", "nunique"),
    ).reset_index()

    agg["res_vacancy_rate"] = np.where(
        agg["ams_res"] > 0, 100 * agg["res_vac"] / agg["ams_res"], np.nan
    )
    agg["bus_vacancy_rate"] = np.where(
        agg["ams_bus"] > 0, 100 * agg["bus_vac"] / agg["ams_bus"], np.nan
    )

    return agg


# ============================================================================
# Part C: Visualizations
# ============================================================================

def plot_zone_trends(
    zone_year_df: pd.DataFrame,
    outcome_var: str = "c000",
    normalize: bool = True,
    save: bool = True,
) -> plt.Figure:
    """Plot employment trends by geographic zone, normalized to 2017=100."""
    fig, ax = plt.subplots(figsize=(10, 6))

    colors = {0: "#D62728", 1: "#1F77B4", 2: "#FF7F0E", 3: "#7F7F7F"}
    markers = {0: "o", 1: "s", 2: "^", 3: ""}

    for zone_id in [0, 1, 2, 3]:
        zone_data = zone_year_df[zone_year_df["zone"] == zone_id].sort_values("year")
        if zone_data.empty:
            continue

        values = zone_data[outcome_var].values.copy()
        if normalize:
            base = zone_data.loc[zone_data["year"] == 2017, outcome_var].values
            if len(base) > 0 and base[0] > 0:
                values = 100 * values / base[0]

        label = ZONE_NAMES[zone_id]
        if zone_id == 3:
            ax.plot(zone_data["year"], values, color=colors[zone_id],
                    linewidth=1.5, alpha=0.5, label=label)
        else:
            ax.plot(zone_data["year"], values, color=colors[zone_id],
                    marker=markers[zone_id], linewidth=2, markersize=6, label=label)

    ax.axvline(x=2018.75, color="red", linestyle="--", alpha=0.7,
               linewidth=2, label="Camp Fire (Nov 2018)")
    if normalize:
        ax.axhline(y=100, color="gray", linestyle=":", alpha=0.5)
        ax.set_ylabel(f"{LODES_VARS.get(outcome_var, outcome_var)} Index (2017=100)", fontsize=12)
    else:
        ax.set_ylabel(LODES_VARS.get(outcome_var, outcome_var), fontsize=12)

    ax.set_xlabel("Year", fontsize=12)
    ax.set_title("Employment Trends by Geographic Zone", fontsize=14)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save:
        filepath = GRAPHS_DIR / f"spillover_zone_trends_{outcome_var}.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"  Saved: {filepath}")

    return fig


def plot_spillover_synthetic_control(
    results: pd.DataFrame,
    zone_name: str = "Chico",
    save: bool = True,
) -> plt.Figure:
    """Plot synthetic control results: actual vs synthetic + gap."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Left: levels
    ax1.plot(results["year"], results["actual"], "o-", linewidth=2.5,
             markersize=8, label=f"{zone_name} (Actual)")
    ax1.plot(results["year"], results["synthetic"], "s--", linewidth=2.5,
             markersize=8, label=f"Synthetic {zone_name}")
    ax1.axvline(x=2018.75, color="red", linestyle="--", alpha=0.7,
                linewidth=2, label="Camp Fire (Nov 2018)")
    ax1.axhline(y=100, color="gray", linestyle=":", alpha=0.5)
    ax1.set_xlabel("Year", fontsize=12)
    ax1.set_ylabel("Employment Index (2017=100)", fontsize=12)
    ax1.set_title(f"{zone_name} vs Synthetic Control", fontsize=13)
    ax1.legend(loc="best")
    ax1.grid(True, alpha=0.3)

    # Right: gap
    colors = ["steelblue" if p == "pre" else "firebrick" for p in results["period"]]
    ax2.bar(results["year"], results["gap"], color=colors, alpha=0.7, edgecolor="white")
    ax2.axvline(x=2018.75, color="red", linestyle="--", alpha=0.7, linewidth=2)
    ax2.axhline(y=0, color="black", linewidth=1)
    ax2.set_xlabel("Year", fontsize=12)
    ax2.set_ylabel("Gap (Actual - Synthetic)", fontsize=12)
    ax2.set_title(f"{zone_name} Treatment Gap", fontsize=13)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if save:
        filepath = GRAPHS_DIR / f"spillover_synthetic_{zone_name.lower().replace(' ', '_')}.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"  Saved: {filepath}")

    return fig


def plot_event_study(
    event_study_df: pd.DataFrame,
    outcome_label: str = "Total Jobs",
    zone_name: str = "Chico",
    save: bool = True,
) -> plt.Figure:
    """Plot event study coefficients with 95% confidence intervals."""
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.errorbar(
        event_study_df["year"], event_study_df["coef"],
        yerr=1.96 * event_study_df["se"],
        fmt="o-", capsize=4, capthick=1.5, linewidth=2,
        markersize=8, color="#1F77B4",
    )
    ax.axvline(x=2018.75, color="red", linestyle="--", alpha=0.7,
               linewidth=2, label="Camp Fire (Nov 2018)")
    ax.axhline(y=0, color="black", linewidth=1)

    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel(f"Treatment Effect ({outcome_label})", fontsize=12)
    ax.set_title(f"Event Study: {zone_name} Spillover Effect on {outcome_label}", fontsize=14)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save:
        filepath = GRAPHS_DIR / "spillover_event_study.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"  Saved: {filepath}")

    return fig


def plot_industry_decomposition(decomp_df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Paired bar chart of Paradise losses vs Chico gains by industry."""
    # Filter to Paradise and Chico only
    plot_df = decomp_df[decomp_df["zone"].isin(["Paradise", "Chico"])].copy()

    industries = plot_df["industry_name"].unique()
    n = len(industries)
    x = np.arange(n)
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))

    paradise_changes = []
    chico_changes = []
    for ind_name in industries:
        p_val = plot_df[(plot_df["industry_name"] == ind_name) & (plot_df["zone"] == "Paradise")]["change"].values
        c_val = plot_df[(plot_df["industry_name"] == ind_name) & (plot_df["zone"] == "Chico")]["change"].values
        paradise_changes.append(p_val[0] if len(p_val) > 0 else 0)
        chico_changes.append(c_val[0] if len(c_val) > 0 else 0)

    ax.barh(x - width / 2, paradise_changes, width, label="Paradise", color="#D62728", alpha=0.8)
    ax.barh(x + width / 2, chico_changes, width, label="Chico", color="#1F77B4", alpha=0.8)

    ax.set_yticks(x)
    ax.set_yticklabels(industries, fontsize=11)
    ax.axvline(x=0, color="black", linewidth=1)
    ax.set_xlabel("Change in Jobs (Pre to Post Fire)", fontsize=12)
    ax.set_title("Industry Decomposition: Paradise Losses vs Chico Gains", fontsize=14)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3, axis="x")
    plt.tight_layout()

    if save:
        filepath = GRAPHS_DIR / "spillover_industry_decomposition.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"  Saved: {filepath}")

    return fig


def plot_net_butte_effect(
    zone_year_df: pd.DataFrame,
    outcome_var: str = "c000",
    save: bool = True,
) -> plt.Figure:
    """Plot net Butte County employment combining all zones."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Stack zones 0, 1, 2
    butte_zones = zone_year_df[zone_year_df["zone"].isin([0, 1, 2])]
    total_butte = butte_zones.groupby("year")[outcome_var].sum().reset_index()

    # Normalize to 2017 = 100
    base = total_butte.loc[total_butte["year"] == 2017, outcome_var].values[0]
    total_butte["index"] = 100 * total_butte[outcome_var] / base

    # Also get Rest of CA for comparison
    ca_data = zone_year_df[zone_year_df["zone"] == 3].sort_values("year")
    ca_base = ca_data.loc[ca_data["year"] == 2017, outcome_var].values[0]
    ca_data = ca_data.copy()
    ca_data["index"] = 100 * ca_data[outcome_var] / ca_base

    ax.plot(total_butte["year"], total_butte["index"], "o-", linewidth=2.5,
            markersize=8, color="#2CA02C", label="Butte County (Total)")
    ax.plot(ca_data["year"], ca_data["index"], "s--", linewidth=2,
            markersize=6, color="#7F7F7F", alpha=0.7, label="Rest of CA")

    # Also show individual zone contributions
    for zone_id, color, ls in [(0, "#D62728", ":"), (1, "#1F77B4", ":"), (2, "#FF7F0E", ":")]:
        zd = zone_year_df[zone_year_df["zone"] == zone_id].sort_values("year")
        if zd.empty:
            continue
        zb = zd.loc[zd["year"] == 2017, outcome_var].values[0]
        if zb > 0:
            ax.plot(zd["year"], 100 * zd[outcome_var] / zb, linestyle=ls,
                    linewidth=1.5, alpha=0.5, color=color, label=ZONE_NAMES[zone_id])

    ax.axvline(x=2018.75, color="red", linestyle="--", alpha=0.7,
               linewidth=2, label="Camp Fire (Nov 2018)")
    ax.axhline(y=100, color="gray", linestyle=":", alpha=0.5)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Employment Index (2017=100)", fontsize=12)
    ax.set_title("Net Butte County Employment Effect", fontsize=14)
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save:
        filepath = GRAPHS_DIR / "spillover_net_butte.png"
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"  Saved: {filepath}")

    return fig


def plot_vacancy_trends(
    vac_agg: pd.DataFrame,
    rate_col: str = "res_vacancy_rate",
    ylabel: str = "Residential Vacancy Rate (%)",
    title: str = "Residential Vacancy Rates by Zone",
    filename: str = "spillover_vacancy_trends.png",
    save: bool = True,
) -> plt.Figure:
    """Plot quarterly vacancy rates by zone."""
    fig, ax = plt.subplots(figsize=(12, 6))

    colors = {0: "#D62728", 1: "#1F77B4", 2: "#FF7F0E"}

    for zone_id in [0, 1, 2]:
        zd = vac_agg[vac_agg["zone"] == zone_id].sort_values("year_quarter")
        if zd.empty:
            continue
        ax.plot(zd["year_quarter"], zd[rate_col], "o-", color=colors[zone_id],
                linewidth=2, markersize=4, label=ZONE_NAMES[zone_id])

    ax.axvline(x=2018.75, color="red", linestyle="--", alpha=0.7,
               linewidth=2, label="Camp Fire (Nov 2018)")
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save:
        filepath = GRAPHS_DIR / filename
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"  Saved: {filepath}")

    return fig


# ============================================================================
# Main Orchestrator
# ============================================================================

def run_spillover_analysis(
    max_donors: int = 500,
    exclude_2020: bool = False,
    employment_only: bool = False,
    vacancy_only: bool = False,
    synth_only: bool = False,
    event_study_only: bool = False,
) -> dict:
    """
    Run full spillover analysis pipeline.

    Steps:
    1. Load California-wide WAC tract data
    2. Classify tracts into zones
    3. Aggregate by zone-year
    4. Build synthetic control for Chico
    5. Run event study regressions
    6. Decompose by industry
    7. Quantify DiD bias
    8. Load and analyze USPS vacancy data
    9. Generate all visualizations
    """
    results = {}

    # ----------------------------------------------------------------
    # Part A: Employment Spillovers
    # ----------------------------------------------------------------
    if not vacancy_only:
        print("=" * 70)
        print("Part A: Employment Spillovers (LODES WAC)")
        print("=" * 70)

        # Step 1: Load data
        print("\n1. Loading California tract-level WAC data...")
        df = load_california_tract_data()
        print(f"   Total tract-years: {len(df):,}")
        print(f"   Unique tracts: {df['tract'].nunique():,}")

        # Step 2: Classify zones
        print("\n2. Classifying tracts into geographic zones...")
        df = classify_tracts(df)
        for zone_id in sorted(ZONE_NAMES.keys()):
            n = df[df["zone"] == zone_id]["tract"].nunique()
            print(f"   Zone {zone_id} ({ZONE_NAMES[zone_id]}): {n} tracts")

        # Filter years if excluding 2020
        if exclude_2020:
            df = df[df["year"] != 2020]
            print("   (Excluded 2020 from analysis)")

        # Step 3: Aggregate
        print("\n3. Aggregating employment by zone and year...")
        zone_agg = aggregate_by_zone_year(df)
        zone_agg.to_csv(TABLES_DIR / "spillover_zone_trends.csv", index=False)
        results["zone_trends"] = zone_agg

        if not event_study_only:
            # Step 4: Synthetic control for Chico and Other Butte
            print("\n4. Building synthetic controls...")
            for target_zone, zone_name in [(1, "Chico"), (2, "Other Butte")]:
                print(f"\n   --- {zone_name} ---")
                synth_results, weights_df, effect = build_spillover_synthetic_control(
                    df, target_zone=target_zone, max_donors=max_donors,
                )
                print(f"   {zone_name} spillover effect: {effect:+.1f} index points")

                pre_rmse = np.sqrt(np.mean(
                    synth_results[synth_results["period"] == "pre"]["gap"] ** 2
                ))
                print(f"   Pre-treatment RMSE: {pre_rmse:.1f}")

                zone_key = zone_name.lower().replace(" ", "_")
                synth_results.to_csv(TABLES_DIR / f"spillover_synth_{zone_key}.csv", index=False)
                weights_df.to_csv(DATA_DIR / f"spillover_synth_weights_{zone_key}.csv", index=False)
                results[f"synth_{zone_key}"] = synth_results

                # Plot
                plot_spillover_synthetic_control(synth_results, zone_name=zone_name)

        if synth_only:
            plt.close("all")
            print("\n" + "=" * 70)
            print("Synthetic control analysis complete.")
            print("=" * 70)
            return results

        # Step 5: Event study
        print("\n5. Running event study regressions...")
        event_df = run_event_study(df, treatment_zone=1, control_zone=3)
        event_df.to_csv(TABLES_DIR / "spillover_event_study.csv", index=False)
        results["event_study"] = event_df

        print("\n   Event Study Coefficients (Chico vs Rest of CA):")
        print(f"   {'Year':<6} {'Coef':>10} {'SE':>10} {'P-value':>10}")
        print("   " + "-" * 40)
        for _, row in event_df.iterrows():
            sig = ""
            if pd.notna(row["pvalue"]):
                if row["pvalue"] < 0.01:
                    sig = "***"
                elif row["pvalue"] < 0.05:
                    sig = "**"
                elif row["pvalue"] < 0.1:
                    sig = "*"
            pval_str = f"{row['pvalue']:.3f}" if pd.notna(row["pvalue"]) else "  base"
            print(f"   {int(row['year']):<6} {row['coef']:>10.1f} {row['se']:>10.1f} {pval_str:>9}{sig}")

        if not event_study_only:
            # Step 6: Industry decomposition
            print("\n6. Decomposing by industry...")
            decomp = decompose_by_industry(zone_agg)
            decomp.to_csv(TABLES_DIR / "spillover_industry_decomposition.csv", index=False)
            results["decomposition"] = decomp

            print("\n   Industry Changes (Pre to Post Fire):")
            for ind in TOP_INDUSTRIES:
                ind_data = decomp[decomp["industry"] == ind]
                p_change = ind_data[ind_data["zone"] == "Paradise"]["change"].values
                c_change = ind_data[ind_data["zone"] == "Chico"]["change"].values
                p_str = f"{p_change[0]:+.0f}" if len(p_change) > 0 else "N/A"
                c_str = f"{c_change[0]:+.0f}" if len(c_change) > 0 else "N/A"
                print(f"   {TOP_INDUSTRY_NAMES.get(ind, ind):<25} Paradise: {p_str:>8}  Chico: {c_str:>8}")

            # Step 7: Bias quantification
            print("\n7. Quantifying DiD bias...")
            bias = quantify_did_bias(df)
            bias.to_csv(TABLES_DIR / "spillover_bias_estimate.csv", index=False)
            results["bias"] = bias

            print("\n   DiD Bias Estimates:")
            print(f"   {'Outcome':<25} {'Butte Ctrl':>12} {'CA Ctrl':>12} {'Bias':>10}")
            print("   " + "-" * 60)
            for _, row in bias.iterrows():
                butte_val = row.get("did_butte_control", np.nan)
                ca_val = row.get("did_ca_control", np.nan)
                bias_val = row.get("bias_estimate", np.nan)
                print(
                    f"   {row['outcome']:<25} {butte_val:>12.1f} {ca_val:>12.1f} {bias_val:>10.1f}"
                )

        # Step 8: Employment visualizations
        print("\n8. Generating employment visualizations...")
        plot_zone_trends(zone_agg)
        plot_event_study(event_df)
        if not event_study_only:
            plot_industry_decomposition(decomp)
            plot_net_butte_effect(zone_agg)

    # ----------------------------------------------------------------
    # Part B: Housing Vacancy Spillovers
    # ----------------------------------------------------------------
    if not employment_only and not synth_only and not event_study_only:
        print("\n" + "=" * 70)
        print("Part B: Housing Vacancy Spillovers (USPS)")
        print("=" * 70)

        print("\n1. Loading USPS vacancy data...")
        try:
            vac_df = load_usps_vacancy_data()

            print("\n2. Classifying tracts and computing vacancy rates...")
            vac_df = classify_vacancy_tracts(vac_df)
            vac_df = compute_vacancy_rates(vac_df)

            # Print zone counts
            butte_vac = vac_df[vac_df["zone"].isin([0, 1, 2])]
            for zone_id in [0, 1, 2]:
                n = butte_vac[butte_vac["zone"] == zone_id]["geoid"].nunique()
                print(f"   Zone {zone_id} ({ZONE_NAMES[zone_id]}): {n} tracts in vacancy data")

            print("\n3. Aggregating by zone and quarter...")
            vac_agg = aggregate_vacancy_by_zone(vac_df)
            vac_agg.to_csv(TABLES_DIR / "spillover_vacancy_trends.csv", index=False)
            results["vacancy_trends"] = vac_agg

            # Print summary
            print("\n   Residential Vacancy Rates (selected quarters):")
            for zone_id in [0, 1, 2]:
                zd = vac_agg[vac_agg["zone"] == zone_id].sort_values("year_quarter")
                if zd.empty:
                    continue
                pre_rate = zd[(zd["year"] == 2018) & (zd["quarter"] == 3)]["res_vacancy_rate"].values
                post_rate = zd[(zd["year"] == 2019) & (zd["quarter"] == 1)]["res_vacancy_rate"].values
                pre_str = f"{pre_rate[0]:.1f}%" if len(pre_rate) > 0 else "N/A"
                post_str = f"{post_rate[0]:.1f}%" if len(post_rate) > 0 else "N/A"
                print(f"   {ZONE_NAMES[zone_id]:<15} Q3 2018: {pre_str:>8}  Q1 2019: {post_str:>8}")

            print("\n4. Generating vacancy visualizations...")
            plot_vacancy_trends(vac_agg)
            plot_vacancy_trends(
                vac_agg,
                rate_col="bus_vacancy_rate",
                ylabel="Business Vacancy Rate (%)",
                title="Business Vacancy Rates by Zone",
                filename="spillover_vacancy_business.png",
            )

        except FileNotFoundError as e:
            print(f"   Warning: {e}")
            print("   Skipping vacancy analysis.")
        except Exception as e:
            print(f"   Error in vacancy analysis: {e}")
            import traceback
            traceback.print_exc()

    # ----------------------------------------------------------------
    # Done
    # ----------------------------------------------------------------
    plt.close("all")

    print("\n" + "=" * 70)
    print("Spillover analysis complete.")
    print(f"Graphs saved to: {GRAPHS_DIR}")
    print(f"Tables saved to: {TABLES_DIR}")
    print(f"Data saved to: {DATA_DIR}")
    print("=" * 70)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Spillover Analysis for Paradise Fire",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python 08_spillover_analysis.py                    Full analysis
  python 08_spillover_analysis.py --exclude-2020     Exclude COVID year
  python 08_spillover_analysis.py --synth-only       Synthetic control only
  python 08_spillover_analysis.py --event-study-only Event study only
  python 08_spillover_analysis.py --vacancy-only     Vacancy analysis only
  python 08_spillover_analysis.py --max-donors 500   Limit donor pool
        """,
    )
    parser.add_argument("--max-donors", type=int, default=500,
                        help="Maximum donor tracts for synthetic control")
    parser.add_argument("--exclude-2020", action="store_true",
                        help="Exclude 2020 from analysis (COVID shock)")
    parser.add_argument("--synth-only", action="store_true",
                        help="Run only synthetic control portion")
    parser.add_argument("--event-study-only", action="store_true",
                        help="Run only event study regressions")
    parser.add_argument("--vacancy-only", action="store_true",
                        help="Run only USPS vacancy analysis")
    parser.add_argument("--employment-only", action="store_true",
                        help="Run only employment analysis (skip vacancy)")

    args = parser.parse_args()

    run_spillover_analysis(
        max_donors=args.max_donors,
        exclude_2020=args.exclude_2020,
        employment_only=args.employment_only,
        vacancy_only=args.vacancy_only,
        synth_only=args.synth_only,
        event_study_only=args.event_study_only,
    )
