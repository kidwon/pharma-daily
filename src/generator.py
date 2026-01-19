"""
Output Generator for Pharma Daily
Generates HTML pages and Markdown documents from analyzed news.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
import logging

from .fetcher import NewsItem
from .config import OUTPUT_DIR, DEFAULT_THEME, THEMES, CATEGORIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PharmaGenerator:
    """Generates HTML and Markdown output for pharmaceutical news."""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or OUTPUT_DIR)
        self.template_dir = Path(__file__).parent.parent / "templates"

        # Setup Jinja2
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Register filters
        self.env.filters['format_date'] = lambda d: d.strftime("%Y-%m-%d %H:%M") if d else ""
        self.env.filters['format_date_short'] = lambda d: d.strftime("%m/%d") if d else ""
        self.env.filters['markdown_to_html'] = self._markdown_to_html

    def _markdown_to_html(self, text: str) -> str:
        """Convert Markdown text to HTML."""
        if not text:
            return ""

        import re

        # Convert headers
        text = re.sub(r'^### (.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)

        # Convert bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

        # Convert list items
        text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        text = re.sub(r'(<li>.*</li>\n?)+', r'<ul>\g<0></ul>', text)

        # Convert line breaks (double newline = paragraph, single = <br>)
        paragraphs = text.split('\n\n')
        result = []
        for p in paragraphs:
            p = p.strip()
            if p:
                # If it's already wrapped in a tag, don't wrap in <p>
                if p.startswith('<h') or p.startswith('<ul'):
                    result.append(p)
                else:
                    # Replace single newlines with <br>
                    p = p.replace('\n', '<br>\n')
                    result.append(f'<p>{p}</p>')

        return '\n'.join(result)

    def generate_markdown(
        self,
        items: list[NewsItem],
        date_str: str,
        analysis: Optional[str] = None
    ) -> str:
        """
        Generate a Markdown document for the daily news.

        Args:
            items: List of NewsItem objects.
            date_str: Date string for the document.
            analysis: Optional AI-generated analysis to include.

        Returns:
            Generated Markdown content.
        """
        grouped = self._group_by_category(items)

        md_lines = [
            f"# 制药日报 Pharma Daily",
            f"",
            f"**日期**: {date_str}",
            f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**新闻数量**: {len(items)}",
            f"",
            "---",
            "",
        ]

        # Add analysis if provided
        if analysis:
            md_lines.extend([
                "## 今日概览",
                "",
                analysis,
                "",
                "---",
                "",
            ])

        # Add statistics
        md_lines.extend([
            "## 数据统计",
            "",
            "| 类别 | 数量 |",
            "|------|------|",
        ])

        for category, news_list in grouped.items():
            en_name = CATEGORIES.get(category, {}).get("en", category)
            md_lines.append(f"| {category} ({en_name}) | {len(news_list)} |")

        md_lines.extend(["", "---", ""])

        # Add news by category
        for category, news_list in grouped.items():
            if not news_list:
                continue

            en_name = CATEGORIES.get(category, {}).get("en", category)
            md_lines.extend([
                f"## {category} | {en_name}",
                "",
            ])

            for item in news_list:
                importance_stars = "⭐" * min(item.importance, 5) if item.importance else ""
                lang_badge = "🇨🇳" if item.language == "zh" else "🇺🇸"

                md_lines.extend([
                    f"### {lang_badge} {item.title}",
                    "",
                    f"- **来源**: {item.source}",
                    f"- **时间**: {item.published.strftime('%Y-%m-%d %H:%M')}",
                ])

                if importance_stars:
                    md_lines.append(f"- **重要性**: {importance_stars}")

                if item.summary:
                    md_lines.extend([
                        "",
                        f"> {item.summary}",
                    ])

                md_lines.extend([
                    "",
                    f"🔗 [阅读原文]({item.link})",
                    "",
                    "---",
                    "",
                ])

        # Footer
        md_lines.extend([
            "",
            "---",
            "",
            "*Generated by Pharma Daily - 制药资讯聚合系统*",
            "",
            f"*{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        ])

        return "\n".join(md_lines)

    def generate_html(
        self,
        items: list[NewsItem],
        date_str: str,
        theme: str = DEFAULT_THEME,
        analysis: Optional[str] = None
    ) -> str:
        """
        Generate an HTML page for the daily news.

        Args:
            items: List of NewsItem objects.
            date_str: Date string for the document.
            theme: Theme name (minimal, pharma-blue, warm).
            analysis: Optional AI-generated analysis to include.

        Returns:
            Generated HTML content.
        """
        if theme not in THEMES:
            logger.warning(f"Unknown theme '{theme}', using default")
            theme = DEFAULT_THEME

        template_file = f"web/{theme}.html"

        try:
            template = self.env.get_template(template_file)
        except Exception as e:
            logger.error(f"Template not found: {template_file}, using inline template")
            return self._generate_inline_html(items, date_str, theme, analysis)

        grouped = self._group_by_category(items)

        context = {
            "title": f"制药日报 - {date_str}",
            "date": date_str,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_count": len(items),
            "news_by_category": grouped,
            "categories": CATEGORIES,
            "analysis": analysis,
            "theme": theme,
        }

        return template.render(**context)

    def _generate_inline_html(
        self,
        items: list[NewsItem],
        date_str: str,
        theme: str,
        analysis: Optional[str]
    ) -> str:
        """Generate HTML using inline template (fallback)."""
        grouped = self._group_by_category(items)

        # Theme colors
        themes = {
            "minimal": {
                "bg": "#ffffff",
                "text": "#1d1d1f",
                "accent": "#0071e3",
                "card_bg": "#f5f5f7"
            },
            "pharma-blue": {
                "bg": "#f0f4f8",
                "text": "#2d3748",
                "accent": "#2b6cb0",
                "card_bg": "#ffffff"
            },
            "warm": {
                "bg": "#faf8f5",
                "text": "#4a4a4a",
                "accent": "#d97706",
                "card_bg": "#ffffff"
            }
        }
        colors = themes.get(theme, themes["minimal"])

        news_html = ""
        for category, news_list in grouped.items():
            if not news_list:
                continue

            en_name = CATEGORIES.get(category, {}).get("en", category)
            news_html += f'<section class="category"><h2>{category} <span class="en">| {en_name}</span></h2>'

            for item in news_list:
                lang_flag = "🇨🇳" if item.language == "zh" else "🇺🇸"
                stars = "⭐" * min(item.importance, 5) if item.importance else ""

                news_html += f'''
                <article class="news-card">
                    <h3>{lang_flag} {item.title}</h3>
                    <div class="meta">
                        <span class="source">{item.source}</span>
                        <span class="date">{item.published.strftime("%Y-%m-%d")}</span>
                        {f'<span class="importance">{stars}</span>' if stars else ''}
                    </div>
                    <p class="summary">{item.summary}</p>
                    <a href="{item.link}" target="_blank" class="read-more">阅读原文 →</a>
                </article>
                '''

            news_html += '</section>'

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>制药日报 - {date_str}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
            background: {colors["bg"]};
            color: {colors["text"]};
            line-height: 1.6;
            padding: 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 1px solid #e0e0e0;
            margin-bottom: 40px;
        }}
        h1 {{ font-size: 2.5rem; font-weight: 600; margin-bottom: 10px; }}
        .subtitle {{ color: #666; font-size: 1.1rem; }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 1.5rem; font-weight: 600; color: {colors["accent"]}; }}
        .stat-label {{ font-size: 0.9rem; color: #666; }}
        .category {{ margin-bottom: 40px; }}
        .category h2 {{
            font-size: 1.5rem;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid {colors["accent"]};
        }}
        .category h2 .en {{ font-weight: 400; color: #888; font-size: 1rem; }}
        .news-card {{
            background: {colors["card_bg"]};
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .news-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }}
        .news-card h3 {{ font-size: 1.2rem; margin-bottom: 10px; }}
        .meta {{
            display: flex;
            gap: 15px;
            margin-bottom: 12px;
            font-size: 0.9rem;
            color: #666;
        }}
        .source {{ color: {colors["accent"]}; font-weight: 500; }}
        .summary {{ color: #555; margin-bottom: 15px; }}
        .read-more {{
            display: inline-block;
            color: {colors["accent"]};
            text-decoration: none;
            font-weight: 500;
        }}
        .read-more:hover {{ text-decoration: underline; }}
        footer {{
            text-align: center;
            padding: 40px 0;
            color: #888;
            font-size: 0.9rem;
        }}
        @media (max-width: 600px) {{
            body {{ padding: 15px; }}
            h1 {{ font-size: 1.8rem; }}
            .news-card {{ padding: 16px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>💊 制药日报</h1>
            <p class="subtitle">Pharma Daily - {date_str}</p>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{len(items)}</div>
                    <div class="stat-label">新闻总数</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{len(grouped)}</div>
                    <div class="stat-label">类别数</div>
                </div>
            </div>
        </header>

        <main>
            {news_html}
        </main>

        <footer>
            <p>Generated by Pharma Daily - 制药资讯聚合系统</p>
            <p>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </footer>
    </div>
</body>
</html>'''

        return html

    def _group_by_category(self, items: list[NewsItem]) -> dict[str, list[NewsItem]]:
        """Group news items by category."""
        grouped = {}
        for item in items:
            category = item.category or "综合"
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(item)

        # Sort by importance within each category
        for category in grouped:
            grouped[category].sort(key=lambda x: x.importance, reverse=True)

        return grouped

    def save_output(
        self,
        items: list[NewsItem],
        date_str: str,
        theme: str = DEFAULT_THEME,
        analysis: Optional[str] = None
    ) -> dict[str, str]:
        """
        Save both HTML and Markdown output.

        Args:
            items: List of NewsItem objects.
            date_str: Date string for the output.
            theme: Theme name for HTML.
            analysis: Optional AI-generated analysis.

        Returns:
            Dictionary with paths to generated files.
        """
        # Create output directory
        output_path = self.output_dir / date_str.replace("-", "")
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate and save Markdown
        md_content = self.generate_markdown(items, date_str, analysis)
        md_file = output_path / "daily.md"
        md_file.write_text(md_content, encoding="utf-8")
        logger.info(f"Saved Markdown: {md_file}")

        # Generate and save HTML
        html_content = self.generate_html(items, date_str, theme, analysis)
        html_file = output_path / "index.html"
        html_file.write_text(html_content, encoding="utf-8")
        logger.info(f"Saved HTML: {html_file}")

        return {
            "markdown": str(md_file),
            "html": str(html_file),
            "directory": str(output_path)
        }


def generate_daily_output(
    items: list[NewsItem],
    date_str: str,
    theme: str = DEFAULT_THEME,
    analysis: Optional[str] = None,
    output_dir: Optional[str] = None
) -> dict[str, str]:
    """
    Convenience function to generate daily output.

    Args:
        items: List of NewsItem objects.
        date_str: Date string.
        theme: Theme name.
        analysis: Optional analysis text.
        output_dir: Optional output directory.

    Returns:
        Dictionary with generated file paths.
    """
    generator = PharmaGenerator(output_dir)
    return generator.save_output(items, date_str, theme, analysis)


if __name__ == "__main__":
    # Test with mock data
    from datetime import datetime

    mock_items = [
        NewsItem(
            title="FDA批准首个基因编辑疗法用于镰状细胞病治疗",
            link="https://example.com/1",
            summary="美国FDA正式批准了首个基于CRISPR技术的基因编辑疗法，用于治疗镰状细胞病，这是基因治疗领域的重大里程碑。",
            published=datetime.now(),
            source="FiercePharma",
            language="en",
            category="监管审批",
            importance=5
        ),
        NewsItem(
            title="辉瑞宣布以430亿美元收购Seagen",
            link="https://example.com/2",
            summary="辉瑞今日宣布以约430亿美元收购癌症药物开发商Seagen，这将显著增强辉瑞在肿瘤领域的研发管线。",
            published=datetime.now(),
            source="药明康德",
            language="zh",
            category="商业动态",
            importance=5
        ),
        NewsItem(
            title="诺华GLP-1类药物III期临床结果积极",
            link="https://example.com/3",
            summary="诺华公司公布其GLP-1受体激动剂III期临床试验达到主要终点，显示出良好的减重效果和安全性。",
            published=datetime.now(),
            source="生物谷",
            language="zh",
            category="临床试验",
            importance=4
        ),
    ]

    generator = PharmaGenerator()

    # Generate Markdown
    md = generator.generate_markdown(mock_items, "2024-01-15")
    print("Generated Markdown:")
    print("=" * 50)
    print(md[:1000])
    print("...")

    # Generate HTML
    html = generator.generate_html(mock_items, "2024-01-15", "minimal")
    print("\nGenerated HTML (preview):")
    print("=" * 50)
    print(html[:500])
    print("...")
