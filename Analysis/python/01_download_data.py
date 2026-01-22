"""
01_download_data.py
Downloads LODES data from Census Bureau for California.
Equivalent to Stata 01_download_data.do
"""
import gzip
import shutil
from pathlib import Path
import requests
from config import (
    LODES_BASE_URL,
    DATA_DIR,
    YEARS,
)


def download_and_extract(url: str, output_path: Path) -> bool:
    """Download a gzipped file and extract it."""
    gz_path = output_path.with_suffix(output_path.suffix + ".gz")

    try:
        print(f"  Downloading {url}...")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        # Save compressed file
        with open(gz_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Extract
        with gzip.open(gz_path, "rb") as f_in:
            with open(output_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Remove compressed file
        gz_path.unlink()
        print(f"  Saved to {output_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"  ERROR downloading {url}: {e}")
        return False
    except Exception as e:
        print(f"  ERROR extracting {gz_path}: {e}")
        if gz_path.exists():
            gz_path.unlink()
        return False


def download_lodes_data(years: list = None, job_types: list = None):
    """
    Download LODES OD, RAC, and WAC data for California.

    Parameters:
    -----------
    years : list, optional
        Years to download. Default is all years from config.
    job_types : list, optional
        Job types to download. Default is JT00 (all jobs) and JT01 (primary jobs).
    """
    if years is None:
        years = YEARS
    if job_types is None:
        job_types = [0, 1]  # JT00 and JT01

    # Create subdirectories
    od_dir = DATA_DIR / "lodes_od"
    rac_dir = DATA_DIR / "lodes_rac"
    wac_dir = DATA_DIR / "lodes_wac"

    for d in [od_dir, rac_dir, wac_dir]:
        d.mkdir(parents=True, exist_ok=True)

    total_files = 0
    successful = 0

    for year in years:
        print(f"\n=== Year {year} ===")

        for jt in job_types:
            jt_str = f"JT0{jt}"

            # Origin-Destination (main and aux)
            for od_type in ["main", "aux"]:
                filename = f"ca_od_{od_type}_{jt_str}_{year}.csv"
                url = f"{LODES_BASE_URL}/od/{filename}.gz"
                output = od_dir / filename
                total_files += 1
                if download_and_extract(url, output):
                    successful += 1

            # Residence Area Characteristics
            # S000 = all workers, SA01-03 = age, SE01-03 = earnings, SI01-03 = industry
            for segment in ["S000", "SA01", "SA02", "SA03", "SE01", "SE02", "SE03", "SI01", "SI02", "SI03"]:
                filename = f"ca_rac_{segment}_{jt_str}_{year}.csv"
                url = f"{LODES_BASE_URL}/rac/{filename}.gz"
                output = rac_dir / filename
                total_files += 1
                if download_and_extract(url, output):
                    successful += 1

            # Workplace Area Characteristics
            for segment in ["S000", "SA01", "SA02", "SA03", "SE01", "SE02", "SE03", "SI01", "SI02", "SI03"]:
                filename = f"ca_wac_{segment}_{jt_str}_{year}.csv"
                url = f"{LODES_BASE_URL}/wac/{filename}.gz"
                output = wac_dir / filename
                total_files += 1
                if download_and_extract(url, output):
                    successful += 1

    # Download geography crosswalk
    print("\n=== Geography Crosswalk ===")
    xwalk_url = f"{LODES_BASE_URL}/ca_xwalk.csv.gz"
    xwalk_output = DATA_DIR / "ca_xwalk.csv"
    total_files += 1
    if download_and_extract(xwalk_url, xwalk_output):
        successful += 1

    print(f"\n=== Complete ===")
    print(f"Downloaded {successful}/{total_files} files successfully")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download LODES data for California")
    parser.add_argument("--years", type=int, nargs="+", help="Years to download (default: 2013-2023)")
    parser.add_argument("--start-year", type=int, help="Start year (alternative to --years)")
    parser.add_argument("--end-year", type=int, help="End year (alternative to --years)")

    args = parser.parse_args()

    if args.years:
        years = args.years
    elif args.start_year or args.end_year:
        start = args.start_year or 2013
        end = args.end_year or 2023
        years = list(range(start, end + 1))
    else:
        years = None  # Use default from config

    download_lodes_data(years=years)
