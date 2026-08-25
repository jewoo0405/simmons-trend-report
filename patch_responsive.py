"""
patch_responsive.py — report_2026_08.html 반응형 패치
각 교체는 정확히 한 곳에서만 발생해야 합니다.
"""
import sys
import re

HTML_PATH = r'C:\simmons-trend-report\output\report_2026_08.html'

# ─────────────────────────────────────────────────────────────
# 헬퍼: 정확히 1회 교체, 없으면 종료
# ─────────────────────────────────────────────────────────────
def replace_once(src: str, old: str, new: str, label: str) -> str:
    count = src.count(old)
    if count == 0:
        print(f'[ERROR] 패턴을 찾지 못했습니다: {label!r}')
        sys.exit(1)
    if count > 1:
        print(f'[ERROR] 패턴이 {count}곳에서 발견됩니다 (정확히 1곳이어야 함): {label!r}')
        sys.exit(1)
    print(f'[OK]    {label}')
    return src.replace(old, new, 1)


# ─────────────────────────────────────────────────────────────
# 삽입용 헬퍼: 정확히 1회 삽입 (old 뒤에 new 추가)
# ─────────────────────────────────────────────────────────────
def insert_after_once(src: str, anchor: str, insertion: str, label: str) -> str:
    return replace_once(src, anchor, anchor + insertion, label)

def insert_before_once(src: str, anchor: str, insertion: str, label: str) -> str:
    return replace_once(src, anchor, insertion + anchor, label)


# ─────────────────────────────────────────────────────────────
# 파일 읽기
# ─────────────────────────────────────────────────────────────
with open(HTML_PATH, encoding='utf-8') as f:
    html = f.read()

print('=== patch_responsive.py 시작 ===')
print(f'파일 크기: {len(html):,} bytes')

# ─────────────────────────────────────────────────────────────
# 1. CSS: body min-width 교체
# ─────────────────────────────────────────────────────────────
html = replace_once(
    html,
    '  min-width: 1280px;',
    '  min-width: 0;',
    'body min-width: 1280px → 0'
)

# ─────────────────────────────────────────────────────────────
# 2. CSS: 반응형 미디어쿼리 추가 — 첫 번째 </style> 바로 직전
#    (line 720, 인쇄용 블록 밖의 메인 <style> 태그)
# ─────────────────────────────────────────────────────────────
RESPONSIVE_CSS = """
/* ── 반응형 브레이크포인트 ─────────────────── */
/* 사이드바 토글 오버레이 */
#sidebar-overlay {
  display: none; position: fixed; inset: 0;
  background: rgba(0,0,0,.35); z-index: 150;
}
#sidebar-overlay.open { display: block; }

/* 사이드바 토글 버튼 */
#sidebar-toggle {
  display: none; align-items: center; justify-content: center;
  width: 36px; height: 36px; margin-right: 8px;
  border: 1px solid var(--border); border-radius: var(--r-s);
  background: var(--surface); cursor: pointer; font-size: 18px; color: var(--tx2);
  flex-shrink: 0;
}

@media (max-width: 1100px) {
  #sidebar-toggle { display: flex; }
  #sidebar {
    position: fixed; left: 0; top: var(--header-h);
    height: calc(100vh - var(--header-h));
    transform: translateX(-100%);
    transition: transform .22s ease;
    z-index: 160; box-shadow: var(--shadow-m);
  }
  #sidebar.open { transform: translateX(0); }
  #main { padding: 16px; }
}

@media (max-width: 800px) {
  .chart-row.col2,
  .chart-row.col3 { grid-template-columns: 1fr !important; }
  .kpi-strip { grid-template-columns: 1fr 1fr !important; }
  .summary-grid { grid-template-columns: 1fr !important; }
  #main { padding: 12px; gap: 14px; }
}

@media (max-width: 480px) {
  .kpi-strip { grid-template-columns: 1fr !important; }
  .header-chip, .conf-badge { display: none; }
}
"""

# 첫 번째 </style>만 교체: 그 앞에 CSS 삽입
# 두 번째 </style>은 JS 팝업 창 내부 인라인 스타일 문자열이므로 제외
# → 첫 번째 </style>은 @media print { } 블록 끝 바로 뒤에 있음
# 고유한 앵커: 'grid-template-columns: 1fr 1fr !important;\n  }\n}\n</style>\n</head>'
FIRST_STYLE_ANCHOR = (
    '    grid-template-columns: 1fr 1fr !important;\n'
    '  }\n'
    '}\n'
    '</style>\n'
    '</head>'
)
FIRST_STYLE_NEW = (
    '    grid-template-columns: 1fr 1fr !important;\n'
    '  }\n'
    '}\n'
    + RESPONSIVE_CSS
    + '</style>\n'
    '</head>'
)
html = replace_once(
    html,
    FIRST_STYLE_ANCHOR,
    FIRST_STYLE_NEW,
    '반응형 CSS 삽입 (첫 번째 </style> 직전)'
)

