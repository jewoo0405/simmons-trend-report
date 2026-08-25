import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08.html', encoding='utf-8') as f:
    src = f.read()

# ── 1. 헤더 버튼 교체 ─────────────────────────────────────────
OLD_HEADER = '''    <!-- 헤더 -->
    <div class="analysis-header">
      <h2>시몬스 브랜드 트렌드 — 전략 분석<span class="ah-sub">2026년 08월</span></h2>
      <button class="an-print-btn" onclick="printAnalysis()">⎙ PDF 인쇄</button>
      <button class="an-close-btn" onclick="closeAnalysis()">✕</button>
    </div>'''

NEW_HEADER = '''    <!-- 헤더 -->
    <div class="analysis-header">
      <h2>시몬스 브랜드 트렌드 — 전략 분석<span class="ah-sub">2026년 08월</span></h2>
      <div class="an-action-group">
        <button class="an-run-btn"  id="btn-analyze" onclick="runAnalysis()" title="현재 데이터로 분석 내용을 불러옵니다">▶ 분석하기</button>
        <button class="an-save-btn" id="btn-save"    onclick="saveAnalysis()" title="현재 분석 내용을 저장합니다">💾 저장</button>
        <button class="an-edit-btn" id="btn-edit"    onclick="editAnalysis()" title="저장된 내용을 지우고 다시 분석합니다" style="display:none;">✏ 수정</button>
        <button class="an-print-btn" onclick="printAnalysis()">⎙ PDF 인쇄</button>
        <button class="an-close-btn" onclick="closeAnalysis()">✕</button>
      </div>
    </div>
    <!-- 저장 상태 배너 -->
    <div id="an-saved-banner" style="display:none;background:#e8f5e9;border:1px solid #a5d6a7;border-radius:6px;padding:7px 14px;font-size:11px;color:#1b5e20;margin-bottom:10px;display:none;">
      💾 <strong>저장된 분석</strong> — <span id="an-saved-date"></span> · 수정 버튼을 누르면 잠금이 해제됩니다.
    </div>'''

if OLD_HEADER not in src:
    print('ERROR: 헤더 패턴 없음')
    sys.exit(1)

src = src.replace(OLD_HEADER, NEW_HEADER, 1)
print('헤더 교체 완료')

# ── 2. CSS 추가 (analysis-overlay 스타일 블록 뒤에 삽입) ──────
OLD_CSS = '.analysis-overlay.open { display: flex; }'
NEW_CSS = '''.analysis-overlay.open { display: flex; }
.an-action-group { display:flex; align-items:center; gap:6px; margin-left:auto; }
.an-run-btn, .an-save-btn, .an-edit-btn {
  padding:6px 14px; border-radius:6px; font-size:12px; font-weight:600;
  cursor:pointer; border:1.5px solid; transition:all .15s;
}
.an-run-btn  { background:#1a1a2e; color:#fff; border-color:#1a1a2e; }
.an-run-btn:hover  { background:#2d2d4e; }
.an-save-btn { background:#2e7d32; color:#fff; border-color:#2e7d32; }
.an-save-btn:hover { background:#388e3c; }
.an-edit-btn { background:#fff; color:#c62828; border-color:#c62828; }
.an-edit-btn:hover { background:#ffebee; }'''

if OLD_CSS not in src:
    print('ERROR: CSS 패턴 없음')
    sys.exit(1)

src = src.replace(OLD_CSS, NEW_CSS, 1)
print('CSS 추가 완료')

# ── 3. JS 함수 교체 ───────────────────────────────────────────
OLD_JS = '''function openAnalysis() {
  document.getElementById('analysis-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
  // 전월 대비 구글 검색 지수 추세 (시몬스 기준)
  const trendEl = document.getElementById('an-sos-trend');'''

NEW_JS = '''// ── 분석 저장/불러오기 (localStorage) ──────────────────────
const ANALYSIS_KEY = 'simmons_analysis_saved_2026_08';

function _refreshAnalysisBtns(isSaved) {
  document.getElementById('btn-analyze').style.display = isSaved ? 'none' : '';
  document.getElementById('btn-save').style.display    = isSaved ? 'none' : '';
  document.getElementById('btn-edit').style.display    = isSaved ? ''     : 'none';
  const banner = document.getElementById('an-saved-banner');
  banner.style.display = isSaved ? 'flex' : 'none';
}

function runAnalysis() {
  // localStorage 무시하고 현재 HTML 분석 내용 표시
  const body = document.getElementById('analysis-body-content');
  if (body && body.dataset.original) {
    body.innerHTML = body.dataset.original;
  }
  _updateSosTrend();
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
    localStorage.setItem(ANALYSIS_KEY, JSON.stringify({ html: body.innerHTML, savedAt: stamp }));
    document.getElementById('an-saved-date').textContent = stamp + ' 저장됨';
    _refreshAnalysisBtns(true);
    // 저장 피드백
    const btn = document.getElementById('btn-save');
    btn.textContent = '✓ 저장됨';
    setTimeout(() => { btn.textContent = '💾 저장'; }, 1500);
  } catch(e) { alert('저장 실패: ' + e.message); }
}

function editAnalysis() {
  if (!confirm('저장된 분석을 삭제하고 현재 데이터로 다시 분석하시겠습니까?')) return;
  localStorage.removeItem(ANALYSIS_KEY);
  runAnalysis();
}

function _updateSosTrend() {
  const trendEl = document.getElementById('an-sos-trend');'''

