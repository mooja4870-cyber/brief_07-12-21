"""
시장 데이터 수집 (네이버 금융 실시간 API).

야후(yfinance)는 한국 지수가 15~20분 지연되고 전일종가 기준도 어긋나
사용자가 보는 네이버 값과 다릅니다. 그래서 한국·미국·환율 모두
네이버 실시간 API(delayTime=0)에서 직접 받아 네이버 화면과 일치시킵니다.

엔드포인트
  국내 지수 : polling.finance.naver.com/api/realtime/domestic/index/{KOSPI|KOSDAQ}
  국내 종목 : polling.finance.naver.com/api/realtime/domestic/stock/{종목코드}
  해외 지수 : polling.finance.naver.com/api/realtime/worldstock/index/{.INX 등}
  해외 종목 : polling.finance.naver.com/api/realtime/worldstock/stock/{NVDA.O 등}
  환율      : m.stock.naver.com/front-api/marketIndex/productDetail?category=exchange&reutersCode=FX_USDKRW
"""
from __future__ import annotations

from dataclasses import dataclass

import requests

_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://finance.naver.com/",
}
_POLL = "https://polling.finance.naver.com/api/realtime"
_FX_URL = (
    "https://m.stock.naver.com/front-api/marketIndex/productDetail"
    "?category=exchange&reutersCode=FX_USDKRW"
)

# 네이버 등락 방향 코드: 1 상한·2 상승 → +, 4 하한·5 하락 → -, 3 보합 → 0
_DOWN_CODES = {"4", "5"}


@dataclass
class Quote:
    name: str
    price_str: str       # 네이버가 준 표시 문자열 그대로 ('7,627.94', '301,250')
    pct: float | None    # 전일 대비 등락률(%), 부호 포함
    suffix: str = ""     # '원' 등

    def fmt(self) -> str:
        price = f"{self.price_str}{self.suffix}"
        if self.pct is None:
            return f"{self.name} {price}"
        sign = "+" if self.pct >= 0 else ""
        return f"{self.name} {price} ({sign}{self.pct:.2f}%)"


def _signed_ratio(ratio_str: str, direction_code: str | None) -> float | None:
    """등락률 문자열 + 방향 코드 → 부호 있는 float."""
    if ratio_str is None:
        return None
    s = str(ratio_str).replace(",", "").strip()
    try:
        r = float(s)
    except ValueError:
        return None
    if s.startswith("-"):            # 이미 부호 있음(해외/환율)
        return r
    if direction_code in _DOWN_CODES:  # 양수 크기 + 방향 코드(국내)
        return -abs(r)
    return abs(r)


def _get(url: str) -> dict | None:
    try:
        r = requests.get(url, headers=_HEADERS, timeout=12)
        r.raise_for_status()
        return r.json()
    except Exception as e:  # noqa: BLE001
        print(f"  ! 요청 실패 {url[:60]}…: {e}")
        return None


def _from_polling(name: str, kind: str, code: str, suffix: str = "") -> Quote | None:
    """domestic/worldstock 공통 폴링 파서."""
    data = _get(f"{_POLL}/{kind}/{code}")
    if not data or not data.get("datas"):
        return None
    d = data["datas"][0]
    price = d.get("closePrice")
    if price is None:
        return None
    direction = (d.get("compareToPreviousPrice") or {}).get("code")
    pct = _signed_ratio(d.get("fluctuationsRatio"), direction)
    return Quote(name=name, price_str=str(price), pct=pct, suffix=suffix)


def _fx() -> Quote | None:
    data = _get(_FX_URL)
    if not data or not data.get("result"):
        return None
    res = data["result"]
    price = res.get("closePrice")
    if price is None:
        return None
    direction = (res.get("fluctuationsType") or {}).get("code")
    pct = _signed_ratio(res.get("fluctuationsRatio"), direction)
    return Quote(name="원/달러", price_str=str(price), pct=pct, suffix="원")


# 수집 대상 (표시명, kind, 코드, 접미사)
_DOMESTIC_INDEX = [("코스피", "KOSPI"), ("코스닥", "KOSDAQ")]
_DOMESTIC_STOCK = [("삼성전자", "005930"), ("SK하이닉스", "000660")]
_WORLD_INDEX = [
    ("S&P500", ".INX"),
    ("나스닥", ".IXIC"),
    ("다우", ".DJI"),
    ("필라델피아반도체(SOX)", ".SOX"),
    ("VIX(공포지수)", ".VIX"),
]
_WORLD_STOCK = [("엔비디아", "NVDA.O")]


def collect() -> list[Quote]:
    """모든 대상을 네이버 실시간에서 수집. 일부 실패해도 나머지 진행."""
    quotes: list[Quote] = []
    for name, code in _DOMESTIC_INDEX:
        q = _from_polling(name, "domestic/index", code)
        if q:
            quotes.append(q)
    for name, code in _DOMESTIC_STOCK:
        q = _from_polling(name, "domestic/stock", code, suffix="원")
        if q:
            quotes.append(q)
    fx = _fx()
    if fx:
        quotes.append(fx)
    for name, code in _WORLD_INDEX:
        q = _from_polling(name, "worldstock/index", code)
        if q:
            quotes.append(q)
    for name, code in _WORLD_STOCK:
        q = _from_polling(name, "worldstock/stock", code)
        if q:
            quotes.append(q)
    return quotes


def to_table(quotes: list[Quote]) -> str:
    """LLM 프롬프트용 평문 테이블."""
    return "\n".join(f"- {q.fmt()}" for q in quotes)


if __name__ == "__main__":
    print(to_table(collect()))
