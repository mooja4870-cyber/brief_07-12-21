"""
카카오톡 '나에게 보내기' API 클라이언트.

카카오 REST API 키와 Refresh Token으로 Access Token을 발급/갱신하고,
생성된 요약 블록을 1초 간격으로 연속 발송합니다.
"""
from __future__ import annotations

import json
import re
import time
import requests

from . import config

_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
_SEND_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

# 말풍선 기본 링크 (지자체/웰촌 공모전 포털)
_LINK = {
    "web_url": "https://www.welchon.com/web/lay1/program/S1T31C447/eventNewList.do?menuIdx=&cIdx=evpr",
    "mobile_web_url": "https://www.welchon.com/web/lay1/program/S1T31C447/eventNewList.do?menuIdx=&cIdx=evpr",
}


def _refresh_access_token() -> str:
    """Refresh token으로 새 Access token 발급."""
    payload = {
        "grant_type": "refresh_token",
        "client_id": config.kakao_rest_api_key(),
        "refresh_token": config.kakao_refresh_token(),
    }
    r = requests.post(_TOKEN_URL, data=payload, timeout=10)
    r.raise_for_status()
    data = r.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"Access token 갱신 응답 오류: {data}")
    return token


def _send_text(access_token: str, text: str, custom_url: str | None = None) -> None:
    """단일 텍스트 말풍선을 '나에게 보내기'로 전송. 텍스트 내 링크가 있으면 버튼 링크로 자동 지정."""
    url_match = re.search(r"(https?://[^\s)\]]+)", text)
    if custom_url:
        link = {"web_url": custom_url, "mobile_web_url": custom_url}
        button_title = "원본 공고 보기"
    elif url_match:
        found_url = url_match.group(1).strip()
        link = {"web_url": found_url, "mobile_web_url": found_url}
        button_title = "원본 공고 보기"
    else:
        link = _LINK
        button_title = "공모전 포털 보기"

    template = {
        "object_type": "text",
        "text": text,
        "link": link,
        "button_title": button_title,
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    r = requests.post(
        _SEND_URL,
        headers=headers,
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=10,
    )
    if r.status_code != 200:
        raise RuntimeError(f"카카오 전송 실패 [HTTP {r.status_code}]: {r.text}")


def send_blocks(blocks: list[str]) -> None:
    """발급받은 토큰으로 N개의 말풍선을 순차 전송. 200자 제한 사전 검증 포함."""
    if not blocks:
        print("  ! 전송할 블록이 없습니다.")
        return

    # 전송 전 검증
    for i, b in enumerate(blocks, start=1):
        if len(b) > 200:
            raise ValueError(
                f"블록 #{i}이 카카오 200자 제한을 초과({len(b)}자):\n{b}"
            )

    if config.DRY_RUN:
        print("=== DRY_RUN: 실제 발송 대신 출력 ===")
        for i, b in enumerate(blocks, 1):
            print(f"\n--- 말풍선 {i}/{len(blocks)} ({len(b)}자) ---\n{b}")
        return

    access_token = _refresh_access_token()
    for i, block in enumerate(blocks, start=1):
        try:
            _send_text(access_token, block)
            print(f"  ✓ 블록 #{i}/{len(blocks)} 전송 완료 ({len(block)}자)")
        except Exception as e:
            print(f"  ! 블록 #{i} 전송 중 오류: {e}")
            raise
        if i < len(blocks):
            time.sleep(1.0)  # Rate limit 보호 및 순서 보장
