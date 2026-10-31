"""Base HTTP session with rate limiting and robots.txt compliance."""

import logging
import re
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "vietnam-university-admission/0.1 "
        "(https://github.com/HongTin2104/vietnam-university-admission; "
        "educational data collection)"
    ),
    "Accept-Language": "vi,en;q=0.9",
}

# Python's RobotFileParser has a bug: "Disallow:" (empty value) is incorrectly
# parsed as "Disallow: " which matches every path. Per the robots.txt spec
# (RFC 9309 §2.2.3), an empty Disallow means "allow all". We work around this
# by fetching the raw file and checking for actual non-empty Disallow rules.
_DISALLOW_RE = re.compile(r"^Disallow:\s*(\S+)", re.IGNORECASE | re.MULTILINE)


def _has_real_disallow(robots_text: str) -> bool:
    """Return True only if the robots.txt contains a non-empty Disallow rule."""
    return bool(_DISALLOW_RE.search(robots_text))


class RateLimitedSession:
    """requests.Session wrapper that enforces per-domain delay and respects robots.txt."""

    def __init__(self, delay: float = 2.0):
        self.delay = delay
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser] = {}
        self._robots_raw: dict[str, str] = {}
        self._session = requests.Session()
        self._session.headers.update(DEFAULT_HEADERS)

    def _can_fetch(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._robots:
            rp = RobotFileParser()
            rp.set_url(f"{origin}/robots.txt")
            raw = ""
            try:
                resp = self._session.get(f"{origin}/robots.txt", timeout=10)
                raw = resp.text if resp.ok else ""
                rp.parse(raw.splitlines())
            except Exception:
                rp.allow_all = True
            self._robots[origin] = rp
            self._robots_raw[origin] = raw

        # Workaround: if Python says False but robots.txt has no real Disallow,
        # the site is allowing all crawlers.
        if not self._robots[origin].can_fetch(DEFAULT_HEADERS["User-Agent"], url):
            raw = self._robots_raw.get(origin, "")
            if raw and not _has_real_disallow(raw):
                logger.debug(
                    "robots.txt parser false-negative for %s; allowing (no real Disallow)", url
                )
                return True
            return False
        return True

    def get(self, url: str, **kwargs) -> requests.Response:
        if not self._can_fetch(url):
            raise PermissionError(f"robots.txt disallows: {url}")

        domain = urlparse(url).netloc
        elapsed = time.monotonic() - self._last_request.get(domain, 0)
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

        logger.debug("GET %s", url)
        resp = self._session.get(url, timeout=30, **kwargs)
        resp.raise_for_status()
        self._last_request[domain] = time.monotonic()
        return resp
