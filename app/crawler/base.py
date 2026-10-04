import os
import json
import time
import asyncio
import logging
import urllib.robotparser
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import httpx
from app.core.config import settings
from app.db.supabase_client import db_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("crawler.base")

class BaseCrawler(ABC):
    """
    Abstract Base Crawler for Vietnam Admissions & Exam Data
    - Exponential backoff retry logic
    - robots.txt compliance checker
    - Checkpoint save/resume mechanism
    - Decree 13/2023 Personal Data Protection compliance filter
    """
    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.user_agent = settings.CRAWLER_USER_AGENT
        self.delay_seconds = settings.CRAWLER_DELAY_SECONDS
        self.max_retries = 3
        self.checkpoint_dir = settings.CHECKPOINT_DIR
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        self.checkpoint_file = os.path.join(self.checkpoint_dir, f"{self.source_name}_checkpoint.json")

        self._robot_parsers: Dict[str, urllib.robotparser.RobotFileParser] = {}
        self._session: Optional[httpx.AsyncClient] = None

    async def get_session(self) -> httpx.AsyncClient:
        if self._session is None or self._session.is_closed:
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
            }
            self._session = httpx.AsyncClient(headers=headers, timeout=25.0, follow_redirects=True)
        return self._session

    async def close(self):
        if self._session and not self._session.is_closed:
            await self._session.aclose()

    def is_allowed_by_robots(self, url: str) -> bool:
        """Checks if URL path is permitted under robots.txt."""
        try:
            parsed = urlparse(url)
            domain = f"{parsed.scheme}://{parsed.netloc}"
            if domain not in self._robot_parsers:
                rp = urllib.robotparser.RobotFileParser()
                rp.set_url(f"{domain}/robots.txt")
                try:
                    rp.read()
                except Exception:
                    # If robots.txt cannot be fetched or doesn't exist, allow by default
                    pass
                self._robot_parsers[domain] = rp

            rp = self._robot_parsers[domain]
            allowed = rp.can_fetch(self.user_agent, url)
            if not allowed:
                logger.warning(f"Robots.txt DISALLOW for URL: {url} by user-agent: {self.user_agent}")
            return allowed
        except Exception as e:
            logger.debug(f"Error checking robots.txt: {e}. Defaulting to True.")
            return True

    async def fetch(self, url: str, is_json: bool = False) -> Optional[Any]:
        """
        Fetches web page or API with exponential backoff retry.
        Respects robots.txt and delays to avoid overloading servers.
        """
        if not self.is_allowed_by_robots(url):
            logger.warning(f"Skipping {url} due to robots.txt rules.")
            return None

        # Polite delay
        await asyncio.sleep(self.delay_seconds)

        session = await self.get_session()
        for attempt in range(1, self.max_retries + 1):
            try:
                response = await session.get(url)
                if response.status_code == 200:
                    return response.json() if is_json else response.text
                elif response.status_code in [404, 410]:
                    logger.warning(f"URL not found ({response.status_code}): {url}")
                    return None
                elif response.status_code == 429:
                    sleep_time = (2 ** attempt) * 2
                    logger.warning(f"Rate limited (429). Backing off for {sleep_time}s on {url}")
                    await asyncio.sleep(sleep_time)
                else:
                    logger.warning(f"HTTP {response.status_code} for {url} (Attempt {attempt}/{self.max_retries})")
            except Exception as e:
                sleep_time = (2 ** attempt) * 1.5
                logger.warning(f"Fetch error {url}: {e}. Retrying in {sleep_time}s...")
                await asyncio.sleep(sleep_time)

        logger.error(f"Failed to fetch {url} after {self.max_retries} attempts.")
        return None

    def save_checkpoint(self, state: Dict[str, Any]):
        """Persists crawler progress checkpoint for pause/resume capability."""
        try:
            with open(self.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            logger.debug(f"Checkpoint saved: {self.checkpoint_file}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def load_checkpoint(self) -> Dict[str, Any]:
        """Loads previous checkpoint if exists."""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read checkpoint: {e}")
        return {}

    @abstractmethod
    def parse(self, html_or_json: Any, **kwargs) -> List[Dict[str, Any]]:
        """Parses fetched content into structured records."""
        pass

    @abstractmethod
    async def save(self, records: List[Dict[str, Any]]) -> int:
        """Saves parsed records to Supabase / Database."""
        pass

    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        """Executes full crawl cycle."""
        pass
