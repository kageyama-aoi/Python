// ─────────────────────────────────────────────
// STATE
// ─────────────────────────────────────────────
const COLORS = ['var(--c0)','var(--c1)','var(--c2)','var(--c3)','var(--c4)','var(--c5)','var(--c6)','var(--c7)'];
const LABEL_W = 188;

let config = {
  timeline: { start: '2/13', end: '2/22' },
  lectures: ['2/16', '2/20']
};

let customPlans = [
  { id:1, name:'前泊 +2',  early: 2, late: 0, daytrip: false },
  { id:2, name:'延泊 +2',  early: 0, late: 2, daytrip: false },
  { id:3, name:'前泊 −1',  early:-1, late: 0, daytrip: false },
  { id:4, name:'延泊 −1',  early: 0, late:-1, daytrip: false },
  { id:5, name:'複合',     early: 2, late:-3, daytrip: false },
  { id:6, name:'日帰り',   early: 2, late:-3, daytrip: true  },
];
let nextId = 7;

// ─────────────────────────────────────────────
// JSON EDITOR — 日程設定 / プラン設定 分離
// ─────────────────────────────────────────────
const scheduleTextarea = document.getElementById('json-schedule');
const scheduleStatus   = document.getElementById('json-schedule-status');
const jsonRange        = document.getElementById('json-date-range');
const plansTextarea    = document.getElementById('json-plans');
const plansStatus      = document.getElementById('json-plans-status');

function showToast(id, color) {
  const t = document.getElementById(id);
  t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 2000);
}

// ── 日程設定パース ──
function parseSchedule() {
  try {
    const parsed = JSON.parse(scheduleTextarea.value);
    if (!parsed.timeline?.start || !parsed.timeline?.end) throw new Error('timeline.start / end が必要です');
    if (!Array.isArray(parsed.lectures) || parsed.lectures.length === 0) throw new Error('lectures 配列が必要です');
    config = { timeline: parsed.timeline, lectures: parsed.lectures };
    scheduleStatus.textContent = '✓ valid';
    scheduleStatus.className = 'json-status ok';
    jsonRange.textContent = `${config.timeline.start} → ${config.timeline.end}`;
    render();
  } catch(e) {
    scheduleStatus.textContent = '✗ ' + e.message;
    scheduleStatus.className = 'json-status error';
  }
}

// ── プラン設定パース ──
function parsePlans(apply) {
  try {
    const parsed = JSON.parse(plansTextarea.value);
    if (!Array.isArray(parsed)) throw new Error('配列形式で入力してください');
    plansStatus.textContent = '✓ valid';
    plansStatus.className = 'json-status ok';
    if (apply) {
      updatePlans(() => {
        customPlans = parsed.map((p, i) => ({
          id: nextId++,
          name:    p.name    ?? `プラン ${i + 2}`,
          early:   p.early   ?? 0,
          late:    p.late    ?? 0,
          daytrip: p.daytrip ?? false,
        }));
      });
    }
  } catch(e) {
    plansStatus.textContent = '✗ ' + e.message;
    plansStatus.className = 'json-status error';
  }
}

// タイピングでリアルタイム反映
scheduleTextarea.addEventListener('input', parseSchedule);
plansTextarea.addEventListener('input', () => parsePlans(false));

// 適用ボタン
document.getElementById('btn-schedule-import').addEventListener('click', parseSchedule);
document.getElementById('btn-plans-import').addEventListener('click', () => parsePlans(true));

// 書き出しボタン
document.getElementById('btn-schedule-export').addEventListener('click', () => {
  const out = JSON.stringify({ timeline: config.timeline, lectures: config.lectures }, null, 2);
  scheduleTextarea.value = out;
  scheduleStatus.textContent = '✓ 書き出し済み';
  scheduleStatus.className = 'json-status ok';
  navigator.clipboard.writeText(out).then(() => showToast('copy-toast-schedule')).catch(()=>{});
});

document.getElementById('btn-plans-export').addEventListener('click', () => {
  const out = JSON.stringify(customPlans.map(p => ({
    name: p.name, early: p.early, late: p.late, daytrip: p.daytrip
  })), null, 2);
  plansTextarea.value = out;
  plansStatus.textContent = '✓ 書き出し済み';
  plansStatus.className = 'json-status ok';
  navigator.clipboard.writeText(out).then(() => showToast('copy-toast-plans')).catch(()=>{});
});

// 初回パース用（後方互換）
function parseJSON(applyPlans) {
  parseSchedule();
  if (applyPlans) parsePlans(true);
}

// ─────────────────────────────────────────────
// DRAWER
// ─────────────────────────────────────────────
const sidebar        = document.getElementById('sidebar');
const overlay        = document.getElementById('sidebar-overlay');
const btnHamburger   = document.getElementById('btn-hamburger');
const btnCloseSidebar = document.getElementById('btn-close-sidebar');

function openDrawer() {
  sidebar.classList.add('open');
  overlay.classList.add('open');
  btnHamburger.classList.add('open');
}
function closeDrawer() {
  sidebar.classList.remove('open');
  overlay.classList.remove('open');
  btnHamburger.classList.remove('open');
}

btnHamburger.addEventListener('click', () => {
  sidebar.classList.contains('open') ? closeDrawer() : openDrawer();
});
btnCloseSidebar.addEventListener('click', closeDrawer);
overlay.addEventListener('click', closeDrawer);

// ESCキーでも閉じる
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeDrawer(); });

// ─────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────
parseJSON(true);
renderSidebar();
