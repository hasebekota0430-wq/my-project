#!/usr/bin/env python3
"""
HR Intelligence Hub
人事・HR領域の国内外情報を自動収集・要約するダッシュボード生成スクリプト

使い方:
    python hr_hub.py              # index.html を生成（Claude API なし）
    python hr_hub.py --ai         # Claude API で要約強化（ANTHROPIC_API_KEY 必要）
    python hr_hub.py --output custom.html
"""

import feedparser
import os
import sys
import re
import json
import html as html_module
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# ================================================================
# カテゴリ定義
# ================================================================
CATEGORIES = {
    "採用": {
        "en": "Recruitment",
        "icon": "🎯",
        "color": "#6366F1",
        "bg_gradient": "from-indigo-500 to-purple-600",
        "card_bg": "#F0F0FF",
        "keywords": ["採用", "リクルート", "求人", "内定", "selection", "recruitment", "hiring", "talent acquisition",
                     "candidate", "applicant", "onboarding", "オンボーディング"],
    },
    "教育研修・育成": {
        "en": "Learning & Development",
        "icon": "📚",
        "color": "#059669",
        "bg_gradient": "from-emerald-500 to-teal-600",
        "card_bg": "#ECFDF5",
        "keywords": ["研修", "育成", "教育", "スキル", "learning", "training", "development",
                     "upskilling", "reskilling", "elearning", "コーチング", "coaching", "mentoring"],
    },
    "人事制度": {
        "en": "HR Policy & Systems",
        "icon": "⚙️",
        "color": "#D97706",
        "bg_gradient": "from-amber-500 to-orange-600",
        "card_bg": "#FFFBEB",
        "keywords": ["人事制度", "評価制度", "給与", "報酬", "賃金", "昇格", "compensation",
                     "performance management", "benefits", "pay", "salary", "grading", "人事評価"],
    },
    "タレントマネジメント": {
        "en": "Talent Management",
        "icon": "⭐",
        "color": "#7C3AED",
        "bg_gradient": "from-violet-500 to-purple-700",
        "card_bg": "#F5F3FF",
        "keywords": ["タレント", "タレントマネジメント", "talent management", "succession planning",
                     "high potential", "hipo", "キャリア", "career development", "leadership pipeline"],
    },
    "組織開発": {
        "en": "Organization Development",
        "icon": "🏢",
        "color": "#0891B2",
        "bg_gradient": "from-cyan-500 to-sky-600",
        "card_bg": "#ECFEFF",
        "keywords": ["組織開発", "組織文化", "culture", "文化", "engagement", "エンゲージメント",
                     "organizational development", "change management", "チームビルディング", "team", "well-being"],
    },
    "労務・法改正": {
        "en": "Labor Law & Compliance",
        "icon": "⚖️",
        "color": "#DC2626",
        "bg_gradient": "from-red-500 to-rose-600",
        "card_bg": "#FEF2F2",
        "keywords": ["労務", "法改正", "労働法", "労働基準", "働き方改革", "時間外", "有給", "残業",
                     "labor law", "employment law", "compliance", "regulation", "legal", "minimum wage",
                     "最低賃金", "育児休業", "介護休業"],
    },
    "HRTech": {
        "en": "HR Technology",
        "icon": "💻",
        "color": "#0284C7",
        "bg_gradient": "from-blue-500 to-cyan-600",
        "card_bg": "#F0F9FF",
        "keywords": ["hrtech", "hr tech", "hris", "人工知能", "ai ", " ai", "machine learning",
                     "technology", "テクノロジー", "saas", "platform", "automation", "自動化",
                     "generative ai", "生成ai", "chatgpt", "llm", "デジタル"],
    },
    "人的資本経営": {
        "en": "Human Capital Management",
        "icon": "📊",
        "color": "#15803D",
        "bg_gradient": "from-green-600 to-emerald-700",
        "card_bg": "#F0FDF4",
        "keywords": ["人的資本", "人的資本経営", "human capital", "esg", "開示", "disclosure",
                     "workforce analytics", "roi", "人材投資", "非財務", "統合報告"],
    },
    "DE&I": {
        "en": "Diversity, Equity & Inclusion",
        "icon": "🌈",
        "color": "#BE185D",
        "bg_gradient": "from-pink-500 to-rose-600",
        "card_bg": "#FDF2F8",
        "keywords": ["dei", "de&i", "diversity", "inclusion", "equity", "ダイバーシティ",
                     "インクルージョン", "lgbtq", "gender", "ジェンダー", "女性活躍", "障害", "disability"],
    },
}

