"""
utils.py
Shared utility functions for Paradise Fire analysis.

Functions here were previously duplicated across 05_synthetic_control.py
and 08_spillover_analysis.py.
"""
import pandas as pd
import numpy as np
from scipy.optimize import minimize

from config import DATA_DIR


def load_california_tract_data(data_type: str = "wac") -> pd.DataFrame:
    """
    Load and aggregate California LODES data to tract-year level.

    Processes raw CSV files to get all California tracts, not just
    Butte County.

    Parameters
    ----------
    data_type : str
        "wac" (workplace area characteristics) or "rac" (residence area
        characteristics).

    Returns
    -------
    pd.DataFrame
        Columns: [tract, year, c000, ca01, ...]
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

        df[geocode_col] = df[geocode_col].str.zfill(15)

        tract_col = geocode_col.replace("geocode", "tract")
        df[tract_col] = df[geocode_col].str[:11]

        count_cols = [c for c in df.columns if c.startswith("c") and c != "createdate"]
        tract_agg = df.groupby(tract_col)[count_cols].sum().reset_index()
        tract_agg["year"] = year

        all_data.append(tract_agg)

    result = pd.concat(all_data, ignore_index=True)

    if "w_tract" in result.columns:
        result = result.rename(columns={"w_tract": "tract"})
    elif "h_tract" in result.columns:
        result = result.rename(columns={"h_tract": "tract"})

    return result


def synthetic_control_weights(
    treated_pre: np.ndarray,
    donors_pre: np.ndarray,
) -> np.ndarray:
    """
    Find optimal weights for synthetic control.

    Minimizes MSE between the treated unit and a weighted combination of
    donors in the pre-treatment period, subject to weights summing to 1
    and being non-negative (Abadie et al. 2010).

    Parameters
    ----------
    treated_pre : array (T_pre,)
        Treated unit outcomes in pre-period.
    donors_pre : array (N_donors, T_pre)
        Donor outcomes in pre-period.

    Returns
    -------
    weights : array (N_donors,)
        Optimal weights (sum to 1, non-negative).
    """
    n_donors = donors_pre.shape[0]

    def objective(w):
        synthetic = donors_pre.T @ w
        return np.mean((treated_pre - synthetic) ** 2)

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds = [(0, 1) for _ in range(n_donors)]
    w0 = np.ones(n_donors) / n_donors

    result = minimize(
        objective,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-10},
    )

    return result.x
