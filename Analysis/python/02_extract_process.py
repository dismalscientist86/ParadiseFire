"""
02_extract_process.py
Extracts Butte County data from LODES files and identifies Paradise tracts.
Equivalent to Stata 02_extract_ButteCo.do, 03_residence_area.do, 04_work_area.do
"""
import pandas as pd
from pathlib import Path
from config import (
    DATA_DIR,
    BUTTE_COUNTY_FIPS,
    PARADISE_TRACTS,
    YEARS,
)


def load_crosswalk() -> pd.DataFrame:
    """Load and process the California geography crosswalk."""
    xwalk_path = DATA_DIR / "ca_xwalk.csv"
    if not xwalk_path.exists():
        raise FileNotFoundError(f"Crosswalk not found at {xwalk_path}. Run 01_download_data.py first.")

    xwalk = pd.read_csv(xwalk_path, dtype=str)
    return xwalk


def check_paradise_tracts():
    """
    Check if Paradise census tracts exist in the crosswalk and identify
    any changes between 2010 and 2020 geography.
    """
    print("=== Checking Paradise Census Tracts ===\n")

    xwalk = load_crosswalk()

    # The crosswalk contains tabblk2020 (2020 block) and trct (tract)
    # Extract tract from block code (first 11 characters of 15-char block code)
    xwalk["tract"] = xwalk["tabblk2020"].str[:11]
    xwalk["county"] = xwalk["tabblk2020"].str[:5]

    # Filter to Butte County
    butte = xwalk[xwalk["county"] == BUTTE_COUNTY_FIPS].copy()

    print(f"Total blocks in Butte County: {len(butte)}")
    print(f"Unique tracts in Butte County: {butte['tract'].nunique()}")

    # Check for Paradise tracts
    print(f"\nLooking for Paradise tracts: {PARADISE_TRACTS}")

    found_tracts = butte[butte["tract"].isin(PARADISE_TRACTS)]["tract"].unique()
    print(f"Found Paradise tracts: {list(found_tracts)}")

    if len(found_tracts) == 0:
        print("\nWARNING: No exact matches found. Searching for similar tract codes...")
        paradise_area = butte[butte["tract"].str.startswith("0600700")]["tract"].unique()
        print(f"Tracts in Paradise area (0600700*): {sorted(paradise_area)}")

    # Show place names if available
    if "cbsaname" in xwalk.columns or "ctyname" in xwalk.columns:
        print("\nPlace names in crosswalk:")
        for col in ["stplcname", "ctyname", "cbsaname"]:
            if col in butte.columns:
                print(f"  {col}: {butte[col].unique()[:10]}...")

    return butte


