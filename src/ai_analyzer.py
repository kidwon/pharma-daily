"""
AI Analyzer for Pharma Daily
Uses DeepSeek API for intelligent news analysis and summarization.
"""

import os
import json
import logging
from typing import Optional
from datetime import datetime

from .fetcher import NewsItem
from .config import CATEGORIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DeepSeek API configuration
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")


class AIAnalyzer:
    """
    AI-powered pharmaceutical news analyzer using DeepSeek API.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=DEEPSEEK_BASE_URL
                )
                logger.info("DeepSeek API client initialized")
            except ImportError:
                logger.warning("openai package not installed, AI analysis disabled")
        else:
            logger.warning("DEEPSEEK_API_KEY not set, AI analysis disabled")

    def analyze_news(self, items: list[NewsItem], date_str: str) -> dict:
        """
        Analyze news items using DeepSeek API.

        Args:
            items: List of NewsItem objects
            date_str: Date string for the analysis

        Returns:
            Dictionary containing analysis results
        """
        if not self.client or not items:
            return self._fallback_analysis(items, date_str)

        # Prepare news data for analysis
        news_text = self._format_news_for_prompt(items)

        prompt = f"""你是资深制药行业分析师。请分析以下最近一周（截至 {date_str}）的制药行业新闻，并按要求输出。

## 新闻列表

{news_text}

## 分析要求

请输出 JSON 格式，包含以下字段：

```json
{{
  "overview": "本周概览，2-3句话总结最重要的行业动态",
  "top_news": [
    {{
      "index": 1,
      "title": "新闻标题",
      "importance": 5,
      "reason": "重要性原因（一句话）",
      "category": "类别"
    }}
  ],
  "category_summary": {{
    "新药研发": "该类别简要总结",
    "临床试验": "该类别简要总结"
  }},
  "tomorrow_watch": "明日值得关注的事项"
}}
```

## 分类标准
- 新药研发 (Drug R&D): 研发管线、候选药物、靶点发现
- 临床试验 (Clinical Trials): I/II/III期试验、疗效数据
- 监管审批 (Regulatory): FDA/EMA/NMPA批准
- 商业动态 (Business/M&A): 收购、并购、融资、合作
- 市场分析 (Market Analysis): 销售数据、市场预测
- 政策法规 (Policy): 医保政策、集采、行业规定

## 重要性评分 (1-5)
- 5分: 重大突破（新药获批、>10亿美元收购、突破性疗法）
- 4分: 重要动态（关键III期数据、大型合作）
- 3分: 一般行业新闻
- 2分: 次要新闻
- 1分: 边缘相关

