"""
지자체·공공기관 AI·숏폼·홍보 콘텐츠 및 지역 살아보기(고흥스테이 등) 공모전/지원사업 데이터 수집.

수집 대상:
  1. 웰촌(welchon.com) 이벤트/공모전 게시판
  2. 위비티(wevity.com) 정부/공공기관 공모전 및 영상/UCC/AI 카테고리
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# 웰촌 이벤트 게시판
_WELCHON_LIST_URL = "https://www.welchon.com/web/lay1/program/S1T31C447/eventNewList.do?menuIdx=&cIdx=evpr"
_WELCHON_BASE_URL = "https://www.welchon.com/web/lay1/program/S1T31C447/"

# 위비티 정부/공공기관(cidx=6) 및 영상/UCC/사진(cidx=10) 카테고리
_WEVITY_GOV_URL = "https://www.wevity.com/?c=find&s=1&gub=3&cidx=6"
_WEVITY_VIDEO_URL = "https://www.wevity.com/?c=find&s=1&gub=1&cidx=10"
_WEVITY_BASE_URL = "https://www.wevity.com/"

# 핵심 타겟 키워드 (제목이나 본문에 포함될 시 우선도 높임)
_TARGET_KEYWORDS = [
    "숏폼", "60초", "영상", "AI", "인공지능", "홍보", "콘텐츠", "살아보기",
    "스테이", "고흥", "체류", "서포터즈", "공모전", "경진대회", "공모", "지원",
    "릴스", "유튜브", "UCC", "상금", "시상", "촌캉스"
]


@dataclass
class ContestItem:
    title: str
    url: str
    organizer: str
    category: str
    details: str = ""

    def fmt(self) -> str:
        s = f"[{self.category}] {self.title}\n  - 주관/출처: {self.organizer}\n  - 원본링크: {self.url}"
        if self.details:
            s += f"\n  - 주요내용/혜택: {self.details}"
        return s


def _fetch_page(url: str) -> str | None:
    try:
        r = requests.get(url, headers=_HEADERS, timeout=12)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  ! 페이지 조회 실패 [{url[:50]}…]: {e}")
        return None


def _extract_details(url: str) -> str:
    """공고 원본 링크에서 상금, 마감일 등 핵심 정보를 200자 내외로 발췌."""
    html = _fetch_page(url)
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    
    # 웰촌 상세페이지
    if "welchon.com" in url:
        view_cont = soup.select_one(".board-view .view-cont") or soup.select_one(".board-view")
        if view_cont:
            text = view_cont.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            return text[:250] + ("…" if len(text) > 250 else "")
            
    # 위비티 상세페이지
    elif "wevity.com" in url:
        info = soup.select_one(".sub-view-box") or soup.select_one(".cd-area") or soup.select_one("#con_area")
        if info:
            text = info.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            return text[:250] + ("…" if len(text) > 250 else "")
            
    # 일반 웹페이지 본문 발췌
    body = soup.find("body")
    if body:
        text = body.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        return text[:250] + ("…" if len(text) > 250 else "")
    return ""


def _collect_welchon() -> list[ContestItem]:
    items: list[ContestItem] = []
    html = _fetch_page(_WELCHON_LIST_URL)
    if not html:
        return items
    soup = BeautifulSoup(html, "html.parser")
    
    for a in soup.select("a[href*='eventNewView.do']"):
        title = (a.get("title") or a.get_text(strip=True)).strip()
        if not title:
            continue
        href = a.get("href", "")
        full_url = urljoin(_WELCHON_LIST_URL, href)
        
        # 중복 방지
        if any(item.url == full_url for item in items):
            continue
            
        items.append(
            ContestItem(
                title=title,
                url=full_url,
                organizer="한국농어촌공사 웰촌",
                category="웰촌/지역·농촌홍보",
            )
        )
    return items


def _collect_wevity(url: str, category_name: str) -> list[ContestItem]:
    items: list[ContestItem] = []
    html = _fetch_page(url)
    if not html:
        return items
    soup = BeautifulSoup(html, "html.parser")
    
    # 위비티 공고 링크는 ix= 번호 포함
    for a in soup.select("a[href*='ix=']"):
        parent = a.parent
        # 슬라이더 배너 제외
        if parent and parent.parent and "slider" in str(parent.parent.get("class", [])):
            continue
            
        title = a.get_text(strip=True)
        # 텍스트가 비어있다면 부모 혹은 이전 형제 요소에서 추출
        if not title and parent:
            title = parent.get_text(strip=True)
        title = re.sub(r"\s+", " ", title).strip()
        
        # 여전히 비어있거나 불필요한 짧은 텍스트 제외
        if not title or len(title) < 4 or title in ("공모전", "이벤트", "더보기"):
            continue
            
        href = a.get("href", "")
        full_url = urljoin(_WEVITY_BASE_URL, href)
        
        if any(item.url == full_url for item in items):
            continue
            
        # 키워드 매칭 우선 필터링 (영상, AI, 숏폼, 공모, 홍보 등)
        if any(kw in title for kw in _TARGET_KEYWORDS):
            items.append(
                ContestItem(
                    title=title,
                    url=full_url,
                    organizer="정부·공공기관 및 지자체 공모",
                    category=category_name,
                )
            )
    return items


def collect() -> list[ContestItem]:
    """웰촌 및 위비티에서 최신 지자체/공공 공모전 정보를 수집하고 상위 항목 상세정보를 가져옵니다."""
    items: list[ContestItem] = []
    
    # 1. 웰촌 (지역/농촌 체류, 숏폼 등)
    items.extend(_collect_welchon())
    
    # 2. 위비티 정부/공공기관 공모전
    items.extend(_collect_wevity(_WEVITY_GOV_URL, "지자체/공공기관 공모전"))
    
    # 3. 위비티 영상/UCC/사진(숏폼/AI 영상 포함) 카테고리
    items.extend(_collect_wevity(_WEVITY_VIDEO_URL, "영상/숏폼/AI 공모전"))
    
    # 점수 부여: 타겟 키워드가 많이 포함된 항목을 상위로 정렬
    def score_item(item: ContestItem) -> int:
        score = 0
        for kw in ["숏폼", "60초", "살아보기", "고흥스테이", "AI", "인공지능", "홍보"]:
            if kw in item.title:
                score += 3
        for kw in _TARGET_KEYWORDS:
            if kw in item.title:
                score += 1
        if "웰촌" in item.category:
            score += 2
        return score

    items.sort(key=score_item, reverse=True)
    
    # 상위 12개 항목 선택 후, 상위 5개는 상세 페이지에서 혜택/요약 발췌
    top_items = items[:12]
    for i, item in enumerate(top_items[:5]):
        details = _extract_details(item.url)
        if details:
            item.details = details
            
    return top_items


def to_table(items: list[ContestItem]) -> str:
    """LLM 프롬프트용 평문 텍스트 테이블 변환."""
    if not items:
        return "- 수집된 공고 내역이 없습니다."
    return "\n\n".join(f"{i+1}. {item.fmt()}" for i, item in enumerate(items))


if __name__ == "__main__":
    print(to_table(collect()))

