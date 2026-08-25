import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08.html', encoding='utf-8') as f:
    src = f.read()

# ── 교체 범위: KPI 카드 행부터 실무 활용 요약 끝 hr 직전까지 ──────────────
OLD = '''      <!-- KPI 카드 요약 -->
      <div class="an-kpi-row">
        <div class="an-kpi-card akc-accent">
          <div class="akc-label">침대 전업 SoS</div>
          <div class="akc-val">58.4%</div>
          <div class="akc-sub">목표 60% · 갭 1.6%p</div>
          <div class="akc-sub" id="an-sos-trend" style="margin-top:3px;font-size:10px;"></div>
        </div>
        <div class="an-kpi-card">
          <div class="akc-label">전체 SoS</div>
          <div class="akc-val">8.5%</div>
          <div class="akc-sub">11개 브랜드 전체 기준</div>
        </div>
        <div class="an-kpi-card">
          <div class="akc-label">SoM (시장점유율)</div>
          <div class="akc-val">20.8%</div>
          <div class="akc-sub">DART 감사보고서 기준</div>
        </div>
        <div class="an-kpi-card">
          <div class="akc-label">ESOV 갭</div>
          <div class="akc-val" style="color:#27ae60;">+37.6%p</div>
          <div class="akc-sub">SoS − SoM (양수 = 성장 여력)</div>
        </div>
      </div>

      <hr class="an-divider">

      <!-- 1. 포지셔닝 진단 -->
      <div class="an-section">
        <h3><span class="an-num">1</span>브랜드 포지셔닝 진단 — 우리가 어디 서 있는가</h3>
        <p><strong>침대 전업 카테고리에서 시몬스는 검색 점유율 1위</strong>입니다. 에이스침대·씰리침대·지누스와 합산한 분모 기준으로 시몬스가 <strong>58.4%</strong>를 점유합니다. 직접 경쟁사 4개를 합쳤을 때 시몬스가 절반 이상을 차지한다는 수치를 객관적으로 제시합니다.</p>
        <div class="an-highlight">
          ✅ 이케아(구글 지수 716) · 한샘(216)은 <strong>가구·인테리어 전 품목을 다루는 종합 브랜드</strong>로, 침대 외 소파·수납·주방 등의 검색이 합산되어 지수가 높습니다. 침대 전업 4개 브랜드(시몬스·에이스침대·씰리침대·지누스)만 기준으로 하면 <strong>시몬스가 압도적 1위</strong>입니다.<br>
          ⚠ 전체 홈퍼니싱 시장 기준으로는 3위 — 비교 범위를 '침대'로 좁히느냐, '홈퍼니싱 전체'로 넓히느냐에 따라 시몬스의 포지션이 달라지므로 보고 목적에 맞게 구분해야 합니다.
        </div>
        <p>브랜드 회의, 임원 보고, 대외 커뮤니케이션에서 시몬스의 시장 지위를 <strong>감이 아닌 숫자로</strong> 설명할 수 있습니다.</p>
      </div>

      <!-- 2. ESOV 분석 -->
      <div class="an-section">
        <h3><span class="an-num">2</span>ESOV 분석 — 성장하고 있는가, 방어하고 있는가</h3>
        <p>Binet &amp; Field의 광고효과 이론에 따르면, <strong>SoS &gt; SoM 상태(양의 ESOV)가 지속되면 시장점유율이 장기적으로 SoS 수준으로 수렴하며 상승</strong>합니다.</p>
        <div class="an-highlight" style="background:#e8f5e9;border-color:#a5d6a7;color:#1b5e20;">
          📈 시몬스 SoS 58.4% &gt; SoM 20.8% → ESOV <strong>+37.6%p</strong><br>
          현재 마케팅이 효과를 내고 있고, <strong>지금 방향이 맞다</strong>는 데이터 증거입니다.
        </div>
        <p>반대로 에이스침대는 SoS·SoM이 균형에 가깝다면 이미 포화 단계에 가깝다는 의미입니다. 시몬스는 <strong>성장 구간</strong>에, 에이스침대는 <strong>방어 구간</strong>에 있을 가능성이 높습니다. 이 분석으로 마케팅 예산 증감 의사결정에 "우리가 어느 단계에 있는지"를 수치로 설명할 수 있습니다.</p>
      </div>

      <!-- 3. KPI 목표 -->
      <div class="an-section">
        <h3><span class="an-num">3</span>KPI 목표 관리 — 얼마나 더 가야 하는가</h3>
        <p>침대 전업 카테고리 SoS <strong>현재 58.4% → 목표 60%</strong> (갭 1.6%p). 이 1.6%p를 채우려면 에이스침대·지누스·씰리침대 중 어느 브랜드의 검색을 잠식해야 하는지를 월별로 추적할 수 있습니다.</p>
        <div class="an-highlight">
          📊 매달 이 수치가 <strong>오르면</strong> → 마케팅이 성과를 내는 중<br>
          📊 매달 이 수치가 <strong>떨어지면</strong> → 경쟁사 캠페인·이슈에 반응해야 한다는 신호
        </div>
        <p>"우리 마케팅 효과를 어떻게 측정할 것인가"라는 질문에 대한 <strong>단일 KPI</strong>를 제공합니다.</p>
      </div>

      <!-- 4. 연령대 분포 -->
      <div class="an-section">
        <h3><span class="an-num">4</span>연령대 분포 — 미래 고객이 오고 있는가</h3>
        <div class="an-warn">
          ⚠ <strong>시몬스 20+30대 검색 비중 22.2%</strong> vs 에이스침대 35.4%<br>
          브랜드 내 연령대 구성비(합계=100%) 기준 — 시몬스의 20·30대 비중이 에이스침대보다 낮습니다.
        </div>
        <p>시몬스의 현재 검색자 주력층은 <strong>40~60대 중심</strong>입니다. 이 고객들이 10년 후 은퇴하면 검색 기반 자체가 줄어듭니다. <strong>지금 20~30대 유입이 없으면 5~10년 후 브랜드 노후화 위험</strong>이 데이터로 실증됩니다.</p>
        <p>마케팅팀은 이 데이터를 근거로 "MZ세대 타겟 캠페인"의 필요성을 경영진에게 <strong>에이스침대 대비 수치 차이로</strong> 제시할 수 있습니다. 막연한 트렌드가 아닌 정량 근거입니다.</p>
        <p style="font-size:11px;color:#888;margin-top:4px;">※ 출처: Naver DataLab — <strong>네이버 로그인 사용자</strong> 기준 집계. 유튜브·인스타그램 등을 주로 이용하는 MZ세대 일부는 과소 반영될 수 있어 실제 격차는 더 클 수 있습니다.</p>
      </div>

      <!-- 5. 콘텐츠 생산성 -->
      <div class="an-section">
        <h3><span class="an-num">5</span>콘텐츠 생산성 — 검색 수요를 제대로 받아내고 있는가</h3>
        <p>Google 검색 수요 대비 네이버 콘텐츠 발행량 비율(카테고리 평균=100 재정규화)을 브랜드별로 비교합니다.</p>
        <div class="an-highlight">
          ▸ 검색 수요 &gt;&gt; 콘텐츠 발행량 → 검색 수요를 경쟁사에 빼앗기는 중<br>
          ▸ 검색 대비 콘텐츠 과잉 → 마케팅 예산이 필요 이상 집중된 상태
        </div>
        <p>이 지표로 콘텐츠 마케팅팀이 <strong>어느 브랜드·키워드에 콘텐츠를 더 써야 하는지 우선순위</strong>를 정할 수 있습니다.</p>
      </div>

      <!-- 6. 변화점 감지 -->
      <div class="an-section">
        <h3><span class="an-num">6</span>변화점 감지 — 무슨 일이 생겼는가</h3>
        <p>월별 검색 트렌드에서 급등·급락(±20% 이상)을 자동 감지합니다. 예를 들어:</p>
        <div class="an-highlight">
          ▸ 특정 월 에이스침대 검색 급등 → 신제품 출시? 가격 프로모션? 사건?<br>
          ▸ 시몬스 검색 일시 급락 → 부정 이슈? 경쟁사 이벤트 흡수?
        </div>
        <p>사후에 발견하는 것이 아니라 <strong>보고서가 나오는 시점에 자동으로 목록화</strong>되어 원인을 즉시 조사할 수 있습니다. CS팀 입장에서는 고객 문의가 늘기 전에 이슈를 인지하는 <strong>조기 경보 시스템</strong>으로 작동합니다.</p>
      </div>

      <!-- 7. 데이터 투명성 -->
      <div class="an-section">
        <h3><span class="an-num">7</span>데이터 투명성 — 이 숫자를 믿을 수 있는가</h3>
        <p>누군가 이 숫자에 "어디서 나온 거야?"라고 물었을 때 대답할 수 있는 근거가 보고서 안에 있습니다.</p>
        <div class="an-highlight">
          ✅ <strong>수집 기간 자동 표시</strong> — "최근 12개월"처럼 실제와 다른 표기 없음<br>
          ✅ <strong>부분 집계 배너</strong> — 월 중간 수집 데이터인지 명시<br>
          ✅ <strong>caution 브랜드 분리</strong> — 가구 전체 매출이 섞인 브랜드는 SoM에서 제외·별도 표기<br>
          ✅ <strong>배치 정규화 비율 공개</strong> — Google Trends 체인 링킹 방식·신뢰도 부록 명시
        </div>
        <p>경영진 보고 및 마케팅 대행사 회의에서 <strong>신뢰도</strong>를 높이는 요소입니다.</p>
      </div>

      <hr class="an-divider">

      <!-- 8. 실무 활용 요약 -->
      <div class="an-section">
        <h3><span class="an-num">8</span>실무 활용 요약</h3>
        <table class="an-table">
          <thead>
            <tr><th>상황</th><th>이 보고서로 할 수 있는 것</th><th>중요도</th></tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>경영진 보고</strong></td>
              <td>SoS 58.4%, SoM 20.8%, ESOV +37.6%p → 현재 마케팅 방향이 맞다는 증거</td>
              <td><span class="an-tag an-tag-r">높음</span></td>
            </tr>
            <tr>
              <td><strong>예산 협의</strong></td>
              <td>KPI 60% 목표까지 1.6%p 남음 → 추가 투자의 논거</td>
              <td><span class="an-tag an-tag-r">높음</span></td>
            </tr>
            <tr>
              <td><strong>MZ 캠페인 기획</strong></td>
              <td>20대 비중 에이스침대 대비 열위 → 젊은층 타겟 필요성의 정량 근거</td>
              <td><span class="an-tag an-tag-r">높음</span></td>
            </tr>
            <tr>
              <td><strong>콘텐츠팀 방향</strong></td>
              <td>검색 수요 대비 콘텐츠 생산성 비율 → 어느 키워드에 집중할지 우선순위</td>
              <td><span class="an-tag an-tag-o">중간</span></td>
            </tr>
            <tr>
              <td><strong>이슈 모니터링</strong></td>
              <td>변화점 자동 감지 → 경쟁사 이상 신호 조기 포착</td>
              <td><span class="an-tag an-tag-o">중간</span></td>
            </tr>
            <tr>
              <td><strong>월간 루틴 의사결정</strong></td>
              <td>매월 5일 자동 발송 → 데이터 없이 감으로 결정하던 것을 수치 기반으로 전환</td>
              <td><span class="an-tag an-tag-g">기반</span></td>
            </tr>
          </tbody>
        </table>
        <p style="margin-top:14px;font-size:12px;color:#888;">
          핵심 요약: <strong>"시몬스는 침대 전업에서 검색 1위인데, 매출 점유율은 아직 그만큼 오지 않았다."</strong><br>
          이 갭이 위협인지 기회인지를 매달 추적하면서, 마케팅 투자를 어디에 얼마나 해야 할지 근거를 만드는 것이 이 대시보드의 존재 이유입니다.
        </p>
      </div>'''

