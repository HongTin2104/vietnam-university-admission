"""Entry point: python -m src.process.run_process"""

import argparse
import logging
from pathlib import Path

from src.process.clean import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean raw crawled data into processed CSV")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()

    df = run(args.raw_dir, args.processed_dir)
    print(f"Processed {len(df)} records → {args.processed_dir / 'scores.csv'}")


if __name__ == "__main__":
    main()
