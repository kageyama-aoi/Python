// ─────────────────────────────────────────────
// CHART RENDER HELPERS
// ─────────────────────────────────────────────
function renderDateHeader(chart, allDates, lectures, dateToFrac, fracToPercent) {
  const dateRow = document.createElement('div');
  dateRow.className = 'date-row';
  const labelSpacer = document.createElement('div');
  labelSpacer.className = 'row-label-col';
  dateRow.appendChild(labelSpacer);

  const datesCol = document.createElement('div');
  datesCol.className = 'dates-col';
  allDates.forEach(d => {
    const cell = document.createElement('div');
    cell.className = 'date-cell' + (lectures.includes(d) ? ' is-lecture' : '');
    cell.textContent = d;
    datesCol.appendChild(cell);
  });
  dateRow.appendChild(datesCol);
  chart.appendChild(dateRow);
}

function renderLectureRow(chart, allDates, lectures, dateToFrac, fracToPercent) {
  const lecRow = document.createElement('div');
  lecRow.className = 'chart-row';
  lecRow.style.marginTop = '8px';

  const lecLabel = document.createElement('div');
  lecLabel.className = 'row-label';
  lecLabel.innerHTML = `<span style="font-size:10px;color:var(--muted);font-family:'DM Mono',monospace;letter-spacing:0.08em;">講義日程</span>`;
  lecRow.appendChild(lecLabel);

  const lecDots = document.createElement('div');
  lecDots.className = 'lec-dots-row';
  const lecLine = document.createElement('div');
  lecLine.className = 'lec-line';
  lecDots.appendChild(lecLine);

  allDates.forEach(d => {
    if (!lectures.includes(d)) return;
    const f = dateToFrac(d);
    const wrap = document.createElement('div');
    wrap.className = 'lec-dot-wrap';
    wrap.style.left = fracToPercent(f);
    const dot = document.createElement('div');
    dot.className = 'lec-dot';
    wrap.appendChild(dot);
    lecDots.appendChild(wrap);
  });

  lecRow.appendChild(lecDots);
  chart.appendChild(lecRow);

  const divider = document.createElement('div');
  divider.className = 'chart-divider';
  chart.appendChild(divider);
}

function renderPlanRow(chart, plan, std, allDates, lectures, dateToFrac, fracToPercent, N) {
  const row = document.createElement('div');
  row.className = 'chart-row';

  // Label
  const lbl = document.createElement('div');
  lbl.className = 'row-label';
  const badge = document.createElement('div');
  badge.className = 'row-badge';
  badge.style.background = plan.color;
  badge.textContent = plan.num;
  const nameWrap = document.createElement('div');
  nameWrap.style.cssText = 'overflow:hidden;flex:1;';
  nameWrap.innerHTML = `
    <div class="row-name" style="color:${plan.color}">${plan.name}</div>
    <div class="row-tag" style="font-size:10px;color:var(--muted2);letter-spacing:0.03em;">${plan.tag}</div>
  `;
  lbl.appendChild(badge);
  lbl.appendChild(nameWrap);
  row.appendChild(lbl);

  // Bar col
  const barCol = document.createElement('div');
  barCol.className = 'bar-col';

  // vgrid
  const vg = document.createElement('div');
  vg.className = 'vgrid';
  allDates.forEach(d => {
    const ln = document.createElement('div');
    ln.className = 'vgrid-line' + (lectures.includes(d) ? ' is-lecture' : '');
    vg.appendChild(ln);
  });
  barCol.appendChild(vg);

  // 標準縦線
  const fStdIn  = dateToFrac(std.baseIn);
  const fStdOut = dateToFrac(std.baseOut);
  if (fStdIn !== null) {
    const vIn = document.createElement('div');
    vIn.className = 'std-vline';
    vIn.style.left = fracToPercent(fStdIn);
    vIn.dataset.label = std.baseIn;
    barCol.appendChild(vIn);
  }
  if (fStdOut !== null) {
    const vOut = document.createElement('div');
    vOut.className = 'std-vline';
    vOut.style.left = fracToPercent(fStdOut);
    vOut.dataset.label = std.baseOut;
    barCol.appendChild(vOut);
  }

  if (plan.daytrip) {
    const f = dateToFrac(plan.startDate);
    if (f !== null) {
      const marker = document.createElement('div');
      marker.className = 'daytrip-marker';
      marker.style.cssText = `left:${fracToPercent(f)};background:${plan.color};box-shadow:0 0 10px ${plan.color};`;
      barCol.appendChild(marker);
      const lbl2 = document.createElement('div');
      lbl2.className = 'daytrip-label';
      lbl2.style.cssText = `left:${fracToPercent(f)};color:${plan.color};`;
      lbl2.textContent = plan.startDate + '（日帰り）';
      barCol.appendChild(lbl2);
    }
  } else {
    const si = dateToFrac(plan.startDate);
    const ei = dateToFrac(plan.endDate);
    if (si !== null && ei !== null) {
      const leftPct  = si * 100;
      const rightPct = ei * 100;
      const widthPct = Math.max(rightPct - leftPct, 100/N * 0.5);

      const bar = document.createElement('div');
      bar.className = 'bar';
      bar.style.cssText = `left:${leftPct.toFixed(3)}%;width:${widthPct.toFixed(3)}%;color:${plan.color};`;

      // Ghost (standard reference) for non-base plans
      if (!plan.isBase) {
        const bsi = dateToFrac(std.baseIn);
        const bei = dateToFrac(std.baseOut);
        if (bsi !== null && bei !== null) {
          const gLeft  = (bsi * 100 - leftPct).toFixed(3) + '%';
          const gWidth = ((bei - bsi) * 100).toFixed(3) + '%';
          const ghost = document.createElement('div');
          ghost.className = 'bar-ghost';
          ghost.style.cssText = `left:${gLeft};width:${gWidth};`;
          bar.appendChild(ghost);
        }
      }

      const fill = document.createElement('div');
      fill.className = 'bar-fill';
      fill.style.background = plan.color;
      bar.appendChild(fill);

      const stroke = document.createElement('div');
      stroke.className = 'bar-stroke';
      stroke.style.borderColor = plan.color;
      bar.appendChild(stroke);

      // Direction arrows
      if (!plan.isBase) {
        if (plan.early !== 0) {
          const a = document.createElement('div');
          a.className = 'bar-arrow';
          a.style.left = '3px';
          a.style.color = plan.color;
          a.textContent = plan.early > 0 ? '◀' : '▷';
          bar.appendChild(a);
        }
        if (plan.late !== 0) {
          const a = document.createElement('div');
          a.className = 'bar-arrow';
          a.style.right = '3px';
          a.style.color = plan.color;
          a.textContent = plan.late > 0 ? '▶' : '◁';
          bar.appendChild(a);
        }
      }

      const dateLabels = document.createElement('div');
      dateLabels.className = 'bar-date-labels';
      dateLabels.style.color = plan.color;
      const rightLabel = plan.startDate !== plan.endDate ? plan.endDate : '';
      dateLabels.innerHTML = `<span>${plan.startDate}</span><span>${rightLabel}</span>`;
      bar.appendChild(dateLabels);

      barCol.appendChild(bar);
    }
  }

  row.appendChild(barCol);
  chart.appendChild(row);

  const spacer = document.createElement('div');
  spacer.className = 'row-spacer';
  chart.appendChild(spacer);
}

