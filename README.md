# 💊 Pharma Daily - 制药资讯聚合系统

自动抓取、分析、生成制药行业每日新闻简报的 Claude Code 技能。

## 功能特性

- 🌐 **多源聚合**: 支持中英文制药新闻源（药明康德、FiercePharma、Endpoints等）
- 🤖 **AI 分析**: 使用 Claude 智能分析、分类、评估新闻重要性
- 📊 **自动分类**: 新药研发、临床试验、监管审批、商业动态等6大类别
- 🎨 **多主题网页**: 3种精美主题（极简、医药蓝、温暖）
- 📝 **Markdown 输出**: 结构化的每日简报文档

## 快速开始

### 安装依赖

```bash
cd pharma-daily
pip install -r requirements.txt
```

### 命令行使用

```bash
# 获取今日新闻
python -m src.main fetch --date today

# 获取昨日新闻
python -m src.main fetch --date yesterday

# 生成网页（极简主题）
python -m src.main generate --date today --theme minimal

# 生成网页（医药蓝主题）
python -m src.main generate --date today --theme pharma-blue

# 查看所有新闻源
python -m src.main sources
```

### Claude Code 技能使用

在 Claude Code 中直接输入：

```
今天制药资讯
```

```
昨天制药资讯，生成网页
```

```
2024-01-15 制药资讯 --theme pharma-blue
```

## 目录结构

```
pharma-daily/
├── .claude/
│   └── skills/
│       └── pharma-daily/
│           ├── skill.json      # 技能配置
│           └── prompt.md       # 技能提示词
├── src/
│   ├── __init__.py
│   ├── config.py              # 配置和RSS源
│   ├── fetcher.py             # RSS抓取模块
│   ├── analyzer.py            # AI分析模块
│   ├── generator.py           # 输出生成模块
│   └── main.py                # 主入口
├── templates/
│   ├── web/
│   │   ├── minimal.html       # 极简主题
│   │   ├── pharma-blue.html   # 医药蓝主题
│   │   └── warm.html          # 温暖主题
│   └── markdown/
│       └── daily.md           # Markdown模板
├── docs/                      # 生成的输出
│   └── YYYYMMDD/
│       ├── index.html
│       ├── daily.md
│       └── raw_news.json
├── requirements.txt
└── README.md
```

## 新闻源

### 中文源

| 名称 | 类别 | URL |
|------|------|-----|
| 药明康德 | 综合 | news.wuxiapptec.com |
| 医药魔方 | 新药研发 | pharmcube.com |
| 丁香园 | 综合 | dxy.cn |
| 生物谷 | 新药研发 | bioon.com |
| 医药经济报 | 商业动态 | yyjjb.com |

### 英文源

| 名称 | 类别 | URL |
|------|------|-----|
| FiercePharma | 综合 | fiercepharma.com |
| BioPharma Dive | 新药研发 | biopharmadive.com |
| Endpoints News | 新药研发 | endpts.com |
| STAT News | 综合 | statnews.com |
| FDA News | 监管审批 | fda.gov |

### 添加新源

在 `src/config.py` 中添加：

```python
RSSSource(
    name="新源名称",
    url="https://example.com/rss",
    language="zh",  # 或 "en"
    category="新药研发",  # 见CATEGORIES
    enabled=True
)
```

## 新闻分类

| 类别 | 英文 | 关键词示例 |
|------|------|-----------|
| 新药研发 | Drug R&D | 研发、管线、靶点、IND |
| 临床试验 | Clinical Trials | I期、II期、III期、疗效 |
| 监管审批 | Regulatory | FDA、NMPA、获批、上市 |
| 商业动态 | Business/M&A | 收购、并购、融资、IPO |
| 市场分析 | Market Analysis | 市场、销售、营收、预测 |
| 政策法规 | Policy | 医保、集采、政策、指南 |

## 主题预览

### Minimal（极简风格）
- 白色背景，优雅排版
- 适合专业阅读和打印

### Pharma Blue（医药蓝）
- 专业蓝色调，医学感
- 卡片式布局，信息清晰

### Warm（温暖风格）
- 柔和暖色调，护眼
- 衬线字体，适合长时间阅读

## 技术栈

- **Python 3.11+**
- **feedparser** - RSS解析
- **requests** - HTTP请求
- **jinja2** - 模板引擎
- **python-dateutil** - 日期处理
- **anthropic** - Claude API（可选）

## License

MIT License