请选出最重要的5条新闻放入 top_news。只输出 JSON，不要其他内容。"""

        try:
            logger.info("Calling DeepSeek API for analysis...")
            response = self.client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "你是专业的制药行业分析师，擅长新闻分析和趋势洞察。请用中文回答，输出格式为 JSON。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )

            content = response.choices[0].message.content.strip()

            # Extract JSON from response
            analysis = self._parse_json_response(content)

            if analysis:
                logger.info("AI analysis completed successfully")
                return analysis
            else:
                logger.warning("Failed to parse AI response, using fallback")
                return self._fallback_analysis(items, date_str)

        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return self._fallback_analysis(items, date_str)

    def _format_news_for_prompt(self, items: list[NewsItem]) -> str:
        """Format news items for the analysis prompt."""
        lines = []
        for i, item in enumerate(items[:30], 1):  # Limit to 30 items
            lang = "中文" if item.language == "zh" else "英文"
            lines.append(f"{i}. [{item.source}] ({lang}) {item.title}")
            if item.summary:
                summary = item.summary[:200] + "..." if len(item.summary) > 200 else item.summary
                lines.append(f"   摘要: {summary}")
            lines.append("")
        return "\n".join(lines)

    def _parse_json_response(self, content: str) -> Optional[dict]:
        """Parse JSON from AI response."""
        try:
            # Try direct parse
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _fallback_analysis(self, items: list[NewsItem], date_str: str) -> dict:
        """Generate basic analysis without AI."""
        logger.info("Using fallback analysis (no AI)")

        # Sort by importance
        sorted_items = sorted(items, key=lambda x: x.importance, reverse=True)

        # Group by category
        categories = {}
        for item in items:
            cat = item.category or "综合"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)

        # Generate top news
        top_news = []
        for i, item in enumerate(sorted_items[:5], 1):
            top_news.append({
                "index": i,
                "title": item.title,
                "importance": item.importance or 3,
                "reason": f"来自 {item.source}",
                "category": item.category or "综合"
            })

        # Generate category summary
        category_summary = {}
        for cat, cat_items in categories.items():
            category_summary[cat] = f"共 {len(cat_items)} 条新闻"

        return {
            "overview": f"{date_str} 共获取 {len(items)} 条制药行业新闻，涵盖 {len(categories)} 个类别。",
            "top_news": top_news,
            "category_summary": category_summary,
            "tomorrow_watch": "请关注各类临床试验数据更新和监管审批进展。"
        }

    def format_analysis_markdown(self, analysis: dict, items: list[NewsItem]) -> str:
        """Format analysis results as Markdown."""
        lines = [
            "## 📊 AI 智能分析",
            "",
            "### 本周概览",
            "",
            analysis.get("overview", ""),
            "",
            "### 🔥 重点新闻",
            ""
        ]

        # Top news
        for news in analysis.get("top_news", []):
            stars = "⭐" * news.get("importance", 3)
            lines.append(f"**{news['index']}. {news['title']}** {stars}")
            lines.append(f"   - 类别: {news.get('category', '综合')}")
            lines.append(f"   - {news.get('reason', '')}")
            lines.append("")

        # Category summary
        lines.extend([
            "### 📁 分类摘要",
            ""
        ])
        for cat, summary in analysis.get("category_summary", {}).items():
            en_name = CATEGORIES.get(cat, {}).get("en", "")
            lines.append(f"**{cat}** ({en_name}): {summary}")
        lines.append("")

        # Tomorrow watch
        if analysis.get("tomorrow_watch"):
            lines.extend([
                "### 🔮 明日关注",
                "",
                analysis["tomorrow_watch"],
                ""
            ])

        return "\n".join(lines)


def analyze_with_ai(items: list[NewsItem], date_str: str, api_key: Optional[str] = None) -> tuple[dict, str]:
    """
    Convenience function to analyze news with AI.

    Args:
        items: List of NewsItem objects
        date_str: Date string
        api_key: Optional DeepSeek API key

    Returns:
        Tuple of (analysis dict, formatted markdown)
    """
    analyzer = AIAnalyzer(api_key)
    analysis = analyzer.analyze_news(items, date_str)
    markdown = analyzer.format_analysis_markdown(analysis, items)
    return analysis, markdown


if __name__ == "__main__":
    # Test with mock data
    from datetime import datetime

    mock_items = [
        NewsItem(
            title="FDA批准首个基因编辑疗法用于镰状细胞病",
            link="https://example.com/1",
            summary="美国FDA正式批准了首个基于CRISPR技术的基因编辑疗法。",
            published=datetime.now(),
            source="FiercePharma",
            language="en",
            category="监管审批",
            importance=5
        ),
        NewsItem(
            title="辉瑞宣布以430亿美元收购Seagen",
            link="https://example.com/2",
            summary="辉瑞今日宣布完成对Seagen的收购。",
            published=datetime.now(),
            source="药明康德",
            language="zh",
            category="商业动态",
            importance=5
        ),
    ]

    analyzer = AIAnalyzer()
    result = analyzer.analyze_news(mock_items, "2024-01-15")
    print(json.dumps(result, ensure_ascii=False, indent=2))
