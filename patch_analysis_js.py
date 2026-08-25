import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08.html', encoding='utf-8') as f:
    src = f.read()

# 실제 openAnalysis 함수 전체를 찾아서 교체
OLD = """function openAnalysis() {
  document.getElementById('analysis-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
  // 전월 대비 구글 검색 지수 추세 (시몬스 기준)
  const trendEl = document.getElementById('an-sos-trend');
  if (trendEl) {
    const ms = RAW.google?.monthly_series?.['시몬스'] || [];
    const minLen = IS_PARTIAL_MONTH ? 3 : 2;
    if (ms.length >= minLen) {
      const curr = IS_PARTIAL_MONTH ? ms[ms.length-2]?.value : ms[ms.length-1]?.value;
      const prev = IS_PARTIAL_MONTH ? ms[ms.length-3]?.value : ms[ms.length-2]?.value;
      const period = IS_PARTIAL_MONTH ? ms[ms.length-2]?.period?.substring(0,7) : ms[ms.length-1]?.period?.substring(0,7);
      if (curr != null && prev != null && prev > 0) {
        const pct = ((curr - prev) / prev * 100).toFixed(1);
        const isUp = parseFloat(pct) >= 0;
        trendEl.innerHTML = `${period} 전월 대비 <span style="color:${isUp?'#80cbc4':'#ef9a9a'};font-weight:700;">${isUp?'▲':'▼'}${isUp?'+':''}${pct}%</span>`;
      }
    }
  }
}"""

NEW = """// ── 분석 저장/불러오기 ──────────────────────────────────────
const ANALYSIS_STORAGE_KEY = 'simmons_analysis_saved_2026_08';

function _refreshAnalysisBtns(isSaved) {
  const btnAnalyze = document.getElementById('btn-analyze');
  const btnSave    = document.getElementById('btn-save');
  const btnEdit    = document.getElementById('btn-edit');
  const banner     = document.getElementById('an-saved-banner');
  if (btnAnalyze) btnAnalyze.style.display = isSaved ? 'none' : '';
  if (btnSave)    btnSave.style.display    = isSaved ? 'none' : '';
  if (btnEdit)    btnEdit.style.display    = isSaved ? ''     : 'none';
  if (banner)     banner.style.display     = isSaved ? 'flex' : 'none';
}

function _doSosTrend() {
  const trendEl = document.getElementById('an-sos-trend');
  if (trendEl) {
    const ms = RAW.google?.monthly_series?.['시몬스'] || [];
    const minLen = IS_PARTIAL_MONTH ? 3 : 2;
    if (ms.length >= minLen) {
      const curr = IS_PARTIAL_MONTH ? ms[ms.length-2]?.value : ms[ms.length-1]?.value;
      const prev = IS_PARTIAL_MONTH ? ms[ms.length-3]?.value : ms[ms.length-2]?.value;
      const period = IS_PARTIAL_MONTH ? ms[ms.length-2]?.period?.substring(0,7) : ms[ms.length-1]?.period?.substring(0,7);
      if (curr != null && prev != null && prev > 0) {
        const pct = ((curr - prev) / prev * 100).toFixed(1);
        const isUp = parseFloat(pct) >= 0;
        trendEl.innerHTML = `${period} 전월 대비 <span style="color:${isUp?'#80cbc4':'#ef9a9a'};font-weight:700;">${isUp?'▲':'▼'}${isUp?'+':''}${pct}%</span>`;
      }
    }
  }
}

function runAnalysis() {
  const body = document.getElementById('analysis-body-content');
  if (body && body.dataset.original) body.innerHTML = body.dataset.original;
  _doSosTrend();
  _refreshAnalysisBtns(false);
}

function saveAnalysis() {
  const body = document.getElementById('analysis-body-content');
  if (!body) return;
  const now = new Date();
  const stamp = now.getFullYear() + '.' +
    String(now.getMonth()+1).padStart(2,'0') + '.' +
    String(now.getDate()).padStart(2,'0') + ' ' +
    String(now.getHours()).padStart(2,'0') + ':' +
    String(now.getMinutes()).padStart(2,'0');
  try {
    localStorage.setItem(ANALYSIS_STORAGE_KEY, JSON.stringify({ html: body.innerHTML, savedAt: stamp }));
    const dateEl = document.getElementById('an-saved-date');
    if (dateEl) dateEl.textContent = stamp + ' 저장됨';
    _refreshAnalysisBtns(true);
    const btn = document.getElementById('btn-save');
    if (btn) { btn.textContent = '✓ 저장됨'; setTimeout(() => { btn.textContent = '💾 저장'; }, 1500); }
  } catch(e) { alert('저장 실패: ' + e.message); }
}

function editAnalysis() {
  if (!confirm('저장된 분석을 삭제하고 현재 데이터로 다시 불러오시겠습니까?')) return;
  localStorage.removeItem(ANALYSIS_STORAGE_KEY);
  runAnalysis();
}

function openAnalysis() {
  document.getElementById('analysis-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';

  // 원본 HTML 최초 1회 저장
  const body = document.getElementById('analysis-body-content');
  if (body && !body.dataset.original) body.dataset.original = body.innerHTML;

  // localStorage 저장본 확인
  let saved = null;
  try { saved = JSON.parse(localStorage.getItem(ANALYSIS_STORAGE_KEY)); } catch {}

  if (saved && saved.html) {
    if (body) body.innerHTML = saved.html;
    const dateEl = document.getElementById('an-saved-date');
    if (dateEl) dateEl.textContent = saved.savedAt + ' 저장됨';
    _refreshAnalysisBtns(true);
  } else {
    _doSosTrend();
    _refreshAnalysisBtns(false);
  }
}"""

count = src.count(OLD)
print(f'패턴 발견: {count}개')

if count == 0:
    print('ERROR: 패턴 없음')
    sys.exit(1)

src = src.replace(OLD, NEW, 1)

with open('output/report_2026_08.html', 'w', encoding='utf-8') as f:
    f.write(src)
print('JS 교체 완료')
