#!/usr/bin/env python3
"""
Pharma Daily - Main Entry Point
Pharmaceutical news aggregation and analysis system.
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging

from .fetcher import fetch_pharma_news, PharmaFetcher, NewsItem
from .analyzer import PharmaAnalyzer, analyze_news, create_daily_brief
from .generator import PharmaGenerator, generate_daily_output
from .config import DEFAULT_THEME, THEMES, OUTPUT_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_date(date_str: str) -> tuple[datetime, str]:
    """
    Parse date string into datetime object and formatted string.

    Args:
        date_str: Date string (today, yesterday, YYYY-MM-DD, 今天, 昨天)

    Returns:
        Tuple of (datetime object, formatted date string)
    """
    date_str_lower = date_str.lower().strip()

    if date_str_lower in ["today", "今天"]:
        dt = datetime.now()
    elif date_str_lower in ["yesterday", "昨天"]:
        dt = datetime.now() - timedelta(days=1)
    else:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid date format: {date_str}")
            dt = datetime.now()

    return dt, dt.strftime("%Y-%m-%d")


def cmd_fetch(args):
    """Fetch pharmaceutical news."""
    dt, date_str = parse_date(args.date)

    logger.info(f"Fetching pharma news for {date_str}...")

    items = fetch_pharma_news(
        date_str=args.date,
        language=args.language,
        category=args.category
    )

    if not items:
        logger.warning("No news items found for the specified criteria.")
        return []

    logger.info(f"Fetched {len(items)} news items")

    # Save raw data as JSON for later processing
    output_dir = Path(OUTPUT_DIR) / date_str.replace("-", "")
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_file = output_dir / "raw_news.json"
    raw_data = [
        {
            "title": item.title,
            "link": item.link,
            "summary": item.summary,
            "published": item.published.isoformat(),
            "source": item.source,
            "language": item.language,
            "category": item.category,
            "importance": item.importance
        }
        for item in items
    ]

    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved raw news to {raw_file}")

    # Print summary
    print(f"\n📰 Pharma Daily - {date_str}")
    print(f"{'=' * 50}")
    print(f"Total news items: {len(items)}")
    print()

    # Group by category
    categories = {}
    for item in items:
        cat = item.category or "综合"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)

    for cat, cat_items in categories.items():
        print(f"\n## {cat} ({len(cat_items)})")
        for item in cat_items[:3]:  # Show first 3
            flag = "🇨🇳" if item.language == "zh" else "🇺🇸"
            print(f"  {flag} {item.title[:60]}...")

    return items


def cmd_generate(args):
    """Generate output files."""
    dt, date_str = parse_date(args.date)

    # Check for raw data
    output_dir = Path(OUTPUT_DIR) / date_str.replace("-", "")
    raw_file = output_dir / "raw_news.json"

    if raw_file.exists():
        logger.info(f"Loading cached news from {raw_file}")
        with open(raw_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        items = [
            NewsItem(
                title=d["title"],
                link=d["link"],
                summary=d["summary"],
                published=datetime.fromisoformat(d["published"]),
                source=d["source"],
                language=d["language"],
                category=d["category"],
                importance=d.get("importance", 0)
            )
            for d in raw_data
        ]
    else:
        logger.info("No cached data found, fetching fresh...")
        items = fetch_pharma_news(date_str=args.date)

    if not items:
        logger.error("No news items to generate output from.")
        return

    # Validate theme
    theme = args.theme
    if theme not in THEMES:
        logger.warning(f"Unknown theme '{theme}', using default")
        theme = DEFAULT_THEME

    logger.info(f"Generating output with theme: {theme}")

    # Generate output
    result = generate_daily_output(
        items=items,
        date_str=date_str,
        theme=theme,
        analysis=args.analysis
    )

    print(f"\n✅ Output generated successfully!")
    print(f"📁 Directory: {result['directory']}")
    print(f"📄 Markdown: {result['markdown']}")
    print(f"🌐 HTML: {result['html']}")


def cmd_analyze(args):
    """Generate analysis prompt."""
    dt, date_str = parse_date(args.date)

    # Load or fetch news
    output_dir = Path(OUTPUT_DIR) / date_str.replace("-", "")
    raw_file = output_dir / "raw_news.json"

    if raw_file.exists():
        with open(raw_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        items = [
            NewsItem(
                title=d["title"],
                link=d["link"],
                summary=d["summary"],
                published=datetime.fromisoformat(d["published"]),
                source=d["source"],
                language=d["language"],
                category=d["category"],
                importance=d.get("importance", 0)
            )
            for d in raw_data
        ]
    else:
        items = fetch_pharma_news(date_str=args.date)

    if not items:
        logger.error("No news items to analyze.")
        return

    # Generate analysis prompt
    if args.type == "full":
        prompt = analyze_news(items)
    else:
        prompt = create_daily_brief(items, date_str)

    print(prompt)


def cmd_list_sources(args):
    """List configured RSS sources."""
    from .config import CHINESE_SOURCES, INTERNATIONAL_SOURCES

    print("\n📡 Configured RSS Sources")
    print("=" * 50)

    print("\n🇨🇳 Chinese Sources:")
    for source in CHINESE_SOURCES:
        status = "✅" if source.enabled else "❌"
        print(f"  {status} {source.name}")
        print(f"     Category: {source.category}")
        print(f"     URL: {source.url}")
        print()

    print("\n🇺🇸 International Sources:")
    for source in INTERNATIONAL_SOURCES:
        status = "✅" if source.enabled else "❌"
        print(f"  {status} {source.name}")
        print(f"     Category: {source.category}")
        print(f"     URL: {source.url}")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Pharma Daily - Pharmaceutical News Aggregation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s fetch --date today
  %(prog)s fetch --date yesterday --language zh
  %(prog)s generate --date 2024-01-15 --theme pharma-blue
  %(prog)s analyze --date today --type brief
  %(prog)s sources
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch pharmaceutical news")
    fetch_parser.add_argument(
        "--date", "-d",
        default="today",
        help="Date to fetch (today, yesterday, YYYY-MM-DD)"
    )
    fetch_parser.add_argument(
        "--language", "-l",
        choices=["zh", "en"],
        help="Filter by language"
    )
    fetch_parser.add_argument(
        "--category", "-c",
        help="Filter by category"
    )
    fetch_parser.set_defaults(func=cmd_fetch)

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate output files")
    gen_parser.add_argument(
        "--date", "-d",
        default="today",
        help="Date to generate (today, yesterday, YYYY-MM-DD)"
    )
    gen_parser.add_argument(
        "--theme", "-t",
        default=DEFAULT_THEME,
        choices=THEMES,
        help="HTML theme"
    )
    gen_parser.add_argument(
        "--analysis", "-a",
        help="Include analysis text"
    )
    gen_parser.set_defaults(func=cmd_generate)

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Generate analysis prompt")
    analyze_parser.add_argument(
        "--date", "-d",
        default="today",
        help="Date to analyze"
    )
    analyze_parser.add_argument(
        "--type", "-t",
        default="brief",
        choices=["full", "brief"],
        help="Analysis type"
    )
    analyze_parser.set_defaults(func=cmd_analyze)

    # Sources command
    sources_parser = subparsers.add_parser("sources", help="List RSS sources")
    sources_parser.set_defaults(func=cmd_list_sources)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
