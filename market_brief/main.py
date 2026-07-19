"""
엔트리포인트: 공모전/지원사업 데이터 수집 → 요약 생성 → 카카오 발송.

사용:
  python -m market_brief.main               # 현재 한국시각으로 슬롯 자동 판별
  python -m market_brief.main --slot morning
  python -m market_brief.main --slot afternoon
  DRY_RUN=1 python -m market_brief.main --slot morning  # 발송 없이 미리보기
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from . import kakao_client, market_data, summarizer

KST = timezone(timedelta(hours=9))


def detect_slot(hour: int) -> str:
    """한국시각 hour(0~23)로 슬롯 판별. 07:00 및 14:00 기준."""
    if hour < 11:
        return "morning"    # 07:00 발송
    return "afternoon"      # 14:00 발송


def run(slot: str | None = None) -> None:
    now = datetime.now(KST)
    if slot is None:
        slot = detect_slot(now.hour)
    date_str = now.strftime("%Y-%m-%d (%a) %H:%M KST")

    print(f"▶ 지자체/기관 공모전 브리핑 시작 | slot={slot} | {date_str}")

    print("· 공모전 및 지원사업 데이터 수집 중…")
    items = market_data.collect()
    if not items:
        raise RuntimeError("공모전/지원사업 데이터를 한 건도 수집하지 못했습니다. 발송을 중단합니다.")
    table = market_data.to_table(items)
    print(table)

    print("· 요약 생성 중…")
    blocks = summarizer.generate(slot, table, date_str)
    total = sum(len(b) for b in blocks)
    print(f"· {len(blocks)}개 블록 / 총 {total}자 생성")

    print("· 카카오 발송 중…")
    kakao_client.send_blocks(blocks)
    print("✅ 완료")


def main() -> None:
    p = argparse.ArgumentParser(description="지자체·공공기관 AI·숏폼 공모전 및 체류 지원사업 카톡 브리핑")
    p.add_argument(
        "--slot",
        choices=["morning", "afternoon", "noon", "evening"],
        default=None,
        help="발송 시점(미지정 시 현재 한국시각으로 자동 판별)",
    )
    args = p.parse_args()
    run(args.slot)


if __name__ == "__main__":
    main()

