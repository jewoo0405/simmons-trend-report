import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08.html', encoding='utf-8') as f:
    src = f.read()

OLD = '<div id="chart-gap" style="height:320px;"></div>\n    </div>\n  </div>'

NEW_GUIDE = '''<div id="chart-gap" style="height:320px;"></div>

      <!-- 지수 해석 가이드 -->
      <div style="margin-top:16px;background:#f8f9fa;border-radius:8px;padding:14px 16px;border:1px solid #e9ecef;">
        <div style="font-size:12px;font-weight:700;color:#c62828;margin-bottom:10px;">&#9757; 지수 해석 가이드</div>
        <div style="display:flex;flex-direction:column;gap:7px;font-size:12px;color:#333;line-height:1.7;">

          <div style="display:flex;align-items:flex-start;gap:8px;">
            <span style="color:#1a73e8;font-size:16px;line-height:1.2;">&#9679;</span>
            <div><strong>구글 검색 수요</strong> — 소비자가 직접 검색해서 찾아보는 양입니다. &ldquo;얼마나 궁금해하는가&rdquo;를 나타내는 수요 지표입니다. 11개 브랜드 평균=100 기준으로 환산했습니다.</div>
          </div>

          <div style="display:flex;align-items:flex-start;gap:8px;">
            <span style="color:#34a853;font-size:16px;line-height:1.2;">&#9679;</span>
            <div><strong>네이버 콘텐츠 공급</strong> — 블로그·뉴스에 올라온 글의 양입니다. &ldquo;얼마나 마케팅 콘텐츠를 뿌렸는가&rdquo;를 나타냅니다. 검색 수요와는 다른 차원의 지표입니다.</div>
          </div>

          <div style="background:#fff3cd;border-radius:5px;padding:9px 12px;border-left:3px solid #f0ad4e;margin-top:2px;">
            <strong style="color:#856404;">이 차트가 보여주는 것</strong><br>
            콘텐츠 생산성 = 네이버 지수 ÷ 구글 지수. 막대가 <strong>오른쪽(+)</strong>이면 검색 수요 대비 콘텐츠가 많이 나오고 있는 것(마케팅 물량 집중), <strong>왼쪽(-)</strong>이면 사람들이 찾아보는 것에 비해 콘텐츠가 부족한 것(마케팅 기회 있음)입니다.
          </div>

          <div style="font-size:11px;color:#666;border-top:1px solid #dee2e6;padding-top:8px;margin-top:2px;">
            <span style="font-weight:700;">해석 요약:</span>
            &nbsp;&#43;높음 = 검색 1건당 콘텐츠가 많다 (마케팅 활발) &nbsp;|&nbsp;
            &#8722;낮음 = 검색보다 콘텐츠가 적다 (마케팅 여력 있음)
            <br>
            &#8251; 이케아·한샘처럼 큰 음수(-) 값은 &ldquo;브랜드 자체 검색량이 워낙 많아서&rdquo; 생기는 현상으로, 단순히 콘텐츠가 부족하다기보다 브랜드 파워가 강하다는 뜻일 수 있습니다.
          </div>

        </div>
      </div>
    </div>
  </div>'''

if OLD not in src:
    print('ERROR: 삽입 마커를 찾을 수 없음')
    # 대안 검색
    alt = '<div id="chart-gap" style="height:320px;"></div>'
    idx = src.find(alt)
    print(f'chart-gap div 위치: {idx}')
    print(repr(src[idx:idx+200]))
    import sys; sys.exit(1)

result = src.replace(OLD, NEW_GUIDE, 1)
print(f'원본: {len(src):,}자 → 수정: {len(result):,}자')

with open('output/report_2026_08.html', 'w', encoding='utf-8') as f:
    f.write(result)
print('저장 완료')