# ─────────────────────────────────────────────────────────────
# 3. HTML: 사이드바 오버레이 div — <nav id="sidebar"> 바로 앞
# ─────────────────────────────────────────────────────────────
html = insert_before_once(
    html,
    '<nav id="sidebar">',
    '<div id="sidebar-overlay" onclick="toggleSidebar()"></div>\n',
    '사이드바 오버레이 div 삽입'
)

# ─────────────────────────────────────────────────────────────
# 4. HTML: 햄버거 버튼 — <div class="header-brand"> 바로 뒤
#    실제 구조: <div class="header-brand">\n    <div class="header-logo">
#    → header-brand 여는 태그 뒤에 삽입
# ─────────────────────────────────────────────────────────────
HAMBURGER_BTN = '\n  <button id="sidebar-toggle" onclick="toggleSidebar()" title="메뉴">☰</button>'

# </div>  (header-brand 닫힘) 다음에 삽입하는 대신,
# header-brand 블록 전체를 잡아서 닫는 </div> 뒤에 삽입
# 실제 구조 확인: header-brand div 닫히는 위치 = 줄 752 '</div>'
# 안전한 앵커: header-brand의 닫힘 직후
# 앵커를 좀 더 구체적으로: header-title-group 닫힘 → header-brand 닫힘 순서

HEADER_BRAND_CLOSE_ANCHOR = (
    '    </div>\n'          # .header-title-group 닫힘
    '  </div>\n'            # .header-brand 닫힘
    '  <div class="header-right">'
)
HEADER_BRAND_CLOSE_NEW = (
    '    </div>\n'
    '  </div>\n'
    '  <button id="sidebar-toggle" onclick="toggleSidebar()" title="메뉴">☰</button>\n'
    '  <div class="header-right">'
)
html = replace_once(
    html,
    HEADER_BRAND_CLOSE_ANCHOR,
    HEADER_BRAND_CLOSE_NEW,
    '햄버거 버튼 삽입 (header-brand 뒤)'
)

# ─────────────────────────────────────────────────────────────
# 5. JS: 사이드바 토글 + ResizeObserver — 마지막 </script> 바로 앞
# ─────────────────────────────────────────────────────────────
RESPONSIVE_JS = """
// ── 사이드바 토글 ──────────────────────────────────────────────
function toggleSidebar() {
  var sb = document.getElementById('sidebar');
  var ov = document.getElementById('sidebar-overlay');
  var open = sb.classList.toggle('open');
  ov.classList.toggle('open', open);
}

// ── ECharts 자동 리사이즈 (ResizeObserver) ─────────────────────
(function() {
  if (typeof ResizeObserver === 'undefined') return;
  var _resizeTimer = null;
  var ro = new ResizeObserver(function(entries) {
    clearTimeout(_resizeTimer);
    _resizeTimer = setTimeout(function() {
      entries.forEach(function(entry) {
        var el = entry.target;
        var chart = (typeof echarts !== 'undefined') && echarts.getInstanceByDom(el);
        if (chart) { try { chart.resize(); } catch(e) {} }
      });
    }, 80);
  });
  // 모든 차트 컨테이너 관찰 등록 (DOM 준비 후)
  function _observeCharts() {
    document.querySelectorAll('[id^="chart-"]').forEach(function(el) {
      ro.observe(el);
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _observeCharts);
  } else {
    _observeCharts();
  }
  // 렌더 함수들이 나중에 차트를 생성하는 경우 대비 — 500ms 후 재스캔
  setTimeout(_observeCharts, 800);
})();
"""

# 마지막 </script> 바로 앞 — 파일에서 마지막으로 등장하는 </script>
# 마지막 </script>의 앵커: window.addEventListener('resize', ...) 블록 끝 부분
LAST_SCRIPT_ANCHOR = '\n</script>\n</body>\n</html>'
html = replace_once(
    html,
    LAST_SCRIPT_ANCHOR,
    RESPONSIVE_JS + '\n</script>\n</body>\n</html>',
    'JS 삽입 (마지막 </script> 직전)'
)

# ─────────────────────────────────────────────────────────────
# 파일 저장
# ─────────────────────────────────────────────────────────────
with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\n[완료] {HTML_PATH} 저장됨 ({len(html):,} bytes)')
print('=== 패치 성공 ===')
