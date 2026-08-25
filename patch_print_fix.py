import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08.html', encoding='utf-8') as f:
    src = f.read()

# ── 1. exportPrint 함수 전체 교체 ────────────────────────────────────────
OLD = r'function exportPrint\(orientation\) \{.*?\n\}'

NEW = r'''function exportPrint(orientation) {
  var isLandscape = (orientation === 'landscape');

  // ① @page 방향 주입
  var oStyle = document.getElementById('_print_page_size');
  if (!oStyle) {
    oStyle = document.createElement('style');
    oStyle.id = '_print_page_size';
    document.head.appendChild(oStyle);
  }
  oStyle.textContent = isLandscape
    ? '@media print { @page { size: A4 landscape; margin: 10mm 14mm; } }'
    : '@media print { @page { size: A4 portrait;  margin: 14mm 12mm; } }';

  if (isLandscape) document.body.classList.add('print-landscape');
  else             document.body.classList.remove('print-landscape');

  // ② 방향별 유효 너비
  var PW   = isLandscape ? 1017 : 703;
  var HALF = Math.floor((PW - 8) / 2);
  function _h(id) {
    if (isLandscape) { return id === 'chart-trend-top' ? 150 : id === 'chart-social' ? 200 : 180; }
    return id === 'chart-trend-top' ? 240 : id === 'chart-social' ? 320 : 280;
  }

  // ③ ECharts 차트 → PNG 스냅샷으로 교체 (캔버스 인쇄 공백 방지)
  var snaps = [];
  _getAllPrintCharts().forEach(function(c) {
    try {
      var el = c.getDom();
      if (!el) return;
      var isHalf = !!el.closest('.chart-row.col2');
      var w = isHalf ? HALF : PW;
      var h = _h(el.id || '');
      c.resize({ width: w, height: h });

      var url = c.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#ffffff' });
      var img = document.createElement('img');
      img.src = url;
      img.className = '_psnap';
      img.style.cssText = 'display:block;width:100%;height:' + h + 'px;object-fit:contain;';

      // 캔버스 숨기고 img 삽입
      el.style.display = 'none';
      el.parentNode.insertBefore(img, el);
      snaps.push({ el: el, img: img, c: c });
    } catch(e) { console.warn('[print resize]', e); }
  });

  // ④ 복원 함수
  function _restore() {
    snaps.forEach(function(s) {
      try { s.img.parentNode && s.img.parentNode.removeChild(s.img); } catch(e) {}
      s.el.style.display = '';
      try { s.c.resize(); } catch(e) {}
    });
    document.body.classList.remove('print-landscape');
    oStyle.textContent = '';
    snaps = [];
  }

  // ⑤ 인쇄 후 자동 복원
  window.addEventListener('afterprint', _restore, { once: true });

  // ⑥ 이미지 로드 여유 후 인쇄 다이얼로그
  setTimeout(function() { window.print(); }, 500);
}'''

# 함수 전체를 정규식으로 찾아 교체
result = re.sub(OLD, NEW, src, count=1, flags=re.DOTALL)

if result == src:
    print('ERROR: exportPrint 패턴 미발견')
    sys.exit(1)

# ── 2. printAnalysis도 같은 방식으로 개선 ─────────────────────────────────
# (분석 모달 인쇄 — canvas 없으므로 단순 개선만)
OLD2 = "function printAnalysis() {"
if OLD2 in result:
    print('printAnalysis 함수 존재 확인')

with open('output/report_2026_08.html', 'w', encoding='utf-8') as f:
    f.write(result)
print('exportPrint 교체 완료')
