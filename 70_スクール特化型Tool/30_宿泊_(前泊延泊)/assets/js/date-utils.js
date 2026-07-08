// ─────────────────────────────────────────────
// DATE UTILS
// ─────────────────────────────────────────────
const YEAR = new Date().getFullYear();

function parseDate(str) {
  // "M/D" → {m, d}
  const [m, d] = str.split('/').map(Number);
  return { m, d };
}

function dateToVal(str) {
  const { m, d } = parseDate(str);
  return m * 100 + d;
}

function addDays(str, n) {
  // Only works within same month for simplicity; extend if needed
  const { m, d } = parseDate(str);
  const base = new Date(YEAR, m - 1, d);
  base.setDate(base.getDate() + n);
  return `${base.getMonth()+1}/${base.getDate()}`;
}

function getAllDates(start, end) {
  const dates = [];
  const { m: sm, d: sd } = parseDate(start);
  const { m: em, d: ed } = parseDate(end);
  let cur = new Date(YEAR, sm - 1, sd);
  const endD = new Date(YEAR, em - 1, ed);
  while (cur <= endD) {
    dates.push(`${cur.getMonth()+1}/${cur.getDate()}`);
    cur.setDate(cur.getDate() + 1);
  }
  return dates;
}

function clamp(date, start, end) {
  const v = dateToVal(date);
  if (v < dateToVal(start)) return start;
  if (v > dateToVal(end))   return end;
  return date;
}

function numToCircle(n) {
  const circles = ['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩','⑪','⑫'];
  return circles[n - 1] || `(${n})`;
}