# ================================================================
# RSS フィードリスト（無料・公開フィード）
# ================================================================
RSS_FEEDS = [
    # --- 日本語ソース ---
    {"url": "https://hrnote.jp/feed/",              "lang": "ja", "source": "HR NOTE"},
    {"url": "https://mag.smarthr.jp/feed/",         "lang": "ja", "source": "SmartHR Mag"},
    {"url": "https://seleck.cc/feed",               "lang": "ja", "source": "SELECK"},
    {"url": "https://blog.tinect.jp/feed/",         "lang": "ja", "source": "Books&Apps"},
    {"url": "https://www.jinjibu.jp/rss/",          "lang": "ja", "source": "日本の人事部"},
    {"url": "https://www.hrpro.co.jp/rss/rss2.0.xml", "lang": "ja", "source": "HRpro"},
    {"url": "https://www.works-i.com/feeds/index.xml", "lang": "ja", "source": "Works研究所"},
    # --- 英語ソース ---
    {"url": "https://www.hrdive.com/feeds/news/",   "lang": "en", "source": "HR Dive"},
    {"url": "https://hrexecutive.com/feed/",        "lang": "en", "source": "HR Executive"},
    {"url": "https://www.aihr.com/blog/feed/",      "lang": "en", "source": "AIHR"},
    {"url": "https://www.hrbartender.com/feed/",    "lang": "en", "source": "HR Bartender"},
    {"url": "https://joshbersin.com/feed/",         "lang": "en", "source": "Josh Bersin"},
    {"url": "https://www.shrm.org/rss/pages/rss.aspx?feed=HR-News", "lang": "en", "source": "SHRM"},
    {"url": "https://hrtech.sg/feed/",              "lang": "en", "source": "HRTech Singapore"},
]

MAX_ITEMS_PER_FEED = 10   # フィードあたり最大取得件数
MAX_DAYS_OLD      = 7     # 何日前までの記事を取得するか
MAX_ITEMS_PER_CAT = 6     # カテゴリカードあたりの表示件数
TOP_RANKING_COUNT = 10    # ランキング表示件数


# ================================================================
# データ取得・分類
# ================================================================
def fetch_all_feeds() -> List[Dict]:
    """全フィードからアイテムを取得"""
    all_items: List[Dict] = []
    cutoff = datetime.utcnow() - timedelta(days=MAX_DAYS_OLD)

    for feed_cfg in RSS_FEEDS:
        try:
            print(f"  Fetching: {feed_cfg['source']} ...", end=" ", flush=True)
            d = feedparser.parse(feed_cfg["url"])
            count = 0
            for entry in d.entries[:MAX_ITEMS_PER_FEED]:
                # 日付パース
                pub = None
                for attr in ("published_parsed", "updated_parsed", "created_parsed"):
                    if hasattr(entry, attr) and getattr(entry, attr):
                        import time
                        pub = datetime.utcfromtimestamp(time.mktime(getattr(entry, attr)))
                        break
                if pub and pub < cutoff:
                    continue

                title = getattr(entry, "title", "")
                link  = getattr(entry, "link",  "")
                # summary: RSS の description / summary を利用
                summary_raw = (getattr(entry, "summary", "") or
                               getattr(entry, "description", "") or "")
                # HTMLタグ除去
                summary = re.sub(r"<[^>]+>", " ", summary_raw)
                summary = re.sub(r"\s+", " ", summary).strip()[:300]

                if not title or not link:
                    continue

                all_items.append({
                    "title":    html_module.escape(title),
                    "link":     link,
                    "summary":  html_module.escape(summary),
                    "source":   feed_cfg["source"],
                    "lang":     feed_cfg["lang"],
                    "pub":      pub.strftime("%Y-%m-%d") if pub else "",
                    "category": None,
                    "score":    0,
                })
                count += 1
            print(f"✓ {count} items")
        except Exception as e:
            print(f"✗ error: {e}")

    print(f"  Total: {len(all_items)} items fetched")
    return all_items


