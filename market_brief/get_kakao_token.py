"""
카카오 refresh_token 발급 도우미 (최초 1회만 로컬에서 실행).

사전 준비(카카오 개발자 콘솔, https://developers.kakao.com):
  1) 내 애플리케이션 → 애플리케이션 추가하기
  2) [앱 키]의 'REST API 키' 복사  → 아래 REST_API_KEY 에 입력
  3) [카카오 로그인] 활성화 ON
  4) [카카오 로그인] → Redirect URI 에  https://localhost  추가
  5) [카카오 로그인] → 동의항목 → '카카오톡 메시지 전송(talk_message)' 사용 ON

실행:
  python -m market_brief.get_kakao_token
  → 안내된 URL을 브라우저에서 열고 동의 → 이동된 주소창의 code=... 값을 붙여넣기
  → 출력된 refresh_token 을 GitHub Secret(KAKAO_REFRESH_TOKEN)에 저장
"""
import sys
import requests

REST_API_KEY = ""     # ← 여기에 REST API 키를 붙여넣으세요 (비우면 실행 시 입력받음)
CLIENT_SECRET = ""    # ← 클라이언트 시크릿(있으면). 비우면 실행 시 입력받음
REDIRECT_URI = "https://localhost"


def main() -> None:
    key = REST_API_KEY or input("REST API 키를 입력하세요: ").strip()
    if not key:
        print("REST API 키가 필요합니다.")
        sys.exit(1)
    secret = CLIENT_SECRET or input(
        "클라이언트 시크릿을 입력하세요 (없으면 그냥 Enter): "
    ).strip()

    auth_url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={key}&redirect_uri={REDIRECT_URI}"
        "&response_type=code&scope=talk_message"
    )
    print("\n[1] 아래 URL을 브라우저에서 열고 '동의하고 계속하기'를 누르세요:\n")
    print(auth_url)
    print(
        "\n[2] 동의 후 주소창이 'https://localhost/?code=XXXXX' 로 바뀝니다.\n"
        "    (페이지는 안 열려도 정상) 주소창의 code 값(XXXXX)만 복사하세요.\n"
    )
    code = input("code 값을 붙여넣으세요: ").strip()

    token_data = {
        "grant_type": "authorization_code",
        "client_id": key,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }
    if secret:
        token_data["client_secret"] = secret
    resp = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data=token_data,
        timeout=15,
    )
    data = resp.json()
    if "refresh_token" not in data:
        print(f"\n❌ 발급 실패: {data}")
        sys.exit(1)

    print("\n✅ 발급 성공! 아래 값들을 GitHub Secrets 에 저장하세요:\n")
    print(f"KAKAO_REST_API_KEY   = {key}")
    print(f"KAKAO_REFRESH_TOKEN  = {data['refresh_token']}")
    if secret:
        print(f"KAKAO_CLIENT_SECRET  = {secret}")
    print(f"\n(참고) access_token  = {data.get('access_token', '')[:12]}… (자동 갱신되므로 저장 불필요)")
    print(f"(참고) refresh_token 만료: 약 {data.get('refresh_token_expires_in', 0)//86400}일 후 (사용 시 자동 연장)")


if __name__ == "__main__":
    main()
