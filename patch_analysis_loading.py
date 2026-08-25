import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08.html', encoding='utf-8') as f:
    src = f.read()

# ── 1. runAnalysis 함수 교체 ──────────────────────────────────
OLD = """function runAnalysis() {
  const body = document.getElementById('analysis-body-content');
  if (body && body.dataset.original) body.innerHTML = body.dataset.original;
  _doSosTrend();
  _refreshAnalysisBtns(false);
}"""

NEW = """function runAnalysis() {
  const btn  = document.getElementById('btn-analyze');
  const body = document.getElementById('analysis-body-content');

  // ① 버튼 로딩 상태
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="an-spinner"></span> 분석 중...';
  }

  // ② 콘텐츠 영역 로딩 오버레이
  if (body) {
    body.style.position = 'relative';
    const overlay = document.createElement('div');
    overlay.id = 'an-loading-overlay';
    overlay.innerHTML = `
      <div style="display:flex;flex-direction:column;align-items:center;gap:14px;">
        <div class="an-spinner-lg"></div>
        <div style="font-size:13px;color:#555;font-weight:600;">데이터 분석 중입니다...</div>
        <div style="font-size:11px;color:#999;">구글 트렌드 · 네이버 · DART 지표 종합 중</div>
      </div>`;
    overlay.style.cssText = 'position:absolute;inset:0;background:rgba(255,255,255,.85);' +
      'display:flex;align-items:center;justify-content:center;border-radius:8px;z-index:10;min-height:200px;';
    body.appendChild(overlay);
  }

  // ③ 실제 분석 (400ms 딜레이로 로딩 느낌 부여)
  setTimeout(() => {
    if (body && body.dataset.original) body.innerHTML = body.dataset.original;
    _doSosTrend();
    _refreshAnalysisBtns(false);
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '▶ 분석하기';
    }
  }, 400);
}"""

count = src.count(OLD)
print(f'runAnalysis 패턴: {count}개')
if count == 0:
    print('ERROR'); sys.exit(1)
src = src.replace(OLD, NEW, 1)

# ── 2. CSS 스피너 추가 ────────────────────────────────────────
OLD_CSS = '.an-run-btn, .an-save-btn, .an-edit-btn {'
NEW_CSS = """@keyframes an-spin { to { transform: rotate(360deg); } }
.an-spinner {
  display: inline-block; width: 11px; height: 11px;
  border: 2px solid rgba(255,255,255,.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: an-spin .6s linear infinite;
  vertical-align: middle; margin-right: 4px;
}
.an-spinner-lg {
  width: 36px; height: 36px;
  border: 3px solid #e0e0e0;
  border-top-color: #1a1a2e;
  border-radius: 50%;
  animation: an-spin .7s linear infinite;
}
.an-run-btn, .an-save-btn, .an-edit-btn {"""

count2 = src.count(OLD_CSS)
print(f'CSS 패턴: {count2}개')
if count2 == 0:
    print('ERROR CSS'); sys.exit(1)
src = src.replace(OLD_CSS, NEW_CSS, 1)

with open('output/report_2026_08.html', 'w', encoding='utf-8') as f:
    f.write(src)
print('저장 완료')
