#!/bin/bash
# HR Intelligence Hub - 毎日ダッシュボード更新スクリプト
# cron 設定例（毎朝8時に自動実行）:
#   0 8 * * * /path/to/your/project/run.sh >> /path/to/your/project/run.log 2>&1

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] HR Intelligence Hub 更新開始"

# 依存パッケージ確認（初回のみインストール）
python3 -c "import feedparser" 2>/dev/null || pip3 install -q feedparser

# AI要約を使う場合は ANTHROPIC_API_KEY を設定して --ai フラグを追加
# export ANTHROPIC_API_KEY="sk-ant-..."
# python3 hr_hub.py --ai --output index.html

# 通常実行（AI なし・完全無料）
python3 hr_hub.py --output index.html

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 完了: index.html を更新しました"

# 生成したHTMLをブラウザで開く（macOS / Linux 対応）
if [[ "$OSTYPE" == "darwin"* ]]; then
    open index.html
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open index.html 2>/dev/null || echo "ブラウザで index.html を手動で開いてください"
fi
