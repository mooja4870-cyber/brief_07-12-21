"""
Gemini 기반 시황 요약 생성기.

보내주신 예시(설명형 + 개조식)와 동일한 톤·구조로,
카카오 200자 제한에 맞춰 3개 블록(각 ≤190자)으로 나눠 반환합니다.

블록 구성:
  1) 헤더 + 핵심 요약(설명형)
  2) 주요 원인(개조식 불릿)
  3) 종합 판단 + 핵심 인사이트
"""
from __future__ import annotations

import json

from . import config

# 발송 시점별 관점
SLOT_FOCUS = {
    "morning": (
        "🌅 미국 증시 마감 종합 (07:00)",
        "밤사이 마감한 미국 증시(S&P500·나스닥·반도체) 결과를 중심으로 분석하고, "
        "이것이 오늘 개장할 한국 증시에 줄 영향과 전망을 덧붙이세요.",
    ),
    "noon": (
        "🏙️ 한국 오전장 시황 (12:00)",
        "오전장 코스피·코스닥 흐름과 외국인·기관 수급, 삼성전자·SK하이닉스 등 "
        "대형주 중심으로 오전 시황을 분석하세요.",
    ),
    "evening": (
        "🌃 한국 마감 + 미국 전망 (21:00)",
        "오늘 마감한 한국 증시를 정리하고, 곧 개장할 미국 증시 관전 포인트와 "
        "야간 변수(금리·환율·지정학)를 종합 전망하세요.",
    ),
}

_BLOCK_MAX = 190  # 카카오 텍스트 템플릿 200자 안전 마진


def _build_prompt(slot: str, header: str, focus: str, table: str, date_str: str) -> str:
    return f"""당신은 한국·미국 증시를 매일 브리핑하는 베테랑 시황 애널리스트입니다.
아래 실시간 시장 데이터를 바탕으로, 부부가 카카오톡으로 받아보는 시황 요약을 작성하세요.

[작성일] {date_str}
[브리핑 시점] {header}
[이 시점의 관점] {focus}

[실시간 시장 데이터]
{table}

[문체 — 매우 중요]
- 설명형 문장 + 개조식(불릿) 혼합. 아래 예시의 톤을 그대로 따르세요.
- 단정적 투자권유(매수/매도)는 금지. 시황 해설과 관점 제시에 집중.
- 과장 없이 차분하고 분석적인 어조. 한국어.
- 데이터가 일부 비어 있으면 있는 데이터로만 작성(없는 수치 지어내기 금지).

[예시 톤]
"오늘 코스피 급락은 단일 악재가 아니라 여러 요인이 동시에 작용한 결과로 분석됩니다. 가장 큰 원인은 …"
"* 미국 금리 인하 기대 후퇴 및 국채금리 상승"
"이번 하락은 국내 경제 자체의 악화보다 글로벌 충격·과열 해소 성격이 강합니다."

[출력 형식 — 반드시 JSON만 출력, 코드블록·설명 금지]
{{
  "block1": "헤더 한 줄 + 오늘 시장의 핵심 요약을 설명형 2~3문장으로. 주요 지수 등락률 포함.",
  "block2": "주요 원인/포인트를 '•' 불릿 3~5개로. 한 줄에 하나씩 줄바꿈(\\n).",
  "block3": "종합 판단 1~2문장 + 핵심 인사이트(앞으로 무엇이 변수인지) 1문장."
}}

[길이 규칙 — 반드시 준수]
- block1: 150~185자 / block2: 160~185자 / block3: 150~185자 로 충실히 채우세요.
- 세 블록 합계 480~555자. 너무 짧으면(합계 400자 미만) 분석·근거를 더 풍부하게 보강하세요.
- 각 블록 한글 기준 최대 {_BLOCK_MAX}자(초과 금지).
"""


def _coerce_json(text: str) -> dict:
    text = text.strip()
    if "```" in text:
        # ```json ... ``` 코드블록 제거
        parts = text.split("```")
        for p in parts:
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{"):
                text = p
                break
    return json.loads(text)


def _clip(s: str) -> str:
    s = (s or "").strip()
    if len(s) <= _BLOCK_MAX:
        return s
    # 마지막 문장/불릿 경계에서 자르기
    cut = s[:_BLOCK_MAX]
    for sep in ("\n", ". ", "다.", "요."):
        idx = cut.rfind(sep)
        if idx > _BLOCK_MAX * 0.6:
            return cut[: idx + len(sep)].strip()
    return cut.strip()


def generate(slot: str, table: str, date_str: str) -> list[str]:
    """slot('morning'|'noon'|'evening')에 맞춰 3개 블록 문자열을 반환."""
    header, focus = SLOT_FOCUS.get(slot, SLOT_FOCUS["evening"])

    import google.generativeai as genai

    genai.configure(api_key=config.gemini_api_key())
    model = genai.GenerativeModel(config.GEMINI_MODEL)

    prompt = _build_prompt(slot, header, focus, table, date_str)
    gen_cfg = {
        "temperature": 0.6,
        "max_output_tokens": 2048,
        # 코드블록 없이 유효한 JSON 만 받도록 강제
        "response_mime_type": "application/json",
    }

    data = None
    last_err = None
    for attempt in range(3):  # 드물게 깨진 응답이 와도 자가 복구
        try:
            resp = model.generate_content(prompt, generation_config=gen_cfg)
            data = _coerce_json(resp.text)
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"  ! 요약 파싱 실패(시도 {attempt + 1}/3): {str(e)[:80]}")
    if data is None:
        raise RuntimeError(f"요약 생성 실패: {last_err}")

    blocks = [
        _clip(data.get("block1", "")),
        _clip(data.get("block2", "")),
        _clip(data.get("block3", "")),
    ]
    return [b for b in blocks if b]
