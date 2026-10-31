"""Entry point: python -m src.crawl.run_crawl [--years 2020 2021 ...]"""

import argparse
import logging
from pathlib import Path

from src.crawl.tuyensinh247 import crawl_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl university admission scores")
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=list(range(2020, 2027)),
        help="Years to crawl (default: 2020-2026)",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory for raw HTML output",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Seconds between requests to the same domain (default: 2.0)",
    )
    args = parser.parse_args()

    records = crawl_all(args.years, args.raw_dir, delay=args.delay)
    print(f"Crawled {len(records)} records for years {args.years}")


if __name__ == "__main__":
    main()
