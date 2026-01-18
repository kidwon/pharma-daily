"""
AI Analyzer for Pharma Daily
Uses Claude to analyze, summarize, and categorize pharmaceutical news.
"""

from typing import Optional
from dataclasses import dataclass
import json
import logging

from .fetcher import NewsItem
from .config import CATEGORIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AnalyzedNews:
    """Analyzed news item with AI-generated insights."""
    item: NewsItem
    summary_zh: str
    summary_en: str
    category: str
    importance: int  # 1-5 scale
    key_points: list[str]
    tags: list[str]


class PharmaAnalyzer:
    """
    Analyzes pharmaceutical news using AI.

    Note: This analyzer provides prompts for Claude to process.
    When used as a Claude Code skill, Claude directly processes the news.
    """

    def __init__(self):
        self.categories = list(CATEGORIES.keys())

    def create_analysis_prompt(self, items: list[NewsItem]) -> str:
        """
        Create a prompt for Claude to analyze the news items.

        Args:
            items: List of NewsItem objects to analyze.

        Returns:
            A formatted prompt string.
        """
        news_text = self._format_news_for_analysis(items)

        prompt = f"""请分析以下制药行业新闻，并按照指定格式输出：

## 新闻列表

{news_text}

## 分析要求

1. **分类**: 将每条新闻归类到以下类别之一：
   - 新药研发 (Drug R&D)
   - 临床试验 (Clinical Trials)
   - 监管审批 (Regulatory)
   - 商业动态 (Business/M&A)
   - 市场分析 (Market Analysis)
   - 政策法规 (Policy)

2. **重要性评分**: 1-5分，5分最重要
   - 5分: 重大突破性新闻（如新药获批、重大收购）
   - 4分: 重要行业动态
   - 3分: 一般行业新闻
   - 2分: 次要新闻
   - 1分: 边缘相关新闻

3. **中文摘要**: 为每条新闻提供简洁的中文摘要（50-100字）

4. **关键词**: 提取3-5个关键标签

## 输出格式

请按重要性排序，使用以下Markdown格式输出：

### [类别名称]

#### [新闻标题]
- **重要性**: ⭐⭐⭐⭐⭐ (5/5)
- **摘要**: [中文摘要]
- **来源**: [来源名称]
- **关键词**: #关键词1 #关键词2 #关键词3
- **链接**: [原文链接]

---

请开始分析："""

        return prompt

    def _format_news_for_analysis(self, items: list[NewsItem]) -> str:
        """Format news items for the analysis prompt."""
        formatted = []

        for i, item in enumerate(items, 1):
            entry = f"""### {i}. {item.title}
- **来源**: {item.source}
- **语言**: {"中文" if item.language == "zh" else "英文"}
- **发布时间**: {item.published.strftime("%Y-%m-%d %H:%M")}
- **链接**: {item.link}
- **摘要**: {item.summary}
"""
            formatted.append(entry)

        return "\n".join(formatted)

    def create_daily_summary_prompt(self, items: list[NewsItem], date_str: str) -> str:
        """
        Create a prompt for generating a daily summary.

        Args:
            items: List of NewsItem objects.
            date_str: Date string for the summary.

        Returns:
            A formatted prompt string.
        """
        news_text = self._format_news_for_analysis(items)

        prompt = f"""请为{date_str}的制药行业新闻生成一份每日简报。

## 今日新闻

{news_text}

## 简报要求

1. **今日概览**: 用2-3句话概括今天最重要的制药行业动态

2. **重点新闻**: 挑选最重要的3-5条新闻，详细分析

3. **分类汇总**: 按类别整理所有新闻
   - 新药研发
   - 临床试验
   - 监管审批
   - 商业动态
   - 市场分析
   - 政策法规

4. **数据统计**:
   - 总新闻数量
   - 各类别分布
   - 中英文来源比例

5. **明日关注**: 基于今日新闻，提示明天值得关注的事项

请使用清晰的Markdown格式输出简报。"""

        return prompt

    def group_by_category(self, items: list[NewsItem]) -> dict[str, list[NewsItem]]:
        """Group news items by category."""
        grouped = {cat: [] for cat in self.categories}
        grouped["综合"] = []

        for item in items:
            category = item.category or "综合"
            if category in grouped:
                grouped[category].append(item)
            else:
                grouped["综合"].append(item)

        # Remove empty categories
        return {k: v for k, v in grouped.items() if v}

    def rank_by_importance(self, items: list[NewsItem]) -> list[NewsItem]:
        """
        Rank news items by estimated importance.

        This is a heuristic ranking. For better results, use Claude's analysis.
        """
        def importance_score(item: NewsItem) -> int:
            score = 0
            text = (item.title + " " + item.summary).lower()

            # High importance keywords
            high_keywords = [
                "获批", "approved", "fda", "ema", "nmpa",
                "突破", "breakthrough", "首个", "first",
                "收购", "acquisition", "merger", "billion",
                "ipo", "融资", "funding"
            ]

            for kw in high_keywords:
                if kw in text:
                    score += 2

            # Medium importance
            medium_keywords = [
                "临床", "clinical", "phase", "试验",
                "合作", "partnership", "collaboration"
            ]

            for kw in medium_keywords:
                if kw in text:
                    score += 1

            return score

        for item in items:
            item.importance = min(5, importance_score(item))

        return sorted(items, key=lambda x: x.importance, reverse=True)


def analyze_news(items: list[NewsItem]) -> str:
    """
    Generate an analysis prompt for the given news items.

    This function is designed to be called by Claude Code skill,
    which will then process the prompt directly.
    """
    analyzer = PharmaAnalyzer()
    return analyzer.create_analysis_prompt(items)


def create_daily_brief(items: list[NewsItem], date_str: str) -> str:
    """
    Generate a daily brief prompt.
    """
    analyzer = PharmaAnalyzer()
    return analyzer.create_daily_summary_prompt(items, date_str)


if __name__ == "__main__":
    # Test with mock data
    from datetime import datetime

    mock_items = [
        NewsItem(
            title="FDA批准首个基因编辑疗法",
            link="https://example.com/1",
            summary="美国FDA正式批准了首个基于CRISPR技术的基因编辑疗法...",
            published=datetime.now(),
            source="FiercePharma",
            language="en",
            category="监管审批"
        ),
        NewsItem(
            title="辉瑞宣布收购生物技术公司",
            link="https://example.com/2",
            summary="辉瑞今日宣布以430亿美元收购某生物技术公司...",
            published=datetime.now(),
            source="药明康德",
            language="zh",
            category="商业动态"
        ),
    ]

    analyzer = PharmaAnalyzer()
    prompt = analyzer.create_analysis_prompt(mock_items)
    print("Analysis Prompt:")
    print("=" * 50)
    print(prompt)
