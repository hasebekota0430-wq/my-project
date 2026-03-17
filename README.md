# 🧠 HR Intelligence Hub

人事・HR領域の国内外情報を自動収集・まとめるダッシュボード。

## 特徴

- **9カテゴリ** 採用 / 教育研修・育成 / 人事制度 / タレントマネジメント / 組織開発 / 労務・法改正 / HRTech / 人的資本経営 / DE&I
- **国内外ソース** 日本語7ソース + 英語7ソース（計14フィード）
- **ダッシュボード型UI** カテゴリ別カード + 重要度ランキング + デイリーサマリー
- **完全無料** Claude API なしでも動作（RSSの要約をそのまま表示）
- **HTMLファイル1枚** ローカルでそのまま開けるスタティックHTML

## セットアップ

```bash
# 依存パッケージをインストール（feedparser のみで動作可）
pip install feedparser

# AI要約も使う場合（任意）
pip install anthropic
```

## 使い方

```bash
# 基本（無料・AI なし）
python3 hr_hub.py

# AI サマリー付き（Claude API キーが必要）
export ANTHROPIC_API_KEY="sk-ant-..."
python3 hr_hub.py --ai

# 出力先を指定
python3 hr_hub.py --output dashboard.html
```

生成された `index.html` をブラウザで開くだけ。

## 毎日自動更新（cron）

```bash
chmod +x run.sh

# crontab に登録（毎朝8時）
crontab -e
# 以下を追記:
# 0 8 * * * /path/to/hr-intelligence-hub/run.sh >> /path/to/run.log 2>&1
```

## 情報ソース

| ソース | 言語 |
|--------|------|
| HR NOTE | 日本語 |
| SmartHR Mag | 日本語 |
| SELECK | 日本語 |
| 日本の人事部 | 日本語 |
| HRpro | 日本語 |
| Books&Apps | 日本語 |
| Works研究所 | 日本語 |
| SHRM | 英語 |
| HR Dive | 英語 |
| HR Executive | 英語 |
| AIHR | 英語 |
| HR Bartender | 英語 |
| Josh Bersin | 英語 |

## カスタマイズ

`hr_hub.py` 内の設定で調整可能：

- `RSS_FEEDS` … フィードの追加・削除
- `CATEGORIES` … カテゴリキーワードの調整
- `MAX_ITEMS_PER_CAT` … カテゴリごとの表示件数（デフォルト6）
- `TOP_RANKING_COUNT` … ランキング表示件数（デフォルト10）
- `MAX_DAYS_OLD` … 何日前までの記事を収集するか（デフォルト7日）
