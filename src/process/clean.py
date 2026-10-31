"""Clean and normalize raw crawled records into a single CSV."""

import json
import logging
import re
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Official score combinations used in Vietnam's national exam
VALID_COMBOS = {
    "A00",
    "A01",
    "A02",
    "A08",
    "A09",
    "A10",
    "B00",
    "B01",
    "B02",
    "B03",
    "B04",
    "B08",
    "C00",
    "C01",
    "C02",
    "C03",
    "C04",
    "D01",
    "D07",
    "D08",
    "D09",
    "D10",
    "D14",
    "D15",
    "D96",
}

# Score range for national exam: 0–30 (3 subjects × 10)
SCORE_MIN = 0.0
SCORE_MAX = 30.0


def _normalize_combo(raw: str) -> str:
    """Extract a valid score combination from a raw cell value."""
    raw = raw.upper().strip()
    m = re.search(r"[A-D]\d{2}", raw)
    if m and m.group() in VALID_COMBOS:
        return m.group()
    # Accept any A/B/C/D + 2 digits even if not in known list
    if m:
        return m.group()
    return raw


def _normalize_name(text: str) -> str:
    """Strip extra whitespace; keep Vietnamese diacritics intact."""
    return re.sub(r"\s+", " ", text).strip()


def _normalize_major_code(raw: str) -> str:
    """Ministry major codes are 7 digits, e.g. 7480201."""
    m = re.search(r"\d{7}", raw)
    return m.group() if m else raw.strip()


def load_raw(raw_dir: Path) -> list[dict]:
    path = raw_dir / "all_records_raw.json"
    if not path.exists():
        raise FileNotFoundError(f"Raw data not found: {path}. Run the crawler first.")
    return json.loads(path.read_text(encoding="utf-8"))


def clean(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records)

    # Normalise text columns
    for col in ("university_name", "major_name"):
        if col in df.columns:
            df[col] = df[col].fillna("").apply(_normalize_name)

    if "major_code" in df.columns:
        df["major_code"] = df["major_code"].fillna("").apply(_normalize_major_code)

    if "score_combo" in df.columns:
        df["score_combo"] = df["score_combo"].fillna("").apply(_normalize_combo)

    # Drop rows where score is out of range
    if "cutoff_score" in df.columns:
        df["cutoff_score"] = pd.to_numeric(df["cutoff_score"], errors="coerce")
        before = len(df)
        df = df[df["cutoff_score"].between(SCORE_MIN, SCORE_MAX)]
        dropped = before - len(df)
        if dropped:
            logger.warning("Dropped %d rows with invalid cutoff_score", dropped)

    # Drop rows missing key fields
    required = ["year", "university_name", "major_name", "score_combo", "cutoff_score"]
    for col in required:
        if col in df.columns:
            df = df[df[col].notna() & (df[col].astype(str).str.strip() != "")]

    # Deduplicate: keep highest score if same (year, uni, major, combo, region)
    key_cols = ["year", "university_code", "major_code", "score_combo", "region_priority"]
    key_cols = [c for c in key_cols if c in df.columns]
    df = df.sort_values("cutoff_score", ascending=False).drop_duplicates(
        subset=key_cols, keep="first"
    )

    df = df.sort_values(["year", "university_name", "major_name"]).reset_index(drop=True)
    logger.info(
        "Cleaned dataset: %d records, %d universities, years %s",
        len(df),
        df["university_name"].nunique() if "university_name" in df.columns else 0,
        sorted(df["year"].unique().tolist()) if "year" in df.columns else [],
    )
    return df


def run(raw_dir: Path, processed_dir: Path) -> pd.DataFrame:
    records = load_raw(raw_dir)
    df = clean(records)
    processed_dir.mkdir(parents=True, exist_ok=True)
    out = processed_dir / "scores.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig", lineterminator="\n")
    logger.info("Saved processed data to %s", out)
    return df
