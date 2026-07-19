"""
Gemini 기반 지자체/기관 공모전·지원사업 요약 생성기.

개조식·음슴체 톤과 구조로,
카카오 200자 제한에 맞춰 5개 블록(각 ≤190자)으로 나눠 반환합니다.

블록 구성:
  1) 헤더 + 지자체·기관 공모전 종합 요약
  2) 추천 공고 1 상세 + 원본 링크
  3) 추천 공고 2 상세 + 원본 링크
  4) 추천 공고 3 상세 + 원본 링크
  5) 종합 지원 전략 + 마감/가산점 주의사항
"""
from __future__ import annotations

import json
import re

from . import config

# 발송 시점별 관점
SLOT_FOCUS = {
    "morning": (
        "🌅 아침 공모전·지원사업 핵심 브리핑 (07:00)",
        "지자체 및 공공기관의 AI/숏폼 영상 공모전, 지역 살아보기(고흥스테이 등) 체류 및 홍보 지원사업, 각종 콘텐츠 시상·혜택 정보를 중심으로 오늘의 추천 공고와 핵심 혜택을 분석하세요.",
    ),
    "afternoon": (
        "☀️ 오후 공모전·지원사업 핵심 브리핑 (14:00)",
        "오후 기준 마감 임박 또는 주목할 만한 지자체/기관의 AI·숏폼 영상 제작 공모전 및 지역 체류 지원사업의 상금/혜택 요약과 참가 전략을 분석하세요.",
    ),
}
# 하위 호환성 유지 (기존 noon, evening 요청 시 afternoon, morning으로 매핑)
SLOT_FOCUS["noon"] = SLOT_FOCUS["afternoon"]
SLOT_FOCUS["evening"] = SLOT_FOCUS["morning"]

_BLOCK_MAX = 190  # 카카오 텍스트 템플릿 200자 안전 마진


def _build_prompt(slot: str, header: str, focus: str, table: str, date_str: str) -> str:
    return f"""당신은 지자체·공공기관 사업 및 공모전 혜택 분석 전문가입니다.
아래 수집된 공고 데이터를 바탕으로, 카카오톡으로 받아볼 '핵심 요약 및 원본 링크' 브리핑을 작성하세요.

[작성일] {date_str}
[브리핑 시점] {header}
[이 시점의 관점] {focus}

[수집된 공고 데이터]
{table}

[문체 — 매우 중요]
- 모든 문장을 '~음 / ~임 / ~함' 같은 개조식 짧은 종결로 끝내세요. '~습니다 / ~입니다 / ~있습니다 / ~됩니다' 같은 존댓말 종결은 절대 쓰지 마세요.
  예: "상금 1천만원을 지급함", "접수 마감은 8월 14일임", "숏폼 제작 가산점이 부여됨".
- 과장 없이 핵심 상금, 지원 혜택, 참가 대상, 마감 기한을 명확히 제시하세요.
- 데이터에 없는 허위 수치나 내용을 지어내지 마세요.

[형식·줄바꿈 규칙 — 가독성 매우 중요]
- 줄이 바뀔 때마다 빈 줄을 하나 두고 바꾸세요. 즉 줄과 줄 사이를 빈 줄 포함 '\\n\\n'으로 구분합니다.
- 이모지는 block1의 첫 줄(헤더)에만 딱 1개 사용하세요(예: 🌅 아침 공모전·지원사업 핵심 브리핑).
- 그 외 모든 줄(block1 둘째 줄부터, block2~block5의 일반 설명)은 줄 맨 앞을 '- '(하이픈+공백)으로 시작하세요.
- 단, block2, block3, block4의 맨 마지막 줄은 반드시 '🔗 원본 링크: [URL]' 형식으로 작성해야 합니다.

[블록별 작성 안내]
- block1: 첫 줄은 이모지 1개로 시작하는 헤더. 빈 줄(\\n\\n) 후 '- '로 시작하는 오늘 수집된 지자체/기관 AI·숏폼·홍보·살아보기 공모전 및 지원사업 동향 요약 1~2개 불릿.
- block2: 추천 공고 1. '- [공고명]' 및 상금/혜택/참가조건 요약 1~2개 불릿. 마지막 줄에 반드시 '🔗 원본 링크: (해당 공고의 실제 URL)' 명시.
- block3: 추천 공고 2. '- [공고명]' 및 상금/혜택/참가조건 요약 1~2개 불릿. 마지막 줄에 반드시 '🔗 원본 링크: (해당 공고의 실제 URL)' 명시.
- block4: 추천 공고 3. '- [공고명]' 및 상금/혜택/참가조건 요약 1~2개 불릿. 마지막 줄에 반드시 '🔗 원본 링크: (해당 공고의 실제 URL)' 명시.
- block5: '- '로 시작하는 종합 지원 전략 또는 가산점/접수일정 팁 1~2개 불릿.

[출력 형식 — 반드시 JSON만 출력, 코드블록·설명 금지]
{{
  "block1": "🌅 아침 공모전·지원사업 핵심 브리핑 (07:00)\\n\\n- 지자체 및 공공기관의 AI 숏폼 영상 제작 및 지역 체류 홍보 공모전 접수가 활발함.\\n\\n- 대상 상금 1천만원 및 거주 지원금 등 실질적 혜택 사업에 주목할 필요가 있음.",
  "block2": "- [웰촌] 바쁜 일상 속 쉼표, 촌캉스 농촌여행 숏폼 공모전\\n\\n- 농어촌공사 주관, 60초 숏폼 제작 및 SNS 홍보 시 상금 및 혜택 지원함.\\n\\n🔗 원본 링크: https://www.welchon.com/web/lay1/program/S1T31C447/eventNewView.do?menuIdx=&cIdx=evpr&bbsIdx=2214028",
  "block3": "- 2026 대전 AI 영상 공모전 (총 상금 5천~3천만원)\\n\\n- 대전광역시 주관, AI 기술 활용 영상 콘텐츠 제작 시 1등 상금 1,000만원 지급함.\\n\\n🔗 원본 링크: https://www.wevity.com/?c=find&s=1&gub=3&cidx=6&gbn=view&gp=1&ix=109142",
  "block4": "- 2026 ACC 민주·인권·평화 영상(+AI) 콘텐츠 공모전\\n\\n- 국립아시아문화전당 주관, 1등 500만원 상금 및 수상작 전시 혜택 부여함.\\n\\n🔗 원본 링크: https://www.wevity.com/?c=find&s=1&gub=3&cidx=6&gbn=view&gp=1&ix=107427",
  "block5": "- 60초 세로형 숏폼 및 AI 도구 활용 영상은 제작 기간을 감안해 미리 기획하는 것이 유리함.\\n\\n- 지자체 살아보기 지원사업은 인플루언서·SNS 홍보 의사 표명 시 가산점이 부여됨."
}}
※ 위 예시의 URL은 수집 데이터에 있는 실제 공고 링크로 정확히 채워넣을 것.

[길이 규칙 — 반드시 준수]
- 빈 줄(\\n\\n)도 글자 수에 포함됩니다. 각 블록은 빈 줄 포함 130~188자로 작성하세요.
- 카카오톡 텍스트 200자 제한으로 인해, block2~4는 요약 텍스트와 원본 링크가 합쳐서 {_BLOCK_MAX}자를 넘지 않도록 간결하고 명확하게 요약하세요.
"""


