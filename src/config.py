"""
Pharma Daily Configuration
RSS sources and settings for pharmaceutical news aggregation.
"""

from dataclasses import dataclass
from typing import Optional
import os

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")

# Default theme
DEFAULT_THEME = "minimal"

# Available themes
THEMES = ["minimal", "pharma-blue", "warm"]


@dataclass
class RSSSource:
    """RSS feed source configuration."""
    name: str
    url: str
    language: str  # "zh" or "en"
    category: Optional[str] = None
    enabled: bool = True


# Chinese pharmaceutical news sources
CHINESE_SOURCES = [
    RSSSource(
        name="药明康德",
        url="https://news.wuxiapptec.com/feed/",
        language="zh",
        category="综合"
    ),
    RSSSource(
        name="医药魔方",
        url="https://www.pharmcube.com/rss",
        language="zh",
        category="新药研发"
    ),
    RSSSource(
        name="丁香园",
        url="https://www.dxy.cn/bbs/rss",
        language="zh",
        category="综合"
    ),
    RSSSource(
        name="生物谷",
        url="https://news.bioon.com/rss/",
        language="zh",
        category="新药研发"
    ),
    RSSSource(
        name="医药经济报",
        url="https://www.yyjjb.com/rss",
        language="zh",
        category="商业动态"
    ),
    RSSSource(
        name="CPhI制药在线",
        url="https://www.cphi.cn/news/rss",
        language="zh",
        category="综合"
    ),
]

# International pharmaceutical news sources
INTERNATIONAL_SOURCES = [
    RSSSource(
        name="FiercePharma",
        url="https://www.fiercepharma.com/rss/xml",
        language="en",
        category="综合"
    ),
    RSSSource(
        name="BioPharma Dive",
        url="https://www.biopharmadive.com/feeds/news/",
        language="en",
        category="新药研发"
    ),
    RSSSource(
        name="Endpoints News",
        url="https://endpts.com/feed/",
        language="en",
        category="新药研发"
    ),
    RSSSource(
        name="STAT News - Pharma",
        url="https://www.statnews.com/category/pharma/feed/",
        language="en",
        category="综合"
    ),
    RSSSource(
        name="FDA News",
        url="https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/drugs/rss.xml",
        language="en",
        category="监管审批"
    ),
    RSSSource(
        name="Pharma Times",
        url="https://www.pharmatimes.com/rss",
        language="en",
        category="商业动态"
    ),
    RSSSource(
        name="Drug Discovery Today",
        url="https://www.drugdiscoverytoday.com/rss/recent",
        language="en",
        category="新药研发"
    ),
]

# All sources combined
ALL_SOURCES = CHINESE_SOURCES + INTERNATIONAL_SOURCES


def get_enabled_sources() -> list[RSSSource]:
    """Get all enabled RSS sources."""
    return [s for s in ALL_SOURCES if s.enabled]


def get_sources_by_language(language: str) -> list[RSSSource]:
    """Get sources filtered by language."""
    return [s for s in get_enabled_sources() if s.language == language]


def get_sources_by_category(category: str) -> list[RSSSource]:
    """Get sources filtered by category."""
    return [s for s in get_enabled_sources() if s.category == category]


# News categories for classification
CATEGORIES = {
    "新药研发": {
        "en": "Drug R&D",
        "keywords_zh": ["研发", "新药", "候选药物", "靶点", "管线", "IND", "临床前"],
        "keywords_en": ["R&D", "pipeline", "drug discovery", "candidate", "target", "preclinical"]
    },
    "临床试验": {
        "en": "Clinical Trials",
        "keywords_zh": ["临床试验", "I期", "II期", "III期", "受试者", "疗效", "安全性"],
        "keywords_en": ["clinical trial", "Phase I", "Phase II", "Phase III", "efficacy", "safety"]
    },
    "监管审批": {
        "en": "Regulatory",
        "keywords_zh": ["FDA", "EMA", "NMPA", "获批", "上市", "审批", "受理", "CDE"],
        "keywords_en": ["FDA", "EMA", "approval", "approved", "regulatory", "submission", "NDA", "BLA"]
    },
    "商业动态": {
        "en": "Business/M&A",
        "keywords_zh": ["收购", "并购", "合作", "授权", "融资", "IPO", "交易"],
        "keywords_en": ["acquisition", "merger", "partnership", "licensing", "funding", "IPO", "deal"]
    },
    "市场分析": {
        "en": "Market Analysis",
        "keywords_zh": ["市场", "销售", "营收", "增长", "预测", "竞争"],
        "keywords_en": ["market", "sales", "revenue", "growth", "forecast", "competition"]
    },
    "政策法规": {
        "en": "Policy",
        "keywords_zh": ["政策", "法规", "医保", "集采", "指南", "规定"],
        "keywords_en": ["policy", "regulation", "guideline", "reimbursement", "pricing"]
    },
}
