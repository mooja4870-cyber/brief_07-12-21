"""
엔트리포인트: 데이터 수집 → 요약 생성 → 카카오 발송.

사용:
  python -m market_brief.main            # 현재 한국시각으로 슬롯 자동 판별
  python -m market_brief.main --slot noon
  DRY_RUN=1 python -m market_brief.main --slot evening   # 발송 없이 미리보기
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from . import kakao_client, market_data, summarizer

KST = timezone(timedelta(hours=9))


def detect_slot(hour: int) -> str:
    """한국시각 hour(0~23)로 슬롯 판별. 가장 가까운 정시 기준."""
    if 5 <= hour < 10:
        return "morning"   # 07:00 발송
    if 10 <= hour < 16:
        return "noon"      # 12:00 발송
    return "evening"       # 21:00 발송


def run(slot: str | None = None) -> None:
    now = datetime.now(KST)
    if slot is None:
        slot = detect_slot(now.hour)
    date_str = now.strftime("%Y-%m-%d (%a) %H:%M KST")

    print(f"▶ 시황 브리핑 시작 | slot={slot} | {date_str}")

    print("· 시장 데이터 수집 중…")
    quotes = market_data.collect()
    if not quotes:
        raise RuntimeError("시장 데이터를 한 건도 수집하지 못했습니다. 발송을 중단합니다.")
    table = market_data.to_table(quotes)
    print(table)

    print("· 요약 생성 중…")
    blocks = summarizer.generate(slot, table, date_str)
    total = sum(len(b) for b in blocks)
    print(f"· {len(blocks)}개 블록 / 총 {total}자 생성")

    print("· 카카오 발송 중…")
    kakao_client.send_blocks(blocks)
    print("✅ 완료")


def main() -> None:
    p = argparse.ArgumentParser(description="한·미 증시 시황 카톡 브리핑")
    p.add_argument(
        "--slot",
        choices=["morning", "noon", "evening"],
        default=None,
        help="발송 시점(미지정 시 현재 한국시각으로 자동 판별)",
    )
    args = p.parse_args()
    run(args.slot)


if __name__ == "__main__":
    main()