def _coerce_json(text: str) -> dict:
    text = text.strip()
    if "```" in text:
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
        
    # 링크가 포함된 경우 링크를 훼손하지 않고 앞의 설명 텍스트를 줄임
    link_match = re.search(r"(🔗\s*원본\s*링크:\s*https?://\S+)", s)
    if link_match:
        link_str = link_match.group(1).strip()
        avail = _BLOCK_MAX - len(link_str) - 2
        if avail > 30:
            body = s[:link_match.start()].strip()
            if len(body) > avail:
                body = body[:avail].rsplit("\n", 1)[0].strip()
            return f"{body}\n\n{link_str}"
            
    # 일반 텍스트인 경우 경계에서 자르기
    cut = s[:_BLOCK_MAX]
    best, best_len = -1, 0
    for sep in ("\n\n", "\n", "음.", "임.", "함.", "니다.", "다.", "요.", ". "):
        idx = cut.rfind(sep)
        if idx > best:
            best, best_len = idx, len(sep)
    if best > _BLOCK_MAX * 0.4:
        return cut[: best + best_len].strip()
    return cut.strip()


def generate(slot: str, table: str, date_str: str) -> list[str]:
    """slot('morning'|'afternoon')에 맞춰 5개 블록 문자열을 반환."""
    header, focus = SLOT_FOCUS.get(slot, SLOT_FOCUS["morning"])

    import google.generativeai as genai

    genai.configure(api_key=config.gemini_api_key())
    model = genai.GenerativeModel(config.GEMINI_MODEL)

    prompt = _build_prompt(slot, header, focus, table, date_str)
    gen_cfg = {
        "temperature": 0.6,
        "max_output_tokens": 2048,
        "response_mime_type": "application/json",
    }

    data = None
    last_err = None
    for attempt in range(3):
        try:
            resp = model.generate_content(prompt, generation_config=gen_cfg)
            data = _coerce_json(resp.text)
            break
        except Exception as e:
            last_err = e
            print(f"  ! 요약 파싱 실패(시도 {attempt + 1}/3): {str(e)[:80]}")
    if data is None:
        raise RuntimeError(f"요약 생성 실패: {last_err}")

    blocks = [_clip(data.get(f"block{i}", "")) for i in range(1, 6)]
    return [b for b in blocks if b]

