#!/bin/bash
# 지자체·기관 AI/숏폼 공모전 카톡 브리핑 로컬 실행 래퍼 (crontab용)
# 사용: run_brief.sh [morning|afternoon|noon|evening]  (생략 시 현재 시각으로 자동 판별)
set -u

DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$DIR/logs"
mkdir -p "$LOG_DIR"

SLOT="${1:-}"
STAMP="$(date '+%Y-%m-%d_%H%M')"
LOG="$LOG_DIR/brief_${STAMP}_${SLOT:-auto}.log"

cd "$DIR"
if [ -n "$SLOT" ]; then
  /usr/bin/python3 -m market_brief.main --slot "$SLOT" >"$LOG" 2>&1
else
  /usr/bin/python3 -m market_brief.main >"$LOG" 2>&1
fi
RC=$?

# 30일 지난 로그 정리
find "$LOG_DIR" -name 'brief_*.log' -mtime +30 -delete 2>/dev/null

exit $RC
