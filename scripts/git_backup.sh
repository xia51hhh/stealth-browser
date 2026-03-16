#!/bin/bash
# stealth-browser 定时备份脚本
# 每30分钟自动提交并推送到 git@github.com:xia51hhh/stealth-browser.git

set -e

REPO_DIR="/home/toe2/stealth-browser"
LOG_FILE="$REPO_DIR/logs/git_backup.log"

mkdir -p "$REPO_DIR/logs"

cd "$REPO_DIR"

# 检查是否有变更
if git diff --quiet && git diff --staged --quiet && [ -z "$(git status --porcelain)" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 无变更，跳过" >> "$LOG_FILE"
    exit 0
fi

# 提交并推送
git add .
COMMIT_MSG="auto backup: $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$COMMIT_MSG" >> "$LOG_FILE" 2>&1
git push origin master >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 备份成功: $COMMIT_MSG" >> "$LOG_FILE"
