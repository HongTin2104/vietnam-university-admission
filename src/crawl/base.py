"""Base HTTP session with rate limiting and robots.txt compliance."""

import logging
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


class RateLimitedSession:
    """requests.Session wrapper that enforces per-domain delay and respects robots.txt."""

    def __init__(self, delay: float = 2.0):
        self.delay = delay
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser] = {}
        self._session = requests.Session()
        self._session.headers.update(DEFAULT_HEADERS)

    def _can_fetch(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._robots:
            rp = RobotFileParser()
            rp.set_url(f"{origin}/robots.txt")
            try:
                rp.read()
            except Exception:
                rp.allow_all = True
            self._robots[origin] = rp
        return self._robots[origin].can_fetch(DEFAULT_HEADERS["User-Agent"], url)

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
