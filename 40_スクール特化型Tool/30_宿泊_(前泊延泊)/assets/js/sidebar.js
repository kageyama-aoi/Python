// ─────────────────────────────────────────────
// SIDEBAR PLAN LIST
// ─────────────────────────────────────────────
function updatePlans(mutateFn) {
  mutateFn();
  renderSidebar();
  render();
}

function renderSidebar() {
  const list = document.getElementById('plan-list');
  list.innerHTML = '';

  customPlans.forEach((plan, i) => {
    const color = COLORS[(i + 1) % COLORS.length]; // +1 because ① is index 0
    const entry = document.createElement('div');
    entry.className = 'plan-entry';

    // badge
    const badge = document.createElement('div');
    badge.className = 'plan-badge';
    badge.style.background = color;
    badge.textContent = `${numToCircle(i + 2)}`;
    entry.appendChild(badge);

    // name col
    const nameCol = document.createElement('div');
    nameCol.style.cssText = 'display:flex;flex-direction:column;gap:4px;overflow:hidden;';

    const nameInput = document.createElement('input');
    nameInput.className = 'name-input';
    nameInput.value = plan.name;
    nameInput.addEventListener('input', e => { plan.name = e.target.value; render(); });

    // daytrip toggle
    const dtRow = document.createElement('div');
    dtRow.className = 'daytrip-row';
    const toggleId = `dt-${plan.id}`;
    dtRow.innerHTML = `
      <label class="toggle">
        <input type="checkbox" id="${toggleId}" ${plan.daytrip ? 'checked' : ''}>
        <div class="toggle-track"></div>
        <div class="toggle-thumb"></div>
      </label>
      <span class="toggle-label">日帰り</span>
    `;
    dtRow.querySelector('input').addEventListener('change', e => {
      updatePlans(() => { plan.daytrip = e.target.checked; });
    });

    nameCol.appendChild(nameInput);
    nameCol.appendChild(dtRow);
    entry.appendChild(nameCol);

    if (!plan.daytrip) {
      // early spin
      const earlyGroup = makeSpinGroup('前泊', plan.early, v => { plan.early = v; render(); }, color);
      const lateGroup  = makeSpinGroup('延泊', plan.late,  v => { plan.late  = v; render(); }, color);
      entry.appendChild(earlyGroup);
      entry.appendChild(lateGroup);
    } else {
      // daytrip: just show arrival offset
      const earlyGroup = makeSpinGroup('入り', plan.early, v => { plan.early = v; render(); }, color);
      entry.appendChild(earlyGroup);
      // placeholder
      const ph = document.createElement('div'); ph.style.width='48px';
      entry.appendChild(ph);
    }

    // remove
    const btnRm = document.createElement('button');
    btnRm.className = 'btn-remove';
    btnRm.textContent = '✕';
    btnRm.title = '削除';
    btnRm.addEventListener('click', () => {
      updatePlans(() => { customPlans = customPlans.filter(p => p.id !== plan.id); });
    });
    entry.appendChild(btnRm);

    list.appendChild(entry);
  });
}

function makeSpinGroup(label, value, onChange, color) {
  const g = document.createElement('div');
  g.className = 'spin-group';

  const lbl = document.createElement('div');
  lbl.className = 'spin-label';
  lbl.textContent = label;

  const inp = document.createElement('input');
  inp.className = 'spin-input';
  inp.type = 'number';
  inp.value = value;
  inp.style.color = color;
  inp.addEventListener('input', e => onChange(parseInt(e.target.value) || 0));

  g.appendChild(lbl);
  g.appendChild(inp);
  return g;
}

function numToCircle(n) {
  const circles = ['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩','⑪','⑫'];
  return circles[n - 1] || `(${n})`;
}

document.getElementById('btn-add-plan').addEventListener('click', () => {
  updatePlans(() => {
    customPlans.push({ id: nextId++, name: `プラン ${customPlans.length + 2}`, early: 0, late: 0, daytrip: false });
  });
});
