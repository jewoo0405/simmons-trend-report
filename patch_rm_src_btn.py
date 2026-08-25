import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08.html', encoding='utf-8') as f:
    src = f.read()

OLD = '''  <!-- 부록 구분선 + 분석 버튼 -->
  <div style="margin:32px 0 0;display:flex;align-items:center;gap:16px;">
    <div style="flex:1;height:2px;background:linear-gradient(90deg,#1a1a2e 0%,#c8a96e 50%,transparent 100%);border-radius:2px;"></div>
    <button onclick="openAnalysis()" style="
      flex-shrink:0;
      background:#1a1a2e;color:#fff;
      border:none;border-radius:8px;
      padding:10px 22px;font-size:13px;font-weight:700;
      cursor:pointer;letter-spacing:.3px;
      box-shadow:0 2px 8px rgba(0,0,0,.18);
      transition:background .15s;
      white-space:nowrap;"
      onmouseover="this.style.background='#2d2d4e'"
      onmouseout="this.style.background='#1a1a2e'">
      📋 분석 내용 보기
    </button>
    <div style="flex:1;height:2px;background:linear-gradient(90deg,transparent 0%,#c8a96e 50%,#1a1a2e 100%);border-radius:2px;"></div>
  </div>

  <!-- 부록 섹션 (T3-1) -->'''

NEW = '''  <!-- 부록 섹션 (T3-1) -->'''

count = src.count(OLD)
print(f'패턴 발견: {count}개')
if count:
    src = src.replace(OLD, NEW, 1)
    with open('output/report_2026_08.html', 'w', encoding='utf-8') as f:
        f.write(src)
    print('소스 중복 버튼 제거 완료')
else:
    print('이미 제거됨')
