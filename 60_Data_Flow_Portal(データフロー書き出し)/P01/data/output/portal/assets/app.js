const tableFilter = document.getElementById('tableFilter');
const caseFilter = document.getElementById('caseFilter');
if (tableFilter || caseFilter) {
  const changeGroupHeader = document.getElementById('changeGroupHeader');
  const groupHeaderCells = document.querySelectorAll('th.group-header[data-group]');
  const columnCells = document.querySelectorAll('th.sticky-top-3[data-group], td[data-group]');
  const applyFilters = () => {
    const tableValue = tableFilter ? tableFilter.value : '';
    const caseValue = caseFilter ? caseFilter.value : '';
    document.querySelectorAll('tbody tr').forEach((row) => {
      const table = row.getAttribute('data-table') || '';
      const caseId = row.getAttribute('data-case') || '';
      const tableOk = (tableValue === '' || table === tableValue);
      const caseOk = (caseValue === '' || caseId === caseValue);
      row.style.display = (tableOk && caseOk) ? '' : 'none';
    });

    const visibleGroups = new Map();
    groupHeaderCells.forEach((th) => {
      const group = th.getAttribute('data-group') || '';
      const count = parseInt(th.getAttribute('data-count') || '0', 10);
      const visible = (tableValue === '' || group === tableValue);
      th.style.display = visible ? '' : 'none';
      if (visible) {
        visibleGroups.set(group, count);
        th.setAttribute('colspan', String(count));
      }
    });

    columnCells.forEach((cell) => {
      const group = cell.getAttribute('data-group') || '';
      const visible = (tableValue === '' || group === tableValue);
      cell.style.display = visible ? '' : 'none';
    });

    if (changeGroupHeader) {
      let total = 0;
      visibleGroups.forEach((count) => { total += count; });
      if (tableValue === '') {
        total = parseInt(changeGroupHeader.getAttribute('data-count') || '0', 10);
      }
      changeGroupHeader.setAttribute('colspan', String(total));
    }
  };

  if (tableFilter) {
    tableFilter.addEventListener('change', applyFilters);
  }
  if (caseFilter) {
    caseFilter.addEventListener('change', applyFilters);
  }
}

const inputSelector = document.getElementById('inputSelector');
if (inputSelector) {
  inputSelector.addEventListener('change', () => {
    const hint = document.getElementById('inputHint');
    if (hint) {
      hint.textContent = '選択後は再生成が必要です';
    }
  });
}