def extract_butte_county_od(years: list = None) -> pd.DataFrame:
    """
    Extract Origin-Destination data for Butte County.
    Keeps records where either home or work location is in Butte County.
    """
    if years is None:
        years = YEARS

    od_dir = DATA_DIR / "lodes_od"
    all_data = []

    for year in years:
        filepath = od_dir / f"ca_od_main_JT00_{year}.csv"
        if not filepath.exists():
            print(f"  Skipping {year} - file not found")
            continue

        print(f"  Processing OD {year}...")
        df = pd.read_csv(filepath, dtype={"w_geocode": str, "h_geocode": str})

        # Ensure geocodes are properly formatted (15 digits with leading zeros)
        df["w_geocode"] = df["w_geocode"].str.zfill(15)
        df["h_geocode"] = df["h_geocode"].str.zfill(15)

        # Extract county codes
        df["w_county"] = df["w_geocode"].str[:5]
        df["h_county"] = df["h_geocode"].str[:5]

        # Keep only Butte County (work OR home in Butte)
        butte_df = df[(df["w_county"] == BUTTE_COUNTY_FIPS) | (df["h_county"] == BUTTE_COUNTY_FIPS)].copy()
        butte_df["year"] = year

        all_data.append(butte_df)
        print(f"    {len(butte_df):,} records")

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def extract_butte_county_rac(years: list = None) -> pd.DataFrame:
    """
    Extract Residence Area Characteristics for Butte County.
    Uses h_geocode (home location).
    """
    if years is None:
        years = YEARS

    rac_dir = DATA_DIR / "lodes_rac"
    all_data = []

    for year in years:
        filepath = rac_dir / f"ca_rac_S000_JT00_{year}.csv"
        if not filepath.exists():
            print(f"  Skipping {year} - file not found")
            continue

        print(f"  Processing RAC {year}...")
        df = pd.read_csv(filepath, dtype={"h_geocode": str})
        df.columns = df.columns.str.lower()  # Normalize column names

        # Ensure geocode is properly formatted
        df["h_geocode"] = df["h_geocode"].str.zfill(15)

        # Extract county and tract
        df["h_county"] = df["h_geocode"].str[:5]
        df["h_tract"] = df["h_geocode"].str[:11]

        # Keep only Butte County
        butte_df = df[df["h_county"] == BUTTE_COUNTY_FIPS].copy()
        butte_df["year"] = year

        all_data.append(butte_df)
        print(f"    {len(butte_df):,} records")

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def extract_butte_county_wac(years: list = None) -> pd.DataFrame:
    """
    Extract Workplace Area Characteristics for Butte County.
    Uses w_geocode (work location).
    """
    if years is None:
        years = YEARS

    wac_dir = DATA_DIR / "lodes_wac"
    all_data = []

    for year in years:
        filepath = wac_dir / f"ca_wac_S000_JT00_{year}.csv"
        if not filepath.exists():
            print(f"  Skipping {year} - file not found")
            continue

        print(f"  Processing WAC {year}...")
        df = pd.read_csv(filepath, dtype={"w_geocode": str})
        df.columns = df.columns.str.lower()  # Normalize column names

        # Ensure geocode is properly formatted
        df["w_geocode"] = df["w_geocode"].str.zfill(15)

        # Extract county and tract
        df["w_county"] = df["w_geocode"].str[:5]
        df["w_tract"] = df["w_geocode"].str[:11]

        # Keep only Butte County
        butte_df = df[df["w_county"] == BUTTE_COUNTY_FIPS].copy()
        butte_df["year"] = year

        all_data.append(butte_df)
        print(f"    {len(butte_df):,} records")

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def add_paradise_indicator(df: pd.DataFrame, geocode_col: str = "h_geocode") -> pd.DataFrame:
    """
    Add a 'paradise' indicator variable based on census tract.

    Parameters:
    -----------
    df : DataFrame
        Data with geocode column
    geocode_col : str
        Name of the geocode column ('h_geocode' for RAC, 'w_geocode' for WAC)
    """
    tract_col = geocode_col.replace("geocode", "tract")

    # Create tract column if not exists
    if tract_col not in df.columns:
        df[tract_col] = df[geocode_col].str[:11]

    # Paradise tracts (11-digit 2020 census codes)
    df["paradise"] = df[tract_col].isin(PARADISE_TRACTS).astype(int)

    return df


def process_and_save_all(years: list = None):
    """Main processing function - extract, process, and save all data."""
    if years is None:
        years = YEARS

    print("=" * 60)
    print("Paradise Fire LODES Data Processing")
    print("=" * 60)

    # Check tract geography first
    print("\n")
    check_paradise_tracts()

    # Process RAC data
    print("\n" + "=" * 60)
    print("Extracting Residence Area Characteristics (RAC)")
    print("=" * 60)
    rac = extract_butte_county_rac(years)
    if not rac.empty:
        rac = add_paradise_indicator(rac, "h_geocode")
        rac_path = DATA_DIR / "rac_butte_all_years.parquet"
        rac.to_parquet(rac_path, index=False)
        print(f"\nSaved RAC data to {rac_path}")
        print(f"  Total records: {len(rac):,}")
        print(f"  Paradise records: {rac['paradise'].sum():,}")
        print(f"  Years: {sorted(rac['year'].unique())}")

    # Process WAC data
    print("\n" + "=" * 60)
    print("Extracting Workplace Area Characteristics (WAC)")
    print("=" * 60)
    wac = extract_butte_county_wac(years)
    if not wac.empty:
        wac = add_paradise_indicator(wac, "w_geocode")
        wac_path = DATA_DIR / "wac_butte_all_years.parquet"
        wac.to_parquet(wac_path, index=False)
        print(f"\nSaved WAC data to {wac_path}")
        print(f"  Total records: {len(wac):,}")
        print(f"  Paradise records: {wac['paradise'].sum():,}")
        print(f"  Years: {sorted(wac['year'].unique())}")

    # Process OD data
    print("\n" + "=" * 60)
    print("Extracting Origin-Destination (OD)")
    print("=" * 60)
    od = extract_butte_county_od(years)
    if not od.empty:
        od_path = DATA_DIR / "od_butte_all_years.parquet"
        od.to_parquet(od_path, index=False)
        print(f"\nSaved OD data to {od_path}")
        print(f"  Total records: {len(od):,}")
        print(f"  Years: {sorted(od['year'].unique())}")

    print("\n" + "=" * 60)
    print("Processing Complete!")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process LODES data for Butte County")
    parser.add_argument("--years", type=int, nargs="+", help="Years to process")
    parser.add_argument("--check-tracts", action="store_true", help="Only check tract geography")

    args = parser.parse_args()

    if args.check_tracts:
        check_paradise_tracts()
    else:
        process_and_save_all(years=args.years)