def categorize_item(item: Dict) -> str:
    """キーワードマッチで記事をカテゴリ分類"""
    text = (item["title"] + " " + item["summary"]).lower()
    scores = {}
    for cat_name, cat in CATEGORIES.items():
        s = sum(1 for kw in cat["keywords"] if kw.lower() in text)
        if s > 0:
            scores[cat_name] = s
    if scores:
        return max(scores, key=lambda k: scores[k])
    return "HRTech"  # デフォルト


def assign_categories(items: List[Dict]) -> List[Dict]:
    """全アイテムにカテゴリを付与"""
    for item in items:
        item["category"] = categorize_item(item)
    return items


def score_importance(items: List[Dict]) -> List[Dict]:
    """簡易重要度スコア（ソースの権威度 + 最新度）"""
    source_weight = {
        "Josh Bersin":   10,
        "SHRM":          9,
        "HR Dive":       8,
        "HR Executive":  7,
        "日本の人事部":   8,
        "HRpro":         7,
        "HR NOTE":       7,
        "SmartHR Mag":   6,
        "Works研究所":   8,
        "AIHR":          7,
    }
    today = datetime.utcnow().date()
    for item in items:
        base = source_weight.get(item["source"], 5)
        if item["pub"]:
            try:
                delta = (today - date.fromisoformat(item["pub"])).days
                recency = max(0, MAX_DAYS_OLD - delta)
            except Exception:
                recency = 0
        else:
            recency = 0
        item["score"] = base + recency
    return items


# ================================================================
# AI 要約（Claude API オプション）
# ================================================================
def enhance_with_ai(items: List[Dict]) -> Dict:
    """Claude API でデイリーサマリー生成 & 要約強化"""
    if not HAS_ANTHROPIC:
        print("  anthropic パッケージが未インストールです。pip install anthropic でインストールしてください。")
        return {"daily_summary": "", "highlights": []}

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("  ANTHROPIC_API_KEY が未設定です。AI 要約をスキップします。")
        return {"daily_summary": "", "highlights": []}

    client = anthropic.Anthropic(api_key=api_key)
    today_str = datetime.now().strftime("%Y年%m月%d日")

    # Top20件のタイトルをまとめてサマリー生成
    top_items = sorted(items, key=lambda x: x["score"], reverse=True)[:20]
    titles_text = "\n".join(
        f"- [{item['source']}] {html_module.unescape(item['title'])}"
        for item in top_items
    )

    prompt = f"""あなたは人事・HR領域の専門アナリストです。
本日（{today_str}）収集された国内外のHR情報のうち、以下の主要記事タイトルをもとに：

1. 今日のHRトレンド全体サマリー（3〜4文、日本語）
2. 特に注目すべきトピック3点（各1文）

を出力してください。出力形式はJSONで：
{{"summary": "...", "highlights": ["...", "...", "..."]}}

記事一覧:
{titles_text}
"""

    try:
        print("  AI サマリー生成中 ...", end=" ", flush=True)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        # JSONブロック抽出
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            data = json.loads(m.group())
            print("✓")
            return {
                "daily_summary": data.get("summary", ""),
                "highlights":    data.get("highlights", []),
            }
    except Exception as e:
        print(f"✗ error: {e}")

    return {"daily_summary": "", "highlights": []}


# ================================================================
# HTML 生成
# ================================================================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HR Intelligence Hub</title>
<style>
/* ===== Reset & Base ===== */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #0F172A;
  --surface: #1E293B;
  --surface2: #263347;
  --border: #334155;
  --text: #F1F5F9;
  --text2: #94A3B8;
  --accent: #6366F1;
  --accent2: #818CF8;
  font-size: 15px;
}
body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Hiragino Sans', 'Noto Sans JP', 'Segoe UI', sans-serif;
  line-height: 1.6;
  min-height: 100vh;
}

