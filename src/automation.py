#!/usr/bin/env python3
"""
Pharma Daily - Automation Runner
Automated pipeline for fetching, analyzing, and generating pharmaceutical news.

This script is designed to be run by GitHub Actions or other CI/CD systems.

Usage:
    python -m src.automation --date today --theme minimal --output-dir docs
"""

import argparse
import sys
import os
import json
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path

from .fetcher import PharmaFetcher, NewsItem
from .analyzer import PharmaAnalyzer
from .ai_analyzer import AIAnalyzer, analyze_with_ai
from .generator import PharmaGenerator
from .config import OUTPUT_DIR, THEMES, DEFAULT_THEME, get_enabled_sources

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_date(date_str: str) -> tuple[datetime, str]:
    """Parse date string into datetime and formatted string."""
    date_str_lower = date_str.lower().strip()

    if date_str_lower in ["today", "今天"]:
        dt = datetime.now()
    elif date_str_lower in ["yesterday", "昨天"]:
        dt = datetime.now() - timedelta(days=1)
    else:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}, using today")
            dt = datetime.now()

    return dt, dt.strftime("%Y-%m-%d")


def fetch_news(days_back: int = 2) -> list[NewsItem]:
    """
    Fetch news from all enabled sources.

    Args:
        days_back: Number of days back to include news from

    Returns:
        List of NewsItem objects
    """
    logger.info("Starting news fetch...")
    fetcher = PharmaFetcher(timeout=30)
    sources = get_enabled_sources()

    all_items = []
    success_count = 0
    fail_count = 0

    for source in sources:
        try:
            items = fetcher.fetch_feed(source)
            if items:
                all_items.extend(items)
                success_count += 1
                logger.info(f"✅ {source.name}: {len(items)} items")
            else:
                logger.warning(f"⚠️ {source.name}: 0 items")
        except Exception as e:
            fail_count += 1
            logger.error(f"❌ {source.name}: {e}")

    logger.info(f"Fetch complete: {success_count} sources succeeded, {fail_count} failed")
    logger.info(f"Total items fetched: {len(all_items)}")

    # Filter by date if needed
    if days_back > 0:
        cutoff = datetime.now() - timedelta(days=days_back)
        filtered = [item for item in all_items if item.published >= cutoff]
        logger.info(f"After date filter ({days_back} days): {len(filtered)} items")
        return filtered

    return all_items


def rank_news(items: list[NewsItem]) -> list[NewsItem]:
    """Rank news by importance."""
    logger.info("Ranking news by importance...")
    analyzer = PharmaAnalyzer()
    return analyzer.rank_by_importance(items)


