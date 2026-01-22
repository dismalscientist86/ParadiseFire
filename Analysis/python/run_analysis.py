#!/usr/bin/env python3
"""
run_analysis.py
Main entry point for the Paradise Fire analysis pipeline.

Usage:
    python run_analysis.py --all              # Run full pipeline
    python run_analysis.py --download         # Download data only
    python run_analysis.py --process          # Process data only
    python run_analysis.py --analyze          # Run analysis only
    python run_analysis.py --visualize        # Generate visualizations only
"""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Paradise Fire Economic Impact Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_analysis.py --all                  Full pipeline (download through visualization)
  python run_analysis.py --download --years 2020 2021 2022 2023   Download specific years
  python run_analysis.py --process              Process downloaded data
  python run_analysis.py --analyze --data wac   Run DiD analysis on WAC data
  python run_analysis.py --visualize            Generate all plots
        """,
    )

    parser.add_argument("--all", action="store_true", help="Run full pipeline")
    parser.add_argument("--download", action="store_true", help="Download LODES data")
    parser.add_argument("--process", action="store_true", help="Process/extract data")
    parser.add_argument("--analyze", action="store_true", help="Run DiD analysis")
    parser.add_argument("--visualize", action="store_true", help="Generate visualizations")
    parser.add_argument("--years", type=int, nargs="+", help="Years to download/process")
    parser.add_argument("--data", choices=["wac", "rac", "both"], default="wac", help="Data type for analysis")

    args = parser.parse_args()

    # Default to --all if no specific step selected
    if not any([args.all, args.download, args.process, args.analyze, args.visualize]):
        args.all = True

    steps_run = []

    # Import modules with numeric prefixes using importlib
    import importlib.util

    def import_module(name, filepath):
        spec = importlib.util.spec_from_file_location(name, filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    script_dir = Path(__file__).parent

    # Download
    if args.all or args.download:
        print("\n" + "=" * 70)
        print("STEP 1: Downloading LODES Data")
        print("=" * 70)
        download = import_module("download", script_dir / "01_download_data.py")
        download.download_lodes_data(years=args.years)
        steps_run.append("download")

    # Process
    if args.all or args.process:
        print("\n" + "=" * 70)
        print("STEP 2: Processing Data")
        print("=" * 70)
        process = import_module("process", script_dir / "02_extract_process.py")
        process.process_and_save_all(years=args.years)
        steps_run.append("process")

    # Analyze
    if args.all or args.analyze:
        print("\n" + "=" * 70)
        print("STEP 3: Running Analysis")
        print("=" * 70)
        analysis = import_module("analysis", script_dir / "03_analysis.py")
        if args.data in ["wac", "both"]:
            analysis.run_full_did_analysis("wac")
        if args.data in ["rac", "both"]:
            analysis.run_full_did_analysis("rac")
        steps_run.append("analyze")

    # Visualize
    if args.all or args.visualize:
        print("\n" + "=" * 70)
        print("STEP 4: Generating Visualizations")
        print("=" * 70)
        viz = import_module("viz", script_dir / "04_visualizations.py")
        if args.data in ["wac", "both"]:
            viz.generate_all_visualizations("wac")
        if args.data in ["rac", "both"]:
            viz.generate_all_visualizations("rac")
        steps_run.append("visualize")

    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"Steps completed: {', '.join(steps_run)}")


if __name__ == "__main__":
    main()