NEW = '''      <!-- KPI 카드 요약 -->
      <div class="an-kpi-row">
        <div class="an-kpi-card akc-accent">
          <div class="akc-label">침대 전업 검색 점유율</div>
          <div class="akc-val">58.4%</div>
          <div class="akc-sub">목표 60% · 갭 1.6%p</div>
          <div class="akc-sub" id="an-sos-trend" style="margin-top:3px;font-size:10px;"></div>
        </div>
        <div class="an-kpi-card">
          <div class="akc-label">전체 홈퍼니싱 검색 점유율</div>
          <div class="akc-val">8.5%</div>
          <div class="akc-sub">11개 브랜드 전체 기준</div>
        </div>
        <div class="an-kpi-card">
          <div class="akc-label">시장 매출 점유율</div>
          <div class="akc-val">20.8%</div>
          <div class="akc-sub">매트리스 전업 3사 매출 기준</div>
        </div>
        <div class="an-kpi-card">
          <div class="akc-label">검색 − 매출 격차</div>
          <div class="akc-val" style="color:#27ae60;">+37.6%p</div>
          <div class="akc-sub">검색 점유율이 매출 점유율보다 높음</div>
        </div>
      </div>

      <hr class="an-divider">

      <!-- 1. 브랜드 검색 순위 -->
      <div class="an-section">
        <h3><span class="an-num">1</span>브랜드 검색 순위 — 소비자들이 침대 살 때 누구를 찾는가</h3>
        <p>침대 브랜드 4개(시몬스·에이스침대·씰리침대·지누스)의 구글 검색량을 합쳤을 때, 시몬스가 <strong>58.4%</strong>를 차지합니다. 소비자 10명이 침대를 검색할 때 약 6명이 시몬스를 찾는다는 뜻입니다.</p>
        <div class="an-highlight">
          ✅ <strong>침대 전문 브랜드 중 검색 1위</strong> — 에이스침대(19.2%), 지누스(21.4%), 씰리침대(0.9%)와 비교해 압도적 우위<br>
          ⚠ <strong>이케아·한샘이 전체 순위에서 1·2위인 이유</strong> — 이 두 브랜드는 침대뿐 아니라 소파·책상·주방 등 집 안의 모든 가구를 다루기 때문에 검색량이 훨씬 많습니다. 침대만 비교하면 시몬스가 1위입니다.
        </div>
        <p>경영진 보고나 외부 발표에서 <strong>"침대 브랜드 1위"</strong>라고 할 때 이 수치를 근거로 사용할 수 있습니다.</p>
      </div>

      <!-- 2. 콘텐츠 공급량 -->
      <div class="an-section">
        <h3><span class="an-num">2</span>콘텐츠 공급량 — 소비자 관심에 맞게 콘텐츠를 쏟고 있는가</h3>
        <p>구글 검색 관심도(소비자 수요)와 네이버 블로그·카페 콘텐츠 발행량을 브랜드별로 비교합니다. 수요보다 콘텐츠가 적으면 경쟁사 콘텐츠에 자리를 빼앗기고, 반대면 예산이 과다 투입된 상태입니다.</p>
        <div class="an-highlight">
          ▸ <strong>시몬스 +73.9</strong> — 구글 검색 수요 대비 네이버 콘텐츠가 충분히 공급됨<br>
          ▸ <strong>에이스침대 +163.0</strong> — 에이스침대는 네이버 콘텐츠를 훨씬 더 공격적으로 운영 중<br>
          ▸ <strong>이케아 −410.9</strong> — 구글에서 많이 찾지만 네이버 콘텐츠는 적음 (글로벌 브랜드 특성)
        </div>
        <p>콘텐츠팀이 "이번 달 어느 키워드에 블로그 글을 써야 하나?"를 결정할 때 <strong>데이터 근거</strong>로 쓸 수 있습니다.</p>
      </div>

      <!-- 3. 월별 검색 흐름 -->
      <div class="an-section">
        <h3><span class="an-num">3</span>월별 검색 흐름 — 경쟁사에 무슨 일이 있었나</h3>
        <p>매달 각 브랜드의 검색량이 얼마나 오르고 내렸는지를 추적합니다. 갑자기 크게 오르거나(+20% 이상) 크게 떨어지면(−20% 이상) 원인을 파악해야 합니다.</p>
        <div class="an-highlight">
          ▸ <strong>경쟁사 검색 급등</strong> → 신제품 출시? 가격 할인? 이슈 발생?<br>
          ▸ <strong>시몬스 검색 급락</strong> → 부정 이슈? 경쟁사 이벤트에 소비자 관심 분산?
        </div>
        <p>고객 문의가 갑자기 늘기 전에 먼저 알 수 있는 <strong>조기 경보 시스템</strong>입니다. CS팀에서 "이번 달 왜 이런 문의가 많지?"를 사전에 예측하는 데 활용할 수 있습니다.</p>
      </div>

      <!-- 4. 연령대 분포 -->
      <div class="an-section">
        <h3><span class="an-num">4</span>연령대 분포 — 미래 고객이 오고 있는가</h3>
        <div class="an-warn">
          ⚠ <strong>시몬스를 검색하는 사람 중 20·30대 비중 22.2%</strong> — 에이스침대는 같은 비중이 35.4%<br>
          시몬스 검색자 주력층은 <strong>40~60대(75.8%)</strong>에 집중되어 있습니다.
        </div>
        <p>지금 시몬스를 주로 찾는 40~60대 고객이 10년 후 은퇴하면 검색 관심 자체가 줄어듭니다. <strong>지금 20~30대를 시몬스 브랜드에 익숙하게 만들지 않으면 5~10년 후 브랜드 노후화 위험</strong>이 데이터로 나타납니다.</p>
        <p>"MZ 세대 마케팅이 왜 필요한가"라는 질문에 감이 아닌 <strong>숫자 근거</strong>로 경영진에게 설명할 수 있습니다.</p>
        <p style="font-size:11px;color:#888;margin-top:4px;">※ 출처: Naver DataLab — 네이버 로그인 사용자 기준. 유튜브·인스타그램 중심의 MZ세대 일부는 과소 집계될 수 있어 실제 격차는 더 클 수 있습니다.</p>
      </div>

      <!-- 5. 검색 vs 매출 격차 -->
      <div class="an-section">
        <h3><span class="an-num">5</span>검색 점유율 vs 매출 점유율 — 마케팅이 제대로 돌고 있는가</h3>
        <p>검색 점유율(얼마나 많이 찾느냐)과 실제 매출 점유율(얼마나 많이 파느냐)을 비교합니다. 검색 점유율이 매출보다 높으면 브랜드에 관심은 있는데 아직 구매로 이어지지 않는 성장 가능성이 있는 상태입니다.</p>
        <div class="an-highlight" style="background:#e8f5e9;border-color:#a5d6a7;color:#1b5e20;">
          📈 <strong>시몬스: 검색 58.4% &gt; 매출 20.8%</strong> → 격차 <strong>+37.6%p</strong><br>
          소비자들이 시몬스를 많이 찾고 있고, 지금 마케팅 방향이 맞다는 증거입니다. 이 격차가 유지되면 장기적으로 매출 점유율도 올라갈 가능성이 높습니다.
        </div>
        <div class="an-highlight" style="background:#fff8e1;border-color:#ffe082;">
          📊 <strong>에이스침대: 검색 19.2% ≈ 매출 20.4%</strong> → 격차 <strong>−1.2%p</strong><br>
          검색과 매출이 거의 일치 → 이미 안정된 시장을 지키는 단계. 시몬스처럼 성장 여력이 큰 상태가 아닙니다.
        </div>
        <p>이 데이터로 "우리 마케팅이 효과가 있냐"라는 질문에 수치로 답할 수 있습니다.</p>
        <p style="font-size:11px;color:#888;margin-top:4px;">※ 매출 점유율: 매트리스 전업 3사(시몬스·에이스침대·지누스) 합계 매출 15,544억 기준. 한샘·현대리바트 등 가구 종합 매출은 제외.</p>
      </div>

      <!-- 6. KPI 목표 -->
      <div class="an-section">
        <h3><span class="an-num">6</span>KPI 목표 — 얼마나 더 가야 하는가</h3>
        <p>침대 브랜드 검색 점유율 <strong>현재 58.4% → 목표 60%</strong> (1.6%p 남음)</p>
        <div class="an-highlight">
          📊 이 수치가 <strong>매달 오르면</strong> → 마케팅이 성과를 내는 중<br>
          📊 이 수치가 <strong>떨어지면</strong> → 경쟁사 캠페인 또는 이슈에 반응해야 한다는 신호
        </div>
        <p>마케팅 성과를 하나의 숫자로 추적할 수 있는 <strong>월간 핵심 지표</strong>입니다. 목표치까지 1.6%p — 지금 어느 경쟁사의 검색을 잠식하면 달성할 수 있는지도 월별 추이로 확인 가능합니다.</p>
      </div>

      <!-- 7. 데이터 신뢰도 -->
      <div class="an-section">
        <h3><span class="an-num">7</span>데이터 신뢰도 — 이 숫자를 믿어도 되는가</h3>
        <p>"이 수치 어디서 나온 거야?"라는 질문을 받았을 때 대답할 수 있도록 출처와 기준을 보고서 안에 모두 담았습니다.</p>
        <div class="an-highlight">
          ✅ <strong>출처 명시</strong> — 구글 트렌드, Naver DataLab, DART 감사보고서(비상장사 포함)<br>
          ✅ <strong>월 중간 수집 여부 표시</strong> — 월말 확정 전 데이터라면 배너로 안내<br>
          ✅ <strong>종합 가구사 매출 분리</strong> — 한샘·현대리바트처럼 가구 전체 매출이 섞인 브랜드는 매출 점유율 계산에서 제외<br>
          ✅ <strong>구글 트렌드 측정 방식 공개</strong> — 부록에 배치 구성 및 신뢰도 점수 명시
        </div>
        <p>경영진 보고 및 외부 발표에서 <strong>숫자 신뢰도</strong>를 뒷받침하는 근거입니다.</p>
      </div>

      <hr class="an-divider">

      <!-- 8. 실무 활용 요약 -->
      <div class="an-section">
        <h3><span class="an-num">8</span>실무 활용 요약</h3>
        <table class="an-table">
          <thead>
            <tr><th>상황</th><th>이 보고서로 할 수 있는 것</th><th>중요도</th></tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>경영진 보고</strong></td>
              <td>검색 1위 58.4%, 매출 점유율 20.8% → 마케팅 방향이 맞다는 데이터 근거</td>
              <td><span class="an-tag an-tag-r">높음</span></td>
            </tr>
            <tr>
              <td><strong>예산 협의</strong></td>
              <td>목표 60%까지 1.6%p 남음 → 추가 투자의 정량 논거 제시 가능</td>
              <td><span class="an-tag an-tag-r">높음</span></td>
            </tr>
            <tr>
              <td><strong>MZ 캠페인 기획</strong></td>
              <td>20·30대 비중 에이스침대(35.4%)보다 낮음(22.2%) → 젊은층 타겟 필요성 수치 입증</td>
              <td><span class="an-tag an-tag-r">높음</span></td>
            </tr>
            <tr>
              <td><strong>콘텐츠팀 방향</strong></td>
              <td>에이스침대(+163)가 시몬스(+74)보다 네이버 콘텐츠 공세 강함 → 대응 여부 판단</td>
              <td><span class="an-tag an-tag-o">중간</span></td>
            </tr>
            <tr>
              <td><strong>이슈 모니터링</strong></td>
              <td>월별 검색 급변 자동 감지 → CS 문의 급증 전 조기 파악</td>
              <td><span class="an-tag an-tag-o">중간</span></td>
            </tr>
            <tr>
              <td><strong>월간 루틴 점검</strong></td>
              <td>매월 자동 발송 → 감이 아닌 수치로 브랜드 상태 점검</td>
              <td><span class="an-tag an-tag-g">기반</span></td>
            </tr>
          </tbody>
        </table>
        <p style="margin-top:14px;font-size:12px;color:#888;">
          한 줄 요약: <strong>"시몬스는 침대 브랜드 중 검색 1위지만, 실제 매출 점유율은 아직 따라오지 않았다."</strong><br>
          이 격차가 기회인지 위기인지를 매달 추적하면서, 마케팅 투자 방향을 데이터로 결정하는 것이 이 대시보드의 목적입니다.
        </p>
      </div>'''

count = src.count(OLD)
print(f'패턴 발견: {count}개')
if count == 0:
    # 디버그: 첫 100자 비교
    idx = src.find('<!-- KPI 카드 요약 -->')
    print(f'KPI 카드 위치: {idx}')
    if idx > 0:
        print(repr(src[idx:idx+200]))
    sys.exit(1)

src = src.replace(OLD, NEW, 1)
with open('output/report_2026_08.html', 'w', encoding='utf-8') as f:
    f.write(src)
print('분석 내용 재작성 완료')
