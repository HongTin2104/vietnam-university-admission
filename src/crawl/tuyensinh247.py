"""Crawler for tuyensinh247.com — aggregated cutoff scores by year.

Page pattern: https://tuyensinh247.com/diem-chuan-<year>-c<id>.html
The site lists điểm chuẩn for each university per year in HTML tables.
"""

import json
import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup

from src.crawl.base import RateLimitedSession

logger = logging.getLogger(__name__)

BASE_URL = "https://tuyensinh247.com"

# University index pages per year (confirmed available as of 2026-10)
YEAR_INDEX_URLS: dict[int, str] = {
    2020: f"{BASE_URL}/diem-chuan-2020-c12568.html",
    2021: f"{BASE_URL}/diem-chuan-2021-c13512.html",
    2022: f"{BASE_URL}/diem-chuan-2022-c14025.html",
    2023: f"{BASE_URL}/diem-chuan-2023-c14800.html",
    2024: f"{BASE_URL}/diem-chuan-2024-c15200.html",
    2025: f"{BASE_URL}/diem-chuan-2025-c15800.html",
    2026: f"{BASE_URL}/diem-chuan-2026-c16200.html",
}


def _parse_score_table(table, year: int, university_name: str, university_code: str) -> list[dict]:
    """Parse one <table> element into a list of score records."""
    records = []
    rows = table.find_all("tr")
    if not rows:
        return records

    for row in rows[1:]:  # skip header row
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        if len(cells) < 3:
            continue
        # Typical columns: major_code | major_name | score_combo | cutoff_score | notes
        # Column order varies; we try to detect by content
        record = {
            "year": year,
            "university_code": university_code,
            "university_name": university_name,
            "major_code": cells[0] if cells else "",
            "major_name": cells[1] if len(cells) > 1 else "",
            "score_combo": cells[2] if len(cells) > 2 else "",
            "cutoff_score": _parse_score(cells[3]) if len(cells) > 3 else None,
            "region_priority": 0,
            "quota": _parse_int(cells[4]) if len(cells) > 4 else None,
            "notes": cells[5] if len(cells) > 5 else "",
        }
        if record["cutoff_score"] is not None:
            records.append(record)
    return records


def _parse_score(text: str) -> float | None:
    text = text.replace(",", ".").strip()
    m = re.search(r"\d+(\.\d+)?", text)
    return float(m.group()) if m else None


def _parse_int(text: str) -> int | None:
    m = re.search(r"\d+", text.replace(".", "").replace(",", ""))
    return int(m.group()) if m else None


def _extract_university_meta(soup: BeautifulSoup) -> tuple[str, str]:
    """Return (university_code, university_name) from a university detail page."""
    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else ""
    # Try to extract code from patterns like "Trường ĐH ABC (QHD)"
    m = re.search(r"\(([A-Z0-9]{2,8})\)", title)
    code = m.group(1) if m else ""
    # Clean name: remove parenthetical code
    name = re.sub(r"\s*\([A-Z0-9]{2,8}\)\s*", "", title).strip()
    return code, name


def crawl_year(year: int, session: RateLimitedSession, raw_dir: Path) -> list[dict]:
    """Crawl all university cutoff scores for one year. Save raw HTML to raw_dir."""
    index_url = YEAR_INDEX_URLS.get(year)
    if not index_url:
        logger.warning("No index URL for year %d", year)
        return []

    logger.info("Fetching index for %d: %s", year, index_url)
    try:
        resp = session.get(index_url)
    except PermissionError as e:
        logger.error("robots.txt blocked: %s", e)
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    # Save raw index HTML
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"index_{year}.html").write_text(resp.text, encoding="utf-8")

    # Find links to individual university pages
    links = soup.select("a[href*='diem-chuan']")
    uni_urls = list({a["href"] for a in links if str(year) in a.get("href", "")})
    logger.info("Found %d university links for %d", len(uni_urls), year)

    all_records: list[dict] = []
    for url in uni_urls:
        if not url.startswith("http"):
            url = BASE_URL + url
        try:
            uni_resp = session.get(url)
        except (PermissionError, Exception) as e:
            logger.warning("Skipping %s: %s", url, e)
            continue

        uni_soup = BeautifulSoup(uni_resp.text, "lxml")
        uni_code, uni_name = _extract_university_meta(uni_soup)

        # Save raw
        safe_name = re.sub(r"[^\w-]", "_", url.split("/")[-1])
        (raw_dir / f"{year}_{safe_name}.html").write_text(uni_resp.text, encoding="utf-8")

        for table in uni_soup.find_all("table"):
            records = _parse_score_table(table, year, uni_name, uni_code)
            all_records.extend(records)

    return all_records


def crawl_all(years: list[int], raw_dir: Path, delay: float = 2.0) -> list[dict]:
    """Crawl all given years and return combined records."""
    session = RateLimitedSession(delay=delay)
    all_records: list[dict] = []
    for year in years:
        records = crawl_year(year, session, raw_dir)
        logger.info("Year %d: %d records", year, len(records))
        all_records.extend(records)

    # Save combined raw JSON for reproducibility
    raw_dir.mkdir(parents=True, exist_ok=True)
    out = raw_dir / "all_records_raw.json"
    out.write_text(json.dumps(all_records, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Saved %d total records to %s", len(all_records), out)
    return all_records
