import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08.html', encoding='utf-8') as f:
    src = f.read()

START = '<!-- 부록 섹션 (T3-1) -->'
s = src.find(START)
if s == -1:
    print('ERROR: 부록 시작 태그를 찾을 수 없음')
    sys.exit(1)

# 부록 섹션 끝: section-appendix div 닫는 곳 찾기
# </div>\n    </div>\n\n</div><!-- /wrap --> 패턴으로 찾기
END_MARKER = '</div>\n\n</div><!-- /'
e = src.find(END_MARKER, s)
if e == -1:
    # 대안 패턴
    END_MARKER = '</div>\n</div><!-- /'
    e = src.find(END_MARKER, s)
if e == -1:
    print('ERROR: 부록 끝 마커를 찾을 수 없음 — 앞뒤 500자 확인:')
    print(repr(src[s:s+500]))
    sys.exit(1)

print(f'부록 시작: {s}, 끝: {e}')
print(f'교체 대상 길이: {e - s} 자')

NEW_APPENDIX = '''<!-- 부록 섹션 (T3-1) -->
  <div class="chart-row" id="section-appendix">
    <div class="card">
      <div class="card-title">부록 — 방법론 및 데이터 소스</div>
      <div class="card-sub">수집 기준 \xb7 산출식 \xb7 데이터 한계 공개 / 수집: 2026.08.25 \xb7 대상: 12개 브랜드</div>

      <!-- ① 수집 대상 브랜드 -->
      <div class="section-title" style="margin-top:16px;">① 수집 대상 브랜드 (12개)</div>
      <table class="data-table" style="margin-bottom:20px;">
        <thead><tr>
          <th style="width:50px;">Tier</th>
          <th style="width:130px;">브랜드</th>
          <th style="width:80px;">카테고리</th>
          <th>수집 키워드 (Naver DataLab / Google Trends 공통)</th>
        </tr></thead>
        <tbody>
        <tr style="background:#fffde7;">
          <td style="text-align:center;font-weight:bold;">A</td>
          <td style="font-weight:bold;">시몬스 ★기준</td>
          <td>침대 전업</td>
          <td><code>시몬스</code> / <code>시몬스침대</code> / <code>시몬스 침대</code> / <code>시몬스 매트리스</code> / <code>SIMMONS</code> / <code>뷰티레스트</code></td>
        </tr>
        <tr>
          <td style="text-align:center;">A</td>
          <td>씰리침대</td>
          <td>침대 전업</td>
          <td><code>씰리침대</code> / <code>씰리 침대</code> / <code>씰리 매트리스</code> / <code>SEALY</code> / <code>씰리</code> / <code>Sealy</code></td>
        </tr>
        <tr style="background:#fff8e7;">
          <td style="text-align:center;color:#8b1538;font-weight:bold;">A</td>
          <td style="color:#8b1538;font-weight:bold;">템퍼 <span style="font-size:10px;background:#8b1538;color:#fff;padding:1px 4px;border-radius:3px;">2026-08 신규</span></td>
          <td>침대 전업</td>
          <td><code>템퍼</code> / <code>템퍼침대</code> / <code>템퍼 매트리스</code> / <code>Tempur</code></td>
        </tr>
        <tr>
          <td style="text-align:center;">B</td>
          <td>에이스침대</td>
          <td>침대 전업</td>
          <td><code>에이스침대</code> / <code>에이스 침대</code> / <code>에이스 매트리스</code> / <code>ACE침대</code>
            <div style="color:#e74c3c;font-size:10px;margin-top:3px;"><s>에이스·ACE 단독</s> — 동음이의 위험으로 제외</div></td>
        </tr>
        <tr>
          <td style="text-align:center;">B</td>
          <td>에몬스</td>
          <td>침대 전업</td>
          <td><code>에몬스</code> / <code>에몬스 가구</code> / <code>에몬스 침대</code> / <code>EMONS</code> / <code>에몬스침대</code></td>
        </tr>
        <tr>
          <td style="text-align:center;">B</td>
          <td>지누스</td>
          <td>침대 전업</td>
          <td><code>지누스</code> / <code>지누스 매트리스</code> / <code>Zinus</code> / <code>zinus</code> / <code>지누스침대</code></td>
        </tr>
        <tr>
          <td style="text-align:center;color:#888;">C</td>
          <td style="color:#888;">한샘</td>
          <td style="color:#888;">종합가구</td>
          <td style="color:#888;"><code>한샘 침대</code> / <code>한샘 매트리스</code> / <code>HANSEM</code>
            <div style="color:#e65100;font-size:10px;margin-top:3px;">⚠ '한샘' 단독 금지 — 가구·인테리어 카테고리 오염</div></td>
        </tr>
        <tr>
          <td style="text-align:center;color:#888;">C</td>
          <td style="color:#888;">현대리바트</td>
          <td style="color:#888;">종합가구</td>
          <td style="color:#888;"><code>현대리바트 침대</code> / <code>리바트 침대</code> / <code>리바트 매트리스</code></td>
        </tr>
        <tr>
          <td style="text-align:center;color:#888;">C</td>
          <td style="color:#888;">까사미아</td>
          <td style="color:#888;">종합가구</td>
          <td style="color:#888;"><code>까사미아 침대</code> / <code>까사미아 매트리스</code></td>
        </tr>
        <tr>
          <td style="text-align:center;color:#888;">C</td>
          <td style="color:#888;">일룸</td>
          <td style="color:#888;">종합가구</td>
          <td style="color:#888;"><code>일룸 침대</code> / <code>일룸 매트리스</code></td>
        </tr>
        <tr>
          <td style="text-align:center;color:#888;">C</td>
          <td style="color:#888;">이케아</td>
          <td style="color:#888;">종합가구</td>
          <td style="color:#888;"><code>이케아 침대</code> / <code>이케아 매트리스</code> / <code>IKEA</code>
            <div style="color:#e65100;font-size:10px;margin-top:3px;">⚠ '이케아' 단독 금지 — 가구 전반 카테고리 오염</div></td>
        </tr>
        <tr>
          <td style="text-align:center;color:#2563eb;">D</td>
          <td style="color:#2563eb;">코웨이 비렉스</td>
          <td style="color:#2563eb;">렌털</td>
          <td style="color:#2563eb;"><code>코웨이 비렉스</code> / <code>비렉스</code> / <code>코웨이 매트리스</code>
            <div style="color:#e65100;font-size:10px;margin-top:3px;">⚠ 렌털 모델 — 온라인 검색 의존도 낮아 Google Trends 지수 매우 낮음 (≈0.2%)</div></td>
        </tr>
        </tbody>
      </table>

      <!-- ② Google Trends 배치 구성 -->
      <div class="section-title" style="margin-top:16px;">② Google Trends 배치 구성 (체인 링킹)</div>
      <div style="font-size:11px;color:#666;margin-bottom:8px;">
        Google Trends는 배치당 최대 5개 키워드 제한. 브리지 브랜드를 통해 배치 간 스케일을 연결하고 시몬스=100으로 최종 정규화.<br>
        <strong style="color:#2e7d32;">배치 E·F는 2026-08-25 기준 시몬스 직접 앵커로 재설계 — 씰리침대 브리지 신호 약함(≤1.5) 문제 해결.</strong>
      </div>
      <table class="data-table" style="margin-bottom:20px;">
        <thead><tr>
          <th style="width:60px;">배치</th>
          <th>수집 브랜드</th>
          <th style="width:130px;">다음 배치 브리지</th>
          <th>비고</th>
        </tr></thead>
        <tbody>
        <tr>
          <td style="text-align:center;font-weight:bold;">A</td>
          <td><code>시몬스</code> · <code>일룸</code> · <code>까사미아</code> · <code>에이스침대</code> · <code>지누스</code></td>
          <td style="color:#2e7d32;font-weight:600;">시몬스 → B</td>
          <td>1차 앵커 배치. 시몬스 기준점</td>
        </tr>
        <tr>
          <td style="text-align:center;font-weight:bold;">B</td>
          <td><code>시몬스</code> · <code>이케아</code> · <code>한샘</code></td>
          <td style="color:#2e7d32;font-weight:600;">시몬스 → C</td>
          <td>대형 브랜드 (이케아 최대값)</td>
        </tr>
        <tr>
          <td style="text-align:center;font-weight:bold;">C</td>
          <td><code>시몬스</code> · <code>에몬스</code></td>
          <td style="color:#f57c00;font-weight:600;">에몬스 → D</td>
          <td>소형 상위. 에몬스 D배치 브리지</td>
        </tr>
        <tr>
          <td style="text-align:center;font-weight:bold;">D</td>
          <td><code>에몬스</code> · <code>현대리바트</code> · <code>씰리침대</code></td>
          <td style="color:#1565c0;font-weight:600;">씰리침대 → E</td>
          <td>소형 하위. 씰리침대 E배치 브리지</td>
        </tr>
        <tr style="background:#f1f8e9;">
          <td style="text-align:center;font-weight:bold;">E</td>
          <td><code>시몬스</code> · <code>씰리침대</code> · <code>코웨이 비렉스</code></td>
          <td style="color:#2e7d32;font-weight:600;">시몬스 → F</td>
          <td style="color:#2e7d32;">2026-08 개선: 시몬스 직접 앵커 추가 — 코웨이비렉스 신뢰도 향상</td>
        </tr>
        <tr style="background:#fff8e7;">
          <td style="text-align:center;font-weight:bold;color:#8b1538;">F</td>
          <td><code>시몬스</code> · <code>템퍼</code></td>
          <td style="color:#2e7d32;font-weight:600;">시몬스 직접</td>
          <td style="color:#8b1538;font-weight:600;">2026-08 신규: 씰리침대 브리지 체인 끊김 해결 → 시몬스 직접 앵커로 템퍼 수집</td>
        </tr>
        </tbody>
      </table>

      <!-- ③ 지표 산출식 -->
      <div class="section-title" style="margin-top:16px;">③ 지표 산출식</div>
      <table class="data-table" style="margin-bottom:20px;">
        <thead><tr>
          <th style="width:160px;">지표</th>
          <th style="width:280px;">산출식</th>
          <th>설명</th>
        </tr></thead>
        <tbody>
        <tr>
          <td>Share of Search (SoS)</td>
          <td style="font-family:monospace;font-size:11px;">SoS(B) = 지수(B) / Σ지수(전체) × 100</td>
          <td>브랜드별 구글 검색 점유율. 전체 합계=100%</td>
        </tr>
        <tr>
          <td>SoS 카테고리 (침대 전업)</td>
          <td style="font-family:monospace;font-size:11px;">SoS_cat(B) = 지수(B) / Σ지수(Tier A·B) × 100</td>
          <td>Tier C·D 종합가구·렌털 제외, 침대 전업(Tier A·B)만 분모 사용</td>
        </tr>
        <tr>
          <td>Share of Market (SoM)</td>
          <td style="font-family:monospace;font-size:11px;">SoM(B) = 매출(B) / Σ매출(6개사) × 100</td>
          <td>FY2025 DART 공시 기준. 6개사: 코웨이비렉스·시몬스·에이스침대·템퍼·씰리침대·지누스</td>
        </tr>
        <tr>
          <td>ESOV (초과 SoV)</td>
          <td style="font-family:monospace;font-size:11px;">ESOV = SoS − SoM</td>
          <td>양(+) = 검색이 매출보다 많음(성장 여력) / 음(−) = 매출이 검색보다 많음(오프라인 강자)</td>
        </tr>
        <tr>
          <td>카테고리 인덱스</td>
          <td style="font-family:monospace;font-size:11px;">인덱스(B,G) = 브랜드값(B,G) / 카테고리평균(G) × 100</td>
          <td>성별·연령 인덱스 모드. 카테고리 평균=100 기준</td>
        </tr>
        <tr>
          <td>구글 vs 네이버 갭</td>
          <td style="font-family:monospace;font-size:11px;">Gap = N_cat − G_cat (각 카테고리 평균=100 재정규화)</td>
          <td>양(+) = 검색 대비 콘텐츠 과다 / 음(−) = 검색 대비 콘텐츠 부족</td>
        </tr>
        </tbody>
      </table>

      <!-- ④ 데이터 소스별 특성 및 한계 -->
      <div class="section-title" style="margin-top:16px;">④ 데이터 소스별 특성 및 한계</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px;margin-bottom:20px;">
        <div style="background:#f9f9f9;border-radius:6px;padding:12px;border-left:3px solid #2e7d32;">
          <div style="font-weight:bold;font-size:12px;margin-bottom:6px;">Google Trends</div>
          <div style="font-size:11px;color:#555;line-height:1.7;">표본 기반 상대지수 (절대 검색량 아님). 배치 6개로 분리 수집 후 체인 링킹으로 통합. 시몬스=100 기준 정규화. 코웨이 비렉스는 신호 약해(≤1.5) 해상도 한계 존재. 템퍼는 배치 F(시몬스 직접 앵커)로 안정 수집.</div>
        </div>
        <div style="background:#f9f9f9;border-radius:6px;padding:12px;border-left:3px solid #1565c0;">
          <div style="font-weight:bold;font-size:12px;margin-bottom:6px;">Naver 콘텐츠 노출량 (블로그+뉴스)</div>
          <div style="font-size:11px;color:#555;line-height:1.7;">검색 수요가 아닌 콘텐츠 발행량 측정. 브랜드 마케팅 활동량 반영. Naver 검색 API 기준. 이케아·한샘·에이스침대는 복합 키워드만 허용.</div>
        </div>
        <div style="background:#f9f9f9;border-radius:6px;padding:12px;border-left:3px solid #9b59b6;">
          <div style="font-weight:bold;font-size:12px;margin-bottom:6px;">Naver DataLab (성별·연령)</div>
          <div style="font-size:11px;color:#555;line-height:1.7;">DataLab 검색 관심도 기준. 실구매 데이터 아님. 배치당 최대 5개 브랜드. 시몬스를 모든 배치 첫 번째(앵커)로 고정해 배치 간 비교 가능. 수집 기간: 최근 3개월.</div>
        </div>
        <div style="background:#f9f9f9;border-radius:6px;padding:12px;border-left:3px solid #c8a96e;">
          <div style="font-weight:bold;font-size:12px;margin-bottom:6px;">매출 데이터 (SoM)</div>
          <div style="font-size:11px;color:#555;line-height:1.7;">DART 공시 기준 6개사 FY2023–2025. ★추정 표기 브랜드(코웨이비렉스·템퍼·지누스)는 IR·사측 발표 기반 추정치. 비상장·비공시 브랜드는 SoM 산출 제외.</div>
        </div>
      </div>

      <!-- ⑤ 지표 정의집 -->
      <div class="section-title" style="margin-top:8px;">⑤ 지표 정의집</div>
      <table class="appendix-table">
        <thead>
          <tr><th>지표명</th><th>산출식</th><th>출처</th><th>갱신 주기</th><th>한계</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>Share of Search (SoS)</td>
            <td>자사 검색량 ÷ 전체 브랜드 합 × 100</td>
            <td>Google Trends (KR)</td>
            <td>월 1회</td>
            <td>표본 기반 상대값, Tier C 포함 시 카테고리 오염</td>
          </tr>
          <tr>
            <td>SoS 카테고리</td>
            <td>자사 검색량 ÷ 침대 전업(Tier A·B) 합 × 100</td>
            <td>Google Trends (KR)</td>
            <td>월 1회</td>
            <td>Tier A·B 중 Google Trends 데이터 있는 브랜드만 분모 포함</td>
          </tr>
          <tr>
            <td>Share of Market (SoM)</td>
            <td>자사 FY매출 ÷ 6개사 합계 × 100</td>
            <td>DART 공시 / IR 추정★</td>
            <td>연 1회 (FY 결산)</td>
            <td>★추정 브랜드(코웨이비렉스·템퍼·지누스) 오차 가능</td>
          </tr>
          <tr>
            <td>구글 검색 지수</td>
            <td>시몬스=100 기준 상대지수</td>
            <td>Google Trends (KR)</td>
            <td>월 1회</td>
            <td>표본 기반 상대값, 절대 검색량 아님</td>
          </tr>
          <tr>
            <td>네이버 콘텐츠 노출량</td>
            <td>블로그 건수 + 뉴스 건수</td>
            <td>Naver 검색 API</td>
            <td>월 1회</td>
            <td>마케팅 물량 반영, 검색 수요 아님</td>
          </tr>
          <tr>
            <td>성별·연령 인덱스</td>
            <td>(브랜드 비율 ÷ 카테고리 평균) × 100</td>
            <td>Naver DataLab</td>
            <td>월 1회 (최근 3개월)</td>
            <td>DataLab 관심도 기준, 실구매 반영 안 됨</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

'''

result = src[:s] + NEW_APPENDIX + src[e:]
print(f'원본: {len(src):,}자 → 수정: {len(result):,}자')
print(f'부록 섹션: {len(NEW_APPENDIX):,}자')

with open('output/report_2026_08.html', 'w', encoding='utf-8') as f:
    f.write(result)
print('저장 완료')
