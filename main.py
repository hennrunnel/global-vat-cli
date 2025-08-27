import argparse
import os
import sys
from datetime import datetime, timezone

from global_vat_cli.aggregator import assemble_records
from global_vat_cli.fetchers.ca import CanadaFetcher
from global_vat_cli.fetchers.ch import SwitzerlandFetcher
from global_vat_cli.fetchers.eu import EUFetcher
from global_vat_cli.fetchers.no import NorwayFetcher
from global_vat_cli.fetchers.uk import UKFetcher
from global_vat_cli.monitor import run_monitor
from global_vat_cli.output import write_json, write_readme, summarize_to_console


def run_pipeline(dry_run: bool = False) -> int:
    timestamp = datetime.now(timezone.utc).isoformat()
    if dry_run:
        os.environ["VATCLI_DRY_RUN"] = "1"
    else:
        os.environ.pop("VATCLI_DRY_RUN", None)

    fetchers = [
        EUFetcher(),
        UKFetcher(),
        CanadaFetcher(),
        SwitzerlandFetcher(),
        NorwayFetcher(),
    ]

    all_raw_records = []
    for fetcher in fetchers:
        try:
            print(f"Fetching from: {fetcher.name} -> {fetcher.source_url}")
            raw = fetcher.fetch()
            print(f"Fetched {len(raw)} records from {fetcher.name}")
            all_raw_records.extend(raw)
        except Exception as exc:
            print(f"WARN: {fetcher.name} failed with error: {exc}")

    final_records = assemble_records(all_raw_records, timestamp)

    if dry_run:
        summarize_to_console(final_records)
    else:
        write_json(final_records, out_path="vat_dataset.json")
        write_readme(final_records, out_path="README.md")

    return 0


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Global VAT/GST dataset CLI")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run parsers and show a summary without writing files",
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Run only the secondary source monitoring module",
    )
    parser.add_argument(
        "--allow-fallbacks",
        action="store_true",
        help="Allow authoritative static fallbacks (e.g., CA GST/HST) if live pages are blocked",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.monitor:
        run_monitor()
        return 0
    if args.allow_fallbacks:
        os.environ["VATCLI_ALLOW_FALLBACKS"] = "1"
    else:
        os.environ.pop("VATCLI_ALLOW_FALLBACKS", None)
    return run_pipeline(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())