function renderLegend(chart) {
  const legend = document.createElement('div');
  legend.className = 'legend';
  legend.innerHTML = `
    <div class="leg-item"><div class="leg-dot" style="background:var(--lec);box-shadow:0 0 5px rgba(77,184,255,0.7)"></div>講義日</div>
    <div class="leg-item"><div class="leg-ghost"></div>標準期間（参照線）</div>
    <div class="leg-item"><span style="font-size:11px;margin-right:2px">◀▶</span>期間が伸びる</div>
    <div class="leg-item"><span style="font-size:11px;margin-right:2px">▷◁</span>期間が縮む</div>
    <div class="leg-item"><div class="leg-diamond" style="background:#f87171;"></div>日帰り（当日のみ）</div>
  `;
  chart.appendChild(legend);
}

// ─────────────────────────────────────────────
// CHART RENDER
// ─────────────────────────────────────────────
function render() {
  const chart = document.getElementById('chart');
  chart.innerHTML = '';
  chart.style.setProperty('--label-w', LABEL_W + 'px');

  const std = getStandard();
  if (!std) return;

  const allDates = getAllDates(config.timeline.start, config.timeline.end);
  const N = allDates.length;

  function dateToFrac(date) {
    const idx = allDates.indexOf(date);
    if (idx === -1) return null;
    return (idx + 0.5) / N;
  }
  function fracToPercent(f) { return (f * 100).toFixed(4) + '%'; }

  renderDateHeader(chart, allDates, config.lectures, dateToFrac, fracToPercent);
  renderLectureRow(chart, allDates, config.lectures, dateToFrac, fracToPercent);

  const allPlans = [
    {
      num: '①', name: '標準', color: COLORS[0],
      startDate: std.baseIn, endDate: std.baseOut,
      early: 0, late: 0, daytrip: false, isBase: true,
      tag: `${std.baseIn} → ${std.baseOut}`
    },
    ...customPlans.map((p, i) => {
      const color = COLORS[(i + 1) % COLORS.length];
      const { startDate, endDate } = computePlanDates(p, std);
      const tag = p.daytrip
        ? `入り ${p.early >= 0 ? '+' : ''}${p.early}（日帰り）`
        : `前 ${p.early === 0 ? '0' : (p.early > 0 ? `+${p.early}` : p.early)}  延 ${p.late === 0 ? '0' : (p.late > 0 ? `+${p.late}` : p.late)}`;
      return {
        num: numToCircle(i + 2),
        name: p.name,
        color,
        startDate, endDate,
        early: p.early, late: p.late,
        daytrip: p.daytrip,
        isBase: false,
        tag
      };
    })
  ];

  allPlans.forEach(plan =>
    renderPlanRow(chart, plan, std, allDates, config.lectures, dateToFrac, fracToPercent, N)
  );
  renderLegend(chart);
}