OLD_JS_END = '''function openAnalysis() {
  document.getElementById('analysis-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
  // 전월 대비 구글 검색 지수 추세 (시몬스 기준)
  const trendEl = document.getElementById('an-sos-trend');'''

# 원래 openAnalysis 함수 끝 부분 찾아서 교체
OLD_OPENANALYSIS = '''function openAnalysis() {
  document.getElementById('analysis-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
  // 전월 대비 구글 검색 지수 추세 (시몬스 기준)
  const trendEl = document.getElementById('an-sos-trend');
  if (trendEl) {
    const ms = RAW.google?.monthly_series?.['시몬스'] || [];
    if (ms.length >= 2) {
      const last = ms[ms.length-1]?.value || 0;
      const prev = ms[ms.length-2]?.value || 0;
      const diff = last - prev;
      trendEl.textContent = diff >= 0
        ? '▲ 전월 대비 +' + diff.toFixed(1) + 'pt'
        : '▼ 전월 대비 ' + diff.toFixed(1) + 'pt';
      trendEl.style.color = diff >= 0 ? '#27ae60' : '#e74c3c';
    }
  }
}'''

NEW_OPENANALYSIS = '''function _updateSosTrend_inner() {
  const trendEl = document.getElementById('an-sos-trend');
  if (trendEl) {
    const ms = RAW.google?.monthly_series?.['시몬스'] || [];
    if (ms.length >= 2) {
      const last = ms[ms.length-1]?.value || 0;
      const prev = ms[ms.length-2]?.value || 0;
      const diff = last - prev;
      trendEl.textContent = diff >= 0
        ? '▲ 전월 대비 +' + diff.toFixed(1) + 'pt'
        : '▼ 전월 대비 ' + diff.toFixed(1) + 'pt';
      trendEl.style.color = diff >= 0 ? '#27ae60' : '#e74c3c';
    }
  }
}
function openAnalysis() {
  document.getElementById('analysis-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';

  // analysis-body-content에 원본 저장 (최초 1회)
  const body = document.getElementById('analysis-body-content');
  if (body && !body.dataset.original) {
    body.dataset.original = body.innerHTML;
  }

  // localStorage 저장본 확인
  const saved = (() => { try { return JSON.parse(localStorage.getItem(ANALYSIS_KEY)); } catch { return null; } })();
  if (saved && saved.html) {
    // 저장된 분석 표시
    if (body) body.innerHTML = saved.html;
    document.getElementById('an-saved-date').textContent = saved.savedAt + ' 저장됨';
    _refreshAnalysisBtns(true);
  } else {
    // 최신 분석 표시
    _updateSosTrend_inner();
    _refreshAnalysisBtns(false);
  }
}'''

if OLD_OPENANALYSIS not in src:
    # 대안: openAnalysis 함수 범위 수동 탐색
    print('WARNING: openAnalysis 정확 패턴 없음 — 대안 탐색')
    idx = src.find('function openAnalysis()')
    end = src.find('\nfunction ', idx + 10)
    print('openAnalysis 범위:', idx, '~', end)
    print(repr(src[idx:end]))
else:
    src = src.replace(OLD_OPENANALYSIS, NEW_OPENANALYSIS, 1)
    print('openAnalysis 교체 완료')

# ── 4. analysis-body div에 id 추가 ───────────────────────────
OLD_BODY = '    <!-- 본문 -->\n    <div class="analysis-body">'
NEW_BODY = '    <!-- 본문 -->\n    <div class="analysis-body">\n      <div id="analysis-body-content">'

src = src.replace(OLD_BODY, NEW_BODY, 1)

OLD_BODY_END = '''</div><!-- /analysis-body -->
  </div><!-- /analysis-box -->
</div><!-- /analysis-overlay -->'''
NEW_BODY_END = '''</div><!-- /analysis-body-content -->
    </div><!-- /analysis-body -->
  </div><!-- /analysis-box -->
</div><!-- /analysis-overlay -->'''

src = src.replace(OLD_BODY_END, NEW_BODY_END, 1)
print('analysis-body-content 래핑 완료')

# ── _updateSosTrend 중복 함수 처리 ───────────────────────────
# (앞서 추가한 _updateSosTrend 함수 + inner 버전 중 _updateSosTrend 빈 것 정리)
OLD_DUMMY = '''function _updateSosTrend() {
  const trendEl = document.getElementById('an-sos-trend');'''
NEW_DUMMY = '''function _updateSosTrend() { _updateSosTrend_inner(); }
function _UNUSED_updateSosTrend() {
  const trendEl = document.getElementById('an-sos-trend');'''

if OLD_DUMMY in src:
    src = src.replace(OLD_DUMMY, NEW_DUMMY, 1)
    print('_updateSosTrend 연결 완료')

with open('output/report_2026_08.html', 'w', encoding='utf-8') as f:
    f.write(src)
print('\n모두 저장 완료')
