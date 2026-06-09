# 📈 brief_07-12-21 — 한·미 증시 시황 카톡 브리핑

코스피·미국 증시 시황을 **555자 내외(설명형+개조식)** 로 요약해
매일 **07:00 / 12:00 / 21:00 (KST)** 카카오톡 '나에게 보내기'로 자동 발송합니다.

- 데이터: 네이버 금융 실시간 API (무지연)
- 요약: Google Gemini (`gemini-2.5-flash-lite`)
- 발송: 카카오 메모 API (200자 제한 → 3말풍선 분할)
- 스케줄: GitHub Actions cron

자세한 설정은 [market_brief/README.md](market_brief/README.md) 참고.

## GitHub Secrets (필수)
저장소 Settings → Secrets and variables → Actions 에 등록:
- `GEMINI_API_KEY`
- `KAKAO_REST_API_KEY`
- `KAKAO_REFRESH_TOKEN`
