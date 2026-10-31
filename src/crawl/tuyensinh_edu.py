"""Crawler for tuyensinh.edu.vn/diem-chuan/ — per-university HTML tables.

robots.txt: User-agent: * / Disallow: (empty) → all paths allowed.
Table structure: STT | Mã ngành | Tên ngành | Tổ hợp môn | Điểm chuẩn | Ghi chú
"""

import json
import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup

from src.crawl.base import RateLimitedSession

logger = logging.getLogger(__name__)

BASE_URL = "https://tuyensinh.edu.vn"
INDEX_URL = f"{BASE_URL}/diem-chuan/"

# Year pattern in URL slug, e.g. "...-2024/"
YEAR_RE = re.compile(r"-(\d{4})/?$")


def _discover_pages(session: RateLimitedSession) -> list[str]:
    """Return all paginated URLs under /diem-chuan/."""
    resp = session.get(INDEX_URL)
    soup = BeautifulSoup(resp.text, "lxml")

    # Find last page number from pagination
    page_links = soup.select("a.page-numbers")
    max_page = 1
    for a in page_links:
        m = re.search(r"/page/(\d+)/", a.get("href", ""))
        if m:
            max_page = max(max_page, int(m.group(1)))

    pages = [INDEX_URL]
    for p in range(2, max_page + 1):
        pages.append(f"{INDEX_URL}page/{p}/")
    logger.info("Index has %d pages", len(pages))
    return pages


def _collect_uni_urls(session: RateLimitedSession, years: list[int]) -> list[tuple[str, int]]:
    """Return (url, year) pairs matching requested years."""
    results: list[tuple[str, int]] = []
    pages = _discover_pages(session)
    for page_url in pages:
        try:
            resp = session.get(page_url)
        except Exception as e:
            logger.warning("Skipping page %s: %s", page_url, e)
            continue
        soup = BeautifulSoup(resp.text, "lxml")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = YEAR_RE.search(href)
            if m and int(m.group(1)) in years and "/diem-chuan/" in href:
                results.append((href, int(m.group(1))))
    # Deduplicate
    seen: set[str] = set()
    unique = []
    for url, year in results:
        if url not in seen:
            seen.add(url)
            unique.append((url, year))
    logger.info("Found %d university pages for years %s", len(unique), years)
    return unique


def _parse_table(table, year: int, university_name: str, university_code: str) -> list[dict]:
    """Parse one <table> into records. Handles multi-combo cells like 'A00; A01'."""
    records = []
    rows = table.find_all("tr")
    if not rows:
        return records

    # Detect column indices from header
    header = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
    col = {
        "major_code": next((i for i, h in enumerate(header) if "mã" in h), 1),
        "major_name": next((i for i, h in enumerate(header) if "tên" in h and "ngành" in h), 2),
        "score_combo": next((i for i, h in enumerate(header) if "tổ hợp" in h or "to hop" in h), 3),
        "cutoff_score": next((i for i, h in enumerate(header) if "điểm" in h or "diem" in h), 4),
        "notes": next((i for i, h in enumerate(header) if "ghi chú" in h or "ghi chu" in h), 5),
    }

    for row in rows[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        if len(cells) < 4:
            continue

        def _get(idx: int) -> str:
            return cells[idx] if idx < len(cells) else ""

        raw_score = _get(col["cutoff_score"])
        score_m = re.search(r"\d+(\.\d+)?", raw_score.replace(",", "."))
        if not score_m:
            continue
        cutoff = float(score_m.group())

        # Split multi-combo cells: "A00; A01" → ["A00", "A01"]
        raw_combo = _get(col["score_combo"])
        combos = [c.strip() for c in re.split(r"[;,/]+", raw_combo) if c.strip()]
        if not combos:
            combos = [raw_combo.strip()]

        for combo in combos:
            combo_m = re.search(r"[A-Da-d]\d{2}", combo)
            if not combo_m:
                continue
            records.append(
                {
                    "year": year,
                    "university_code": university_code,
                    "university_name": university_name,
                    "major_code": _get(col["major_code"]),
                    "major_name": _get(col["major_name"]),
                    "score_combo": combo_m.group().upper(),
                    "cutoff_score": cutoff,
                    "region_priority": 0,
                    "quota": None,
                    "notes": _get(col["notes"]),
                }
            )
    return records


def _extract_meta(soup: BeautifulSoup, url: str) -> tuple[str, str]:
    """Return (university_code, university_name) from page."""
    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else ""
    # Remove "Điểm chuẩn " prefix and year suffix
    name = re.sub(r"^[Ðđ]iểm chuẩn\s*", "", title, flags=re.IGNORECASE)
    name = re.sub(r"\s*\d{4}\s*$", "", name).strip()
    # Try to extract code from parenthetical
    m = re.search(r"\(([A-Z0-9]{2,10})\)", name)
    code = m.group(1) if m else ""
    name = re.sub(r"\s*\([A-Z0-9]{2,10}\)\s*", "", name).strip()
    return code, name


def crawl_all(years: list[int], raw_dir: Path, delay: float = 2.0) -> list[dict]:
    """Crawl tuyensinh.edu.vn for all given years. Save raw HTML + combined JSON."""
    session = RateLimitedSession(delay=delay)
    raw_dir.mkdir(parents=True, exist_ok=True)

    uni_pages = _collect_uni_urls(session, years)
    all_records: list[dict] = []

    for url, year in uni_pages:
        if not url.startswith("http"):
            url = BASE_URL + url
        try:
            resp = session.get(url)
        except Exception as e:
            logger.warning("Skipping %s: %s", url, e)
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        uni_code, uni_name = _extract_meta(soup, url)

        # Save raw HTML
        safe = re.sub(r"[^\w-]", "_", url.replace(BASE_URL, "").strip("/"))[:80]
        (raw_dir / f"{year}_{safe}.html").write_text(resp.text, encoding="utf-8")

        for table in soup.find_all("table"):
            records = _parse_table(table, year, uni_name, uni_code)
            all_records.extend(records)
            if records:
                logger.info("  %s %d: %d rows", uni_name[:40], year, len(records))

    out = raw_dir / "all_records_raw.json"
    out.write_text(json.dumps(all_records, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Total: %d records from %d pages", len(all_records), len(uni_pages))
    return all_records
