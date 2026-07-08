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

  if (customPlans.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'plan-list-empty';
    empty.textContent = 'プランがありません';
    list.appendChild(empty);
    return;
  }

  customPlans.forEach((plan, i) => {
    const color = COLORS[(i + 1) % COLORS.length]; // +1 because ① is index 0
    const entry = document.createElement('div');
    entry.className = 'plan-entry';

    // ── 行1: バッジ + 名前入力 + 削除ボタン ──
    const header = document.createElement('div');
    header.className = 'plan-entry-header';

    const badge = document.createElement('div');
    badge.className = 'plan-badge';
    badge.style.background = color;
    badge.textContent = numToCircle(i + 2);

    const nameInput = document.createElement('input');
    nameInput.className = 'name-input';
    nameInput.value = plan.name;
    nameInput.addEventListener('input', e => { plan.name = e.target.value; render(); });

    const btnRm = document.createElement('button');
    btnRm.className = 'btn-remove';
    btnRm.textContent = '✕';
    btnRm.title = '削除';
    btnRm.addEventListener('click', () => {
      updatePlans(() => { customPlans = customPlans.filter(p => p.id !== plan.id); });
    });

    header.appendChild(badge);
    header.appendChild(nameInput);
    header.appendChild(btnRm);
    entry.appendChild(header);

    // ── 行2: 日帰りトグル + スピングループ ──
    const controls = document.createElement('div');
    controls.className = 'plan-entry-controls';

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

    const spins = document.createElement('div');
    spins.className = 'plan-spins';
    if (!plan.daytrip) {
      spins.appendChild(makeSpinGroup('前泊', plan.early, v => { plan.early = v; render(); }, color));
      spins.appendChild(makeSpinGroup('延泊', plan.late,  v => { plan.late  = v; render(); }, color));
    } else {
      spins.appendChild(makeSpinGroup('入り', plan.early, v => { plan.early = v; render(); }, color));
    }

    controls.appendChild(dtRow);
    controls.appendChild(spins);
    entry.appendChild(controls);

    list.appendChild(entry);
  });
}

function makeSpinGroup(label, value, onChange, color) {
  const g = document.createElement('div');
  g.className = 'spin-group';

  const lbl = document.createElement('div');
  lbl.className = 'spin-label';
  lbl.textContent = label;

  const row = document.createElement('div');
  row.className = 'spin-row';

  const btnMinus = document.createElement('button');
  btnMinus.className = 'spin-btn';
  btnMinus.textContent = '−';
  btnMinus.style.color = color;

  const inp = document.createElement('input');
  inp.className = 'spin-input';
  inp.type = 'number';
  inp.value = value;
  inp.style.color = color;
  inp.addEventListener('input', e => onChange(parseInt(e.target.value) || 0));

  const btnPlus = document.createElement('button');
  btnPlus.className = 'spin-btn';
  btnPlus.textContent = '＋';
  btnPlus.style.color = color;

  btnMinus.addEventListener('click', () => {
    const next = (parseInt(inp.value) || 0) - 1;
    inp.value = next;
    onChange(next);
  });
  btnPlus.addEventListener('click', () => {
    const next = (parseInt(inp.value) || 0) + 1;
    inp.value = next;
    onChange(next);
  });

  row.appendChild(btnMinus);
  row.appendChild(inp);
  row.appendChild(btnPlus);

  g.appendChild(lbl);
  g.appendChild(row);
  return g;
}


document.getElementById('btn-add-plan').addEventListener('click', () => {
  updatePlans(() => {
    customPlans.push({ id: nextId++, name: `プラン ${customPlans.length + 2}`, early: 0, late: 0, daytrip: false });
  });
});
