# 🏆 지자체·기관 AI/숏폼 공모전 카톡 브리핑 (market_brief)

지자체 및 공공기관의 **AI 숏폼 제작, 홍보 공모전, 지역 체류(살아보기 등) 지원사업** 최신 공고 핵심 요약과 원본 링크를
매일 정해진 시각에 **카카오톡 '나에게 보내기'** 로 자동 발송합니다.

- **데이터**: 웰촌(welchon.com) 공모전 게시판 + 위비티(wevity.com) 정부/공공기관 및 영상/UCC/AI 카테고리 실시간 크롤링
- **요약**: Google Gemini (핵심 상금·지원금·체류 혜택·참가 자격·마감 기한 요약)
- **발송**: 카카오 메모 API — 200자 제한 맞춤 **5개 말풍선 분할 발송 (말풍선 버튼 클릭 시 원본 URL 열림)**
- **스케줄**: 로컬 crontab 또는 GitHub Actions 백업, 하루 2회 (한국시각 07/14시)

| 시각(KST) | 슬롯 | 내용 |
|-----------|------|------|
| 07:00 | morning | 아침 공모전·지원사업 핵심 브리핑 (추천 공고 3선 + 원본 링크) |
| 14:00 | afternoon | 오후 마감 임박 및 추천 공모전 브리핑 (추천 공고 3선 + 원본 링크) |

---

## 설정 (최초 1회)

### 1. Gemini API 키
[Google AI Studio](https://aistudio.google.com/app/apikey) 에서 발급.

### 2. 카카오 앱 생성 + refresh token 발급
1. [카카오 개발자 콘솔](https://developers.kakao.com) → **내 애플리케이션 → 추가**
2. **앱 키**에서 `REST API 키` 복사
3. **카카오 로그인** 활성화 ON
4. **카카오 로그인 → Redirect URI** 에 `https://localhost` 추가
5. **카카오 로그인 → 동의항목** 에서 **카카오톡 메시지 전송(`talk_message`)** 사용 ON
6. 로컬에서 토큰 발급 도우미 실행:
   ```bash
   pip install -r market_brief/requirements.txt
   python -m market_brief.get_kakao_token
   ```
   안내대로 동의 후 `code` 를 붙여넣으면 `KAKAO_REST_API_KEY` 와 `KAKAO_REFRESH_TOKEN` 이 출력됩니다.

### 3. GitHub Secrets 등록 (클라우드 실행용)
저장소 **Settings → Secrets and variables → Actions → New repository secret** 에 3개 등록:

| Secret 이름 | 값 |
|-------------|----|
| `GEMINI_API_KEY` | 1번에서 발급한 키 |
| `KAKAO_REST_API_KEY` | 2번의 REST API 키 |
| `KAKAO_REFRESH_TOKEN` | 2번에서 발급한 refresh token |

등록하면 [`.github/workflows/market-brief.yml`](../.github/workflows/market-brief.yml) 이
설정된 시각에 자동 실행됩니다. **Actions 탭 → 워크플로 → Run workflow** 로 즉시 테스트도 가능합니다.

---

## 로컬에서 직접 실행 / 미리보기

```bash
# market_brief/.env 에 키 3개를 넣거나, 아래처럼 환경변수로 전달
export GEMINI_API_KEY=...
export KAKAO_REST_API_KEY=...
export KAKAO_REFRESH_TOKEN=...

# 실제 발송 없이 결과만 콘솔로 미리보기 (카톡 안 감)
DRY_RUN=1 python -m market_brief.main --slot evening

# 실제 발송
python -m market_brief.main --slot morning
```

`--slot` 을 생략하면 현재 한국시각으로 자동 판별합니다.

---

## 파일 구성
```
market_brief/
├── main.py            # 엔트리포인트 (수집→요약→발송)
├── market_data.py     # yfinance 시장 데이터 수집
├── summarizer.py      # Gemini 555자 3블록 요약
├── kakao_client.py    # 토큰 갱신 + 나에게 보내기
├── get_kakao_token.py # (1회용) refresh token 발급 도우미
├── config.py          # 환경변수 로더
└── requirements.txt
```

## 참고 / 주의
- 카카오 `refresh_token` 은 약 2개월 유효하나 사용 시 자동 연장됩니다. 갱신값이 내려오면
  실행 로그에 새 토큰이 출력되니 Secret 을 업데이트하세요.
- GitHub Actions cron 은 부하에 따라 **수 분~십수 분 지연**될 수 있습니다(무료 플랜 특성).
- 본 브리핑은 시황 해설이며 **투자 권유가 아닙니다.**
