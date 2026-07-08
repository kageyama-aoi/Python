// ─────────────────────────────────────────────
// CSV ユーティリティ
// ─────────────────────────────────────────────
function nightsBetween(a, b) {
  const { m: am, d: ad } = parseDate(a);
  const { m: bm, d: bd } = parseDate(b);
  return Math.round((new Date(YEAR,bm-1,bd) - new Date(YEAR,am-1,ad)) / 86400000);
}

function downloadCsv(filename, rows) {
  const csvContent = '\uFEFF' + rows.join('\r\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

function q(v) { return `"${String(v).replace(/"/g, '""')}"`; }

// ── 日程CSV（講義日程 + 標準プランのみ） ──
document.getElementById('btn-csv-schedule').addEventListener('click', () => {
  const std = getStandard();
  if (!std) return;
  const ts = config.timeline.start.replace('/','-');
  const te = config.timeline.end.replace('/','-');

  const rows = [
    [q('【日程設定】'), q(`出力日時: ${new Date().toLocaleString('ja-JP')}`)].join(','),
    '',
    q('■ 講義日程') + ',',
    [q('タイムライン開始'), q(config.timeline.start)].join(','),
    [q('タイムライン終了'), q(config.timeline.end)].join(','),
    [q('講義日'), q(config.lectures.join(' / '))].join(','),
    '',
    q('■ 標準プラン（自動算出）') + ',',
    [q('項目'), q('日付')].join(','),
    [q('標準チェックイン'), q(std.baseIn)].join(','),
    [q('標準チェックアウト'), q(std.baseOut)].join(','),
    [q('標準宿泊数'), q(nightsBetween(std.baseIn, std.baseOut) + '泊')].join(','),
    [q('算出ルール'), q('チェックイン＝講義初日の前日 / チェックアウト＝講義最終日当日')].join(','),
  ];
  downloadCsv(`日程設定_${ts}_${te}.csv`, rows);
});

// ── プランCSV（全プラン一覧） ──
document.getElementById('btn-csv-plans').addEventListener('click', () => {
  const std = getStandard();
  if (!std) return;
  const ts = config.timeline.start.replace('/','-');
  const te = config.timeline.end.replace('/','-');
  const allPlans = buildAllPlans(std);
  const baseNights = nightsBetween(std.baseIn, std.baseOut);

  const header = ['プラン番号','プラン名','前泊数','延泊数','日帰り',
    'チェックイン','チェックアウト','宿泊数',
    '標準比（チェックイン）','標準比（チェックアウト）','備考'].map(q).join(',');

  const dataRows = allPlans.map(p => {
    const nights  = p.daytrip ? 0 : nightsBetween(p.startDate, p.endDate);
    const inDiff  = nightsBetween(std.baseIn,  p.startDate);
    const outDiff = nightsBetween(std.baseOut, p.endDate);
    const note = p.daytrip ? '日帰り（宿泊なし）'
      : nights === baseNights ? '標準と同泊数'
      : nights > baseNights   ? `標準より${nights - baseNights}泊多い`
      :                         `標準より${baseNights - nights}泊少ない`;
    return [
      p.num, p.name,
      p.daytrip ? '-' : p.early,
      p.daytrip ? '-' : p.late,
      p.daytrip ? '○' : '',
      p.startDate, p.endDate,
      p.daytrip ? 0 : nights,
      inDiff  === 0 ? '±0' : inDiff  > 0 ? `+${inDiff}`  : inDiff,
      outDiff === 0 ? '±0' : outDiff > 0 ? `+${outDiff}` : outDiff,
      note,
    ].map(q).join(',');
  });

  const rows = [
    [q('【プラン一覧】'), q(`出力日時: ${new Date().toLocaleString('ja-JP')}`)].join(','),
    [q('タイムライン'), q(`${config.timeline.start} → ${config.timeline.end}`)].join(','),
    [q('講義日'), q(config.lectures.join(' / '))].join(','),
    '',
    header,
    ...dataRows,
  ];
  downloadCsv(`プラン一覧_${ts}_${te}.csv`, rows);
});