/* ===== Header ===== */
.site-header {
  background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
  border-bottom: 1px solid var(--border);
  padding: 0 24px;
  position: sticky; top: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  height: 60px;
}
.logo { display: flex; align-items: center; gap: 10px; }
.logo-icon { font-size: 22px; }
.logo-text { font-size: 1.1rem; font-weight: 700; background: linear-gradient(135deg, #818CF8, #C084FC); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.header-meta { font-size: 0.78rem; color: var(--text2); }
.header-badge { background: var(--accent); color: #fff; font-size: 0.65rem; font-weight: 700; padding: 2px 8px; border-radius: 20px; margin-left: 10px; }

/* ===== Main Layout ===== */
.main { max-width: 1400px; margin: 0 auto; padding: 28px 20px 60px; }

/* ===== Today's Summary ===== */
.today-summary {
  background: linear-gradient(135deg, #1E293B 0%, #1a2744 100%);
  border: 1px solid #4F46E5;
  border-radius: 16px;
  padding: 24px 28px;
  margin-bottom: 32px;
  position: relative;
  overflow: hidden;
}
.today-summary::before {
  content: "";
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, #6366F1, #8B5CF6, #EC4899, #06B6D4);
}
.summary-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.summary-icon { font-size: 1.4rem; }
.summary-title { font-size: 1rem; font-weight: 700; color: var(--accent2); text-transform: uppercase; letter-spacing: 0.05em; }
.summary-date { font-size: 0.78rem; color: var(--text2); margin-left: auto; }
.summary-text { font-size: 0.93rem; color: #CBD5E1; line-height: 1.8; margin-bottom: 16px; }
.highlights { display: flex; flex-wrap: wrap; gap: 10px; }
.highlight-chip {
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.35);
  color: #A5B4FC;
  font-size: 0.78rem;
  padding: 5px 12px;
  border-radius: 20px;
}
.highlight-chip::before { content: "✦ "; }

/* ===== Section title ===== */
.section-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text2);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 8px;
}
.section-title::before { content: ""; display: block; width: 3px; height: 14px; background: var(--accent); border-radius: 2px; }

/* ===== Ranking ===== */
.ranking-section { margin-bottom: 36px; }
.ranking-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 10px; }
.rank-item {
  display: flex; align-items: flex-start; gap: 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
  transition: border-color 0.2s, transform 0.15s;
  text-decoration: none;
  color: inherit;
}
.rank-item:hover { border-color: var(--accent2); transform: translateY(-1px); }
.rank-num {
  font-size: 1rem; font-weight: 800;
  min-width: 26px; text-align: center; padding-top: 1px;
}
.rank-num.top1 { color: #F59E0B; }
.rank-num.top2 { color: #94A3B8; }
.rank-num.top3 { color: #CD7F32; }
.rank-num.other { color: var(--text2); }
.rank-body { flex: 1; min-width: 0; }
.rank-title { font-size: 0.85rem; font-weight: 600; line-height: 1.4; margin-bottom: 4px; }
.rank-meta { display: flex; align-items: center; gap: 8px; }
.rank-source { font-size: 0.7rem; color: var(--text2); }
.rank-cat-badge { font-size: 0.65rem; padding: 1px 7px; border-radius: 10px; font-weight: 600; }

/* ===== Category Grid ===== */
.categories-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 20px; margin-bottom: 40px; }

.cat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
  transition: box-shadow 0.2s;
}
.cat-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
.cat-header {
  padding: 14px 18px;
  display: flex; align-items: center; gap: 10px;
  border-bottom: 1px solid var(--border);
}
.cat-icon { font-size: 1.3rem; }
.cat-title-wrap { flex: 1; }
.cat-name { font-size: 0.95rem; font-weight: 700; }
.cat-en   { font-size: 0.68rem; color: var(--text2); margin-top: 1px; }
.cat-count { font-size: 0.7rem; color: var(--text2); background: var(--surface2); padding: 2px 8px; border-radius: 10px; }
.cat-articles { padding: 10px 14px; }
.article-item {
  padding: 10px 6px;
  border-bottom: 1px solid var(--border);
}
.article-item:last-child { border-bottom: none; }
.article-link {
  text-decoration: none; color: inherit;
  display: block;
}
.article-link:hover .article-title { color: var(--accent2); }
.article-title { font-size: 0.83rem; font-weight: 600; line-height: 1.4; margin-bottom: 4px; color: var(--text); }
.article-summary { font-size: 0.74rem; color: var(--text2); line-height: 1.55; margin-bottom: 6px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.article-meta { display: flex; align-items: center; gap: 6px; font-size: 0.68rem; color: #64748B; }
.lang-badge { background: rgba(100,116,139,0.2); padding: 1px 5px; border-radius: 4px; font-size: 0.62rem; }
.no-items { text-align: center; color: var(--text2); font-size: 0.8rem; padding: 24px 0; }

/* ===== Footer ===== */
.footer {
  text-align: center;
  color: var(--text2);
  font-size: 0.73rem;
  border-top: 1px solid var(--border);
  padding: 20px 0;
}
.footer a { color: var(--accent2); text-decoration: none; }

/* ===== Scrollbar ===== */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
</head>
<body>

<!-- Header -->
<header class="site-header">
  <div class="logo">
    <span class="logo-icon">🧠</span>
    <span class="logo-text">HR Intelligence Hub</span>
    <span class="header-badge">DAILY</span>
  </div>
  <div class="header-meta">生成日時: __GENERATED_AT__　|　記事数: __TOTAL_ITEMS__件　|　ソース: __SOURCE_COUNT__</div>
</header>

<main class="main">

  <!-- Today's Summary -->
  <section class="today-summary">
    <div class="summary-header">
      <span class="summary-icon">📰</span>
      <span class="summary-title">Today's HR Briefing</span>
      <span class="summary-date">__DATE__</span>
    </div>
    <p class="summary-text">__DAILY_SUMMARY__</p>
    <div class="highlights">__HIGHLIGHTS_HTML__</div>
  </section>

  <!-- Ranking -->
  <section class="ranking-section">
    <h2 class="section-title">🔥 重要度ランキング Top __RANK_COUNT__</h2>
    <div class="ranking-list">__RANKING_HTML__</div>
  </section>

  <!-- Category Cards -->
  <section class="categories-section">
    <h2 class="section-title">📂 カテゴリ別記事</h2>
    <div class="categories-grid">__CATEGORIES_HTML__</div>
  </section>

</main>

<footer class="footer">
  <p>HR Intelligence Hub &nbsp;|&nbsp; 自動収集・生成 &nbsp;|&nbsp; __FOOTER_DATE__</p>
</footer>
</body>
</html>
"""


def build_html(items: List[Dict], ai_data: Dict) -> str:
    now = datetime.now()
    today_str = now.strftime("%Y年%m月%d日（%A）")
    gen_str   = now.strftime("%Y-%m-%d %H:%M")

    # --- Daily Summary ---
    daily_summary = ai_data.get("daily_summary", "")
    if not daily_summary:
        top_sources = list(dict.fromkeys(i["source"] for i in sorted(items, key=lambda x: x["score"], reverse=True)[:5]))
        daily_summary = (
            f"本日は {len(items)} 件の人事・HR関連情報を {len(RSS_FEEDS)} ソースから収集しました。"
            f"主なソース：{', '.join(top_sources[:4])} など。"
            f"各カテゴリの最新動向をカード形式でご確認ください。"
            f"AI要約を有効にするには <code>--ai</code> フラグと <code>ANTHROPIC_API_KEY</code> を設定してください。"
        )

    highlights = ai_data.get("highlights", [])
    if not highlights:
        # RSS タイトルから自動ハイライト
        top3 = sorted(items, key=lambda x: x["score"], reverse=True)[:3]
        highlights = [html_module.unescape(i["title"])[:50] + "…" for i in top3]

    highlights_html = "".join(
        f'<span class="highlight-chip">{html_module.escape(h)}</span>' for h in highlights
    )

    # --- Ranking ---
    ranked = sorted(items, key=lambda x: x["score"], reverse=True)[:TOP_RANKING_COUNT]
    ranking_parts = []
    for idx, item in enumerate(ranked, 1):
        cat_info = CATEGORIES.get(item["category"], CATEGORIES["HRTech"])
        num_class = {1: "top1", 2: "top2", 3: "top3"}.get(idx, "other")
        ranking_parts.append(f"""
      <a class="rank-item" href="{item['link']}" target="_blank" rel="noopener">
        <span class="rank-num {num_class}">#{idx}</span>
        <div class="rank-body">
          <div class="rank-title">{item['title']}</div>
          <div class="rank-meta">
            <span class="rank-source">{item['source']}</span>
            <span class="rank-cat-badge" style="background:{cat_info['color']}22;color:{cat_info['color']};border:1px solid {cat_info['color']}44">
              {cat_info['icon']} {item['category']}
            </span>
            {f"<span class='rank-source'>{item['pub']}</span>" if item['pub'] else ""}
          </div>
        </div>
      </a>""")

    # --- Category Cards ---
    cat_parts = []
    for cat_name, cat_info in CATEGORIES.items():
        cat_items = [i for i in items if i["category"] == cat_name]
        cat_items_sorted = sorted(cat_items, key=lambda x: x["score"], reverse=True)[:MAX_ITEMS_PER_CAT]

        articles_html = ""
        if cat_items_sorted:
            for art in cat_items_sorted:
                lang_badge = '<span class="lang-badge">EN</span>' if art["lang"] == "en" else '<span class="lang-badge">JA</span>'
                summary_text = art["summary"] if art["summary"] else "（要約なし）"
                articles_html += f"""
          <div class="article-item">
            <a class="article-link" href="{art['link']}" target="_blank" rel="noopener">
              <div class="article-title">{art['title']}</div>
              <div class="article-summary">{summary_text}</div>
              <div class="article-meta">
                {lang_badge}
                <span>{art['source']}</span>
                {f"<span>{art['pub']}</span>" if art['pub'] else ""}
              </div>
            </a>
          </div>"""
        else:
            articles_html = '<p class="no-items">記事が見つかりませんでした</p>'

        header_color = cat_info["color"]
        cat_parts.append(f"""
      <div class="cat-card" style="border-top: 3px solid {header_color}">
        <div class="cat-header">
          <span class="cat-icon">{cat_info['icon']}</span>
          <div class="cat-title-wrap">
            <div class="cat-name">{cat_name}</div>
            <div class="cat-en">{cat_info['en']}</div>
          </div>
          <span class="cat-count">{len(cat_items)}件</span>
        </div>
        <div class="cat-articles">{articles_html}</div>
      </div>""")

    unique_sources = len(set(i["source"] for i in items))

    html = HTML_TEMPLATE
    html = html.replace("__GENERATED_AT__", gen_str)
    html = html.replace("__TOTAL_ITEMS__",  str(len(items)))
    html = html.replace("__SOURCE_COUNT__", f"{unique_sources}ソース")
    html = html.replace("__DATE__",         today_str)
    html = html.replace("__DAILY_SUMMARY__", daily_summary)
    html = html.replace("__HIGHLIGHTS_HTML__", highlights_html)
    html = html.replace("__RANK_COUNT__",  str(TOP_RANKING_COUNT))
    html = html.replace("__RANKING_HTML__",  "".join(ranking_parts))
    html = html.replace("__CATEGORIES_HTML__", "".join(cat_parts))
    html = html.replace("__FOOTER_DATE__", gen_str)
    return html


# ================================================================
# エントリーポイント
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="HR Intelligence Hub Generator")
    parser.add_argument("--ai",     action="store_true", help="Claude API でAIサマリーを生成（ANTHROPIC_API_KEY 必要）")
    parser.add_argument("--output", default="index.html", help="出力HTMLファイル名 (default: index.html)")
    args = parser.parse_args()

    print("=" * 55)
    print("  HR Intelligence Hub  -  データ収集開始")
    print("=" * 55)

    # 1. フィード取得
    print("\n[1/4] RSS フィード取得中...")
    items = fetch_all_feeds()

    if not items:
        print("⚠️  記事が取得できませんでした。インターネット接続を確認してください。")
        sys.exit(1)

    # 2. カテゴリ分類
    print("\n[2/4] カテゴリ分類中...")
    items = assign_categories(items)
    for cat in CATEGORIES:
        c = sum(1 for i in items if i["category"] == cat)
        print(f"  {CATEGORIES[cat]['icon']} {cat}: {c}件")

    # 3. スコアリング
    print("\n[3/4] 重要度スコアリング中...")
    items = score_importance(items)

    # 4. AI 要約（オプション）
    ai_data: Dict = {"daily_summary": "", "highlights": []}
    if args.ai:
        print("\n[4/4] AI サマリー生成中...")
        ai_data = enhance_with_ai(items)
    else:
        print("\n[4/4] AI 要約スキップ（--ai フラグで有効化可）")

    # 5. HTML 生成
    print("\n[5/5] HTML ダッシュボード生成中...")
    html_content = build_html(items, ai_data)
    output_path = Path(args.output)
    output_path.write_text(html_content, encoding="utf-8")
    print(f"  ✓ 生成完了: {output_path.resolve()}")

    print("\n" + "=" * 55)
    print(f"  完了！ブラウザで {output_path} を開いてください。")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
