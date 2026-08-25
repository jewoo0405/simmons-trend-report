import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08.html', encoding='utf-8') as f:
    src = f.read()

OLD = """
  // 지수 설명 박스 (P1-2 재정의 반영)
  const gapGuide = `<div style="margin-top:10px;padding:10px 14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;font-size:11px;color:#475569;line-height:1.9;">
    <div style="margin-bottom:6px;font-weight:700;color:#1e3a8a;font-size:11px;">📌 지수 해석 가이드</div>
    <div><span style="display:inline-block;width:16px;text-align:center;margin-right:4px;">🔵</span><b>구글 검색 수요</b> — Google Trends 검색 관심도 · 소비자가 얼마나 찾는가 (수요 지표) · 11개 브랜드 평균=100 재정규화 · 한국</div>
    <div style="margin-top:4px;"><span style="display:inline-block;width:16px;text-align:center;margin-right:4px;">🟢</span><b>네이버 콘텐츠 공급</b> — 블로그+뉴스 총 건수 · 마케팅 물량 지표 (수요 지표 아님) · 11개 브랜드 평균=100 재정규화</div>
    <div style="margin-top:5px;padding:6px 8px;background:#eff6ff;border-radius:4px;color:#1e40af;font-size:10.5px;">
      <b>P1-2 재정의:</b> &nbsp;두 지표는 차원이 다름(수요 vs 공급) — 단순 뺄셈 불가. &nbsp;<b>콘텐츠 생산성 = 네이버 상대지수 ÷ 구글 상대지수</b>로 재정의. &nbsp;100 이상 = 수요 대비 콘텐츠 집중, 100 미만 = 발행 부족.
    </div>
    <div style="margin-top:6px;padding-top:6px;border-top:1px solid #e2e8f0;color:#64748b;">
      <b>해석:</b> &nbsp;높음 = 검색 1단위당 콘텐츠 많음 (마케팅 활발) &nbsp;|&nbsp; 낮음 = 검색 대비 콘텐츠 적음 (마케팅 여력) &nbsp;|&nbsp; ※ 직접 증감 비교 비권장 — 발행 플랫폼·방식 차이 있음
    </div>
  </div>`;
  document.getElementById('section-gap')?.insertAdjacentHTML('beforeend', gapGuide);
"""

count = src.count(OLD)
print(f'패턴 발견: {count}개')

if count == 0:
    print('ERROR: 패턴 없음')
    sys.exit(1)

result = src.replace(OLD, '\n', 1)
with open('output/report_2026_08.html', 'w', encoding='utf-8') as f:
    f.write(result)
print('저장 완료')