def analyze_news(items: list[NewsItem], date_str: str) -> tuple[dict, str]:
    """
    Analyze news using AI (if available) or fallback.

    Returns:
        Tuple of (analysis dict, markdown string)
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")

    if api_key:
        logger.info("Using DeepSeek AI for analysis...")
        return analyze_with_ai(items, date_str, api_key)
    else:
        logger.warning("DEEPSEEK_API_KEY not set, using basic analysis")
        ai_analyzer = AIAnalyzer()
        analysis = ai_analyzer._fallback_analysis(items, date_str)
        markdown = ai_analyzer.format_analysis_markdown(analysis, items)
        return analysis, markdown


def generate_output(
    items: list[NewsItem],
    date_str: str,
    theme: str,
    output_dir: str,
    analysis_md: str
) -> dict:
    """
    Generate HTML and Markdown output.

    Returns:
        Dictionary with output file paths
    """
    logger.info(f"Generating output with theme: {theme}")

    generator = PharmaGenerator(output_dir)

    # Generate dated output
    result = generator.save_output(items, date_str, theme, analysis_md)

    # Also copy to root index.html for GitHub Pages
    root_index = Path(output_dir) / "index.html"
    dated_index = Path(result["html"])

    if dated_index.exists():
        shutil.copy(dated_index, root_index)
        logger.info(f"Copied to root: {root_index}")

    return result


def create_archive_index(output_dir: str) -> None:
    """Create an archive index page listing all daily reports."""
    output_path = Path(output_dir)
    archives = []

    # Find all dated directories
    for item in sorted(output_path.iterdir(), reverse=True):
        if item.is_dir() and item.name.isdigit() and len(item.name) == 8:
            index_file = item / "index.html"
            if index_file.exists():
                date_str = f"{item.name[:4]}-{item.name[4:6]}-{item.name[6:]}"
                archives.append({
                    "date": date_str,
                    "path": f"{item.name}/index.html"
                })

    if not archives:
        return

    # Generate archive page
    archive_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pharma Daily Archive - 制药日报归档</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f7;
        }}
        h1 {{ text-align: center; }}
        .archive-list {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .archive-item {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }}
        .archive-item:last-child {{ border-bottom: none; }}
        a {{ color: #0071e3; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>💊 Pharma Daily Archive</h1>
    <p style="text-align: center; color: #666;">制药日报历史归档</p>
    <div class="archive-list">
"""

    for archive in archives[:30]:  # Show last 30
        archive_html += f"""        <div class="archive-item">
            <span>{archive['date']}</span>
            <a href="{archive['path']}">查看 →</a>
        </div>
"""

    archive_html += """    </div>
    <p style="text-align: center; margin-top: 24px; color: #888; font-size: 14px;">
        Generated by Pharma Daily
    </p>
</body>
</html>"""

    archive_file = output_path / "archive.html"
    archive_file.write_text(archive_html, encoding="utf-8")
    logger.info(f"Created archive index: {archive_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Pharma Daily Automation Runner"
    )
    parser.add_argument(
        "--date", "-d",
        default="today",
        help="Date to process (today, yesterday, YYYY-MM-DD)"
    )
    parser.add_argument(
        "--theme", "-t",
        default=DEFAULT_THEME,
        choices=THEMES,
        help="HTML theme"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=OUTPUT_DIR,
        help="Output directory"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=2,
        help="Days back to include news (0 for no filter)"
    )
    parser.add_argument(
        "--skip-ai",
        action="store_true",
        help="Skip AI analysis even if API key is available"
    )

    args = parser.parse_args()

    # Parse date
    dt, date_str = parse_date(args.date)
    logger.info(f"=" * 50)
    logger.info(f"Pharma Daily Automation")
    logger.info(f"Date: {date_str}")
    logger.info(f"Theme: {args.theme}")
    logger.info(f"Output: {args.output_dir}")
    logger.info(f"=" * 50)

    try:
        # Step 1: Fetch news
        items = fetch_news(args.days_back)
        if not items:
            logger.error("No news items fetched, aborting")
            sys.exit(1)

        # Step 2: Rank news
        items = rank_news(items)

        # Step 3: AI Analysis
        if args.skip_ai:
            os.environ.pop("DEEPSEEK_API_KEY", None)
        analysis, analysis_md = analyze_news(items, date_str)

        # Step 4: Generate output
        result = generate_output(
            items=items,
            date_str=date_str,
            theme=args.theme,
            output_dir=args.output_dir,
            analysis_md=analysis_md
        )

        # Step 5: Create archive index
        create_archive_index(args.output_dir)

        # Summary
        logger.info(f"=" * 50)
        logger.info(f"✅ Generation complete!")
        logger.info(f"📁 Directory: {result['directory']}")
        logger.info(f"📄 Markdown: {result['markdown']}")
        logger.info(f"🌐 HTML: {result['html']}")
        logger.info(f"📊 Total news: {len(items)}")
        logger.info(f"=" * 50)

        # Save summary JSON
        summary = {
            "date": date_str,
            "generated_at": datetime.now().isoformat(),
            "theme": args.theme,
            "total_items": len(items),
            "files": result,
            "analysis": analysis
        }
        summary_file = Path(result["directory"]) / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info(f"📋 Summary: {summary_file}")

    except Exception as e:
        logger.error(f"Automation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
