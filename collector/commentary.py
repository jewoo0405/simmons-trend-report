"""
AI 코멘터리 생성 — §16

Anthropic API로 임원용 3문장 브리핑 생성.
ANTHROPIC_API_KEY 없으면 조용히 건너뜀.
근거 없는 원인 추측 방지: suspect=True 항목 반드시 언급 규칙 포함.
"""
import os
import json

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


def _build_prompt(snapshot):
    """스냅샷에서 브리핑 프롬프트 생성"""
    google = snapshot.get("google", {})
    normalized = google.get("normalized", {})
    gap = snapshot.get("gap", [])
    quality = snapshot.get("quality", {})
    suspect = quality.get("suspect", False)
    collected_at = snapshot.get("collected_at", "")

    # 순위 요약
    ranking = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    ranking_text = "\n".join(
        f"  {i+1}위 {name}: {val}" for i, (name, val) in enumerate(ranking[:6])
    )

    # 갭 상위 3개
    gap_text = ""
    if gap:
        top_gaps = sorted(gap, key=lambda x: abs(x.get("gap", 0)), reverse=True)[:3]
        gap_text = "\n".join(
            f"  {g['brand']}: 네이버-구글 {g['gap']:+.0f}pt"
            for g in top_gaps
        )

    suspect_note = ""
    if suspect:
        suspect_note = "\n주의: 이번 데이터에 전일 대비 3배 이상 변동(suspect=True)이 있습니다. 반드시 언급하세요."

    prompt = f"""아래는 침대·가구 브랜드 검색 트렌드 스냅샷입니다. 시몬스 담당 임원용 브리핑을 작성하세요.

수집일시: {collected_at}

구글 검색 지수 (시몬스=100):
{ranking_text}

구글 vs 네이버 갭 상위:
{gap_text}

규칙:
- 정확히 3문장
- 시몬스 관점에서만 서술
- tier 3(종합 가구: 한샘, 현대리바트, 까사미아, 일룸, 에몬스, 이케아)는 카테고리 오염이 있으므로 순위 비교에 사용하지 말 것
- 데이터에 없는 원인을 추측하지 말 것. 원인이 불명확하면 '원인 미확인'이라고 쓸 것
- 수치를 정확히 인용할 것{suspect_note}"""

    return prompt


def generate_commentary(snapshot):
    """
    Anthropic API로 임원 브리핑 생성.
    Returns: str (3문장) or "" if unavailable.
    """
    if not ANTHROPIC_API_KEY:
        print("  [Commentary] ANTHROPIC_API_KEY 없음 — 건너뜀")
        return ""

    try:
        import anthropic
    except ImportError:
        print("  [Commentary] anthropic 패키지 없음 (pip install anthropic)")
        return ""

    prompt = _build_prompt(snapshot)

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        print(f"  [Commentary] 생성 완료 ({len(text)}자)")
        return text
    except Exception as e:
        print(f"  [Commentary] 오류: {e}")
        return ""
