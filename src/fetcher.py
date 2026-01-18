"""
RSS Feed Fetcher for Pharma Daily
Fetches news from pharmaceutical RSS sources with date filtering.
"""

import feedparser
import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from typing import Optional
from dataclasses import dataclass
import time
import logging

from .config import RSSSource, get_enabled_sources, CATEGORIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """A single news item."""
    title: str
    link: str
    summary: str
    published: datetime
    source: str
    language: str
    category: Optional[str] = None
    importance: int = 0  # 0-5 scale


class PharmaFetcher:
    """Fetches pharmaceutical news from configured RSS sources."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.user_agent = "PharmaDaily/1.0 (News Aggregator)"

    def fetch_feed(self, source: RSSSource) -> list[NewsItem]:
        """Fetch news items from a single RSS source."""
        items = []
        try:
            logger.info(f"Fetching from {source.name}...")

            # Use requests to handle more complex scenarios
            headers = {"User-Agent": self.user_agent}
            response = requests.get(source.url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            for entry in feed.entries:
                try:
                    # Parse publication date
                    published = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published = datetime(*entry.updated_parsed[:6])
                    elif hasattr(entry, 'published'):
                        published = date_parser.parse(entry.published)
                    else:
                        published = datetime.now()

                    # Extract summary
                    summary = ""
                    if hasattr(entry, 'summary'):
                        summary = self._clean_html(entry.summary)
                    elif hasattr(entry, 'description'):
                        summary = self._clean_html(entry.description)

                    # Truncate summary if too long
                    if len(summary) > 500:
                        summary = summary[:497] + "..."

                    item = NewsItem(
                        title=entry.get('title', 'Untitled'),
                        link=entry.get('link', ''),
                        summary=summary,
                        published=published,
                        source=source.name,
                        language=source.language,
                        category=source.category
                    )
                    items.append(item)

                except Exception as e:
                    logger.warning(f"Error parsing entry from {source.name}: {e}")
                    continue

            logger.info(f"Fetched {len(items)} items from {source.name}")

        except requests.RequestException as e:
            logger.error(f"Network error fetching {source.name}: {e}")
        except Exception as e:
            logger.error(f"Error fetching {source.name}: {e}")

        return items

    def fetch_all(
        self,
        sources: Optional[list[RSSSource]] = None,
        date_filter: Optional[datetime] = None,
        days_back: int = 1
    ) -> list[NewsItem]:
        """
        Fetch news from all sources with optional date filtering.

        Args:
            sources: List of RSS sources to fetch from. Uses all enabled if None.
            date_filter: Specific date to filter for.
            days_back: Number of days back to include (default: 1).

        Returns:
            List of NewsItem objects sorted by publication date.
        """
        if sources is None:
            sources = get_enabled_sources()

        all_items = []

        for source in sources:
            items = self.fetch_feed(source)
            all_items.extend(items)
            time.sleep(0.5)  # Be polite to servers

        # Apply date filter
        if date_filter:
            cutoff_start = date_filter.replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_end = cutoff_start + timedelta(days=1)
            all_items = [
                item for item in all_items
                if cutoff_start <= item.published < cutoff_end
            ]
        elif days_back:
            cutoff = datetime.now() - timedelta(days=days_back)
            all_items = [item for item in all_items if item.published >= cutoff]

        # Sort by date, newest first
        all_items.sort(key=lambda x: x.published, reverse=True)

        # Classify categories if not set
        for item in all_items:
            if not item.category:
                item.category = self._classify_category(item)

        logger.info(f"Total items fetched: {len(all_items)}")
        return all_items

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        import re
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()

    def _classify_category(self, item: NewsItem) -> str:
        """Classify news item into a category based on keywords."""
        text = (item.title + " " + item.summary).lower()

        best_category = "综合"
        best_score = 0

        for category, info in CATEGORIES.items():
            score = 0
            keywords = info.get(f"keywords_{item.language}", [])

            for keyword in keywords:
                if keyword.lower() in text:
                    score += 1

            if score > best_score:
                best_score = score
                best_category = category

        return best_category if best_score > 0 else "综合"


def fetch_pharma_news(
    date_str: Optional[str] = None,
    language: Optional[str] = None,
    category: Optional[str] = None
) -> list[NewsItem]:
    """
    Convenience function to fetch pharmaceutical news.

    Args:
        date_str: Date string (YYYY-MM-DD) or relative ("today", "yesterday").
        language: Filter by language ("zh" or "en").
        category: Filter by category.

    Returns:
        List of NewsItem objects.
    """
    fetcher = PharmaFetcher()

    # Parse date
    date_filter = None
    days_back = 1

    if date_str:
        date_str_lower = date_str.lower()
        if date_str_lower in ["today", "今天"]:
            date_filter = datetime.now()
        elif date_str_lower in ["yesterday", "昨天"]:
            date_filter = datetime.now() - timedelta(days=1)
        else:
            try:
                date_filter = date_parser.parse(date_str)
            except:
                pass

    # Get sources
    sources = get_enabled_sources()

    if language:
        sources = [s for s in sources if s.language == language]

    if category:
        sources = [s for s in sources if s.category == category]

    # Fetch
    items = fetcher.fetch_all(
        sources=sources,
        date_filter=date_filter,
        days_back=days_back if not date_filter else 0
    )

    return items


if __name__ == "__main__":
    # Test fetching
    print("Testing Pharma Fetcher...")
    items = fetch_pharma_news(date_str="today")

    print(f"\nFetched {len(items)} news items:\n")
    for item in items[:10]:
        print(f"[{item.source}] {item.title}")
        print(f"  Category: {item.category}")
        print(f"  Published: {item.published}")
        print(f"  Link: {item.link}")
        print()
