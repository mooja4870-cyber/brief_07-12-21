# 📈 brief_07-12-21 — 한·미 증시 시황 카톡 브리핑

코스피·미국 증시 시황을 **555자 내외(설명형+개조식)** 로 요약해
매일 **07:00 / 12:00 / 21:00 (KST)** 카카오톡 '나에게 보내기'로 자동 발송합니다.

- 데이터: 네이버 금융 실시간 API (무지연)
- 요약: Google Gemini (`gemini-2.5-flash-lite`)
- 발송: 카카오 메모 API (200자 제한 → 3말풍선 분할)
- 스케줄: **로컬 Mac crontab** (정시 발송 — `run_brief.sh`)
  - GitHub Actions cron 은 1~4시간 지연·누락이 잦아 v0.1.3 에서 제거. 수동 실행(workflow_dispatch) 백업만 유지

자세한 설정은 [market_brief/README.md](market_brief/README.md) 참고.

## 로컬 스케줄 (crontab)
```
0 7  * * * /bin/bash "/Users/l/project/brief_07-12-21/run_brief.sh" morning
0 12 * * * /bin/bash "/Users/l/project/brief_07-12-21/run_brief.sh" noon
0 21 * * * /bin/bash "/Users/l/project/brief_07-12-21/run_brief.sh" evening
```
실행 로그는 `logs/` 에 저장(30일 보관). 환경변수는 프로젝트 루트 `.env` 사용.

## GitHub Secrets (수동 백업 실행용)
저장소 Settings → Secrets and variables → Actions 에 등록:
- `GEMINI_API_KEY`
- `KAKAO_REST_API_KEY`
- `KAKAO_REFRESH_TOKEN`
