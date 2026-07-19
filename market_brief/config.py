"""
환경설정 로더.

GitHub Actions에서는 Secrets가 환경변수로 주입되고,
로컬에서는 .env 파일(있으면)에서 읽습니다.
"""
from __future__ import annotations

import os

try:
    from dotenv import load_dotenv  # type: ignore

    # market_brief/.env 또는 프로젝트 루트 .env 자동 탐색
    load_dotenv()
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass


def _require(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        raise RuntimeError(
            f"환경변수 {name} 가(이) 설정되지 않았습니다. "
            f"README의 '환경변수 설정'을 참고하세요."
        )
    return val


# Gemini (요약 생성)
def gemini_api_key() -> str:
    return _require("GEMINI_API_KEY")


# flash-lite 는 thinking 토큰을 쓰지 않아 JSON 출력이 잘리지 않고 무료 쿼터도 넉넉
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")

# Kakao (나에게 보내기)
def kakao_rest_api_key() -> str:
    return _require("KAKAO_REST_API_KEY")


def kakao_refresh_token() -> str:
    return _require("KAKAO_REFRESH_TOKEN")


def kakao_client_secret() -> str | None:
    """클라이언트 시크릿(설정돼 있으면 토큰 요청에 포함). 미설정이면 None."""
    return os.environ.get("KAKAO_CLIENT_SECRET", "").strip() or None


# 발송 끄기(테스트용): DRY_RUN=1 이면 카톡 발송 대신 콘솔 출력
DRY_RUN = os.environ.get("DRY_RUN", "").strip() in ("1", "true", "True")

# 카톡 알림 연결 웹 배포처 (d_airelatednews 앱 주소)
WEB_APP_URL = os.environ.get("WEB_APP_URL", "https://d-airelatednews-web.onrender.com")
