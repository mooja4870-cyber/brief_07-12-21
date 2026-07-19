# 🏆 brief_AI_related — 지자체·기관 AI/숏폼/홍보 공모전 카톡 브리핑

지자체 및 공공기관의 **AI 숏폼 제작, 홍보 공모전, 지역 체류(살아보기 등) 지원사업** 최신 공고 핵심 요약과 원본 링크를
매일 **07:00 / 14:00 (KST)** 카카오톡 '나에게 보내기'로 자동 발송합니다.

- 데이터: 웰촌(welchon.com) 공모전 게시판 + 위비티(wevity.com) 정부/공공기관/영상·AI 카테고리
- 요약: Google Gemini (`gemini-2.5-flash-lite`) (핵심 상금·혜택·마감일·접수조건 요약)
- 발송: 카카오 메모 API (200자 제한 맞춤 5개 블록 분할 발송, 원본 URL 노란색 버튼 자동 링크)
- 스케줄: **로컬 Mac crontab** (정시 발송 — `run_brief.sh`)

자세한 설정은 [market_brief/README.md](market_brief/README.md) 참고.

## 로컬 스케줄 (crontab)
```
0 7  * * * /bin/bash "/Users/l/project/brief_AI_related/run_brief.sh" morning
0 14 * * * /bin/bash "/Users/l/project/brief_AI_related/run_brief.sh" afternoon
```
실행 로그는 `logs/` 에 저장(30일 보관). 환경변수는 프로젝트 루트 `.env` 사용.

## GitHub Secrets (수동 백업 실행용)
저장소 Settings → Secrets and variables → Actions 에 등록:
- `GEMINI_API_KEY`
- `KAKAO_REST_API_KEY`
- `KAKAO_REFRESH_TOKEN`
