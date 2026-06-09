"""
카카오톡 '나에게 보내기'(메모 API) 클라이언트.

- refresh_token 으로 access_token 을 갱신한 뒤
- 기본 텍스트 템플릿으로 나와의 채팅방에 메시지를 발송합니다.
- 한 말풍선 200자 제한 때문에 블록 단위로 여러 번 발송합니다.

참고: https://developers.kakao.com/docs/latest/ko/kakaotalk-message/rest-api
"""
from __future__ import annotations

import json
import time

import requests

from . import config

_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
_MEMO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

# 말풍선 버튼이 누르면 열리는 링크(시세 확인용)
_LINK = {
    "web_url": "https://finance.naver.com/sise/",
    "mobile_web_url": "https://m.stock.naver.com",
}


def _refresh_access_token() -> str:
    """refresh_token 으로 새 access_token 발급."""
    data = {
        "grant_type": "refresh_token",
        "client_id": config.kakao_rest_api_key(),
        "refresh_token": config.kakao_refresh_token(),
    }
    secret = config.kakao_client_secret()
    if secret:
        data["client_secret"] = secret
    resp = requests.post(_TOKEN_URL, data=data, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"access_token 발급 실패: {data}")
    # refresh_token 이 새로 내려오면(갱신 임박 시) 안내
    if data.get("refresh_token"):
        print(
            "ℹ️  새 refresh_token 이 발급되었습니다. "
            "GitHub Secret(KAKAO_REFRESH_TOKEN)을 아래 값으로 갱신하세요:\n"
            f"   {data['refresh_token']}"
        )
    return token


def _send_text(access_token: str, text: str) -> None:
    template = {
        "object_type": "text",
        "text": text,
        "link": _LINK,
        "button_title": "시세 보기",
    }
    resp = requests.post(
        _MEMO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"카카오 발송 실패 [{resp.status_code}]: {resp.text}")


def send_blocks(blocks: list[str]) -> None:
    """블록들을 순서대로 나에게 보내기로 발송."""
    if config.DRY_RUN:
        print("=== DRY_RUN: 실제 발송 대신 출력 ===")
        for i, b in enumerate(blocks, 1):
            print(f"\n--- 말풍선 {i}/{len(blocks)} ({len(b)}자) ---\n{b}")
        return

    token = _refresh_access_token()
    for i, b in enumerate(blocks, 1):
        _send_text(token, b)
        print(f"  ✓ 말풍선 {i}/{len(blocks)} 발송 ({len(b)}자)")
        if i < len(blocks):
            time.sleep(1)  # 순서 보장 + 레이트리밋 여유
