import os
from datetime import datetime

from src.utils.fs import ensure_dir, write_text


class PortalRenderer:
    def __init__(self, config):
        self.config = config
        self.null_values = set(
            [str(v).lower() for v in config["csv"].get("null_values", [])]
        )
        self.fixed_columns = config["display"].get("fixed_columns", [])

    def render(self, events, columns, input_csv):
        output_dir = self.config["paths"]["output_dir"]
        assets_dir = self.config["paths"]["assets_dir"]
        ensure_dir(output_dir)
        ensure_dir(assets_dir)

        css_path = os.path.join(assets_dir, "style.css")
        write_text(css_path, build_css())

        html = self.build_html(events, columns, input_csv, "assets/style.css")
        index_path = os.path.join(output_dir, "index.html")
        write_text(index_path, html)
        return index_path

    def build_html(self, events, columns, input_csv, css_path):
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fixed_widths = build_fixed_widths(self.fixed_columns)
        left_offsets = build_left_offsets(fixed_widths)

        legend_html = ""
        if self.config["display"].get("show_legend", True):
            legend_html = """
            <div class="legend inline">
              <span class="badge added">added</span>
              <span class="badge removed">removed</span>
              <span class="badge changed">changed</span>
              <span class="badge same">same</span>
            </div>
            """

        fixed_total = sum(fixed_widths)
        fixed_group_style = build_sticky_style(0, fixed_total)
        table_groups = build_table_groups(events, columns)
        grouped_columns = [col for _, cols in table_groups for col in cols]
        col_group_map = {}
        for label, cols in table_groups:
            for col in cols:
                col_group_map[col] = label

        header_group = (
            f"<th class='group-header sticky-top-1 sticky-col' style='{fixed_group_style}' "
            f"colspan='{len(self.fixed_columns)}'>"
            "対象・フロー（固定）</th>"
            f"<th id='changeGroupHeader' class='group-header sticky-top-1' "
            f"data-count='{len(grouped_columns)}' colspan='{len(grouped_columns)}'>"
            f"<div class='group-title'>変更カラム（イベント内の更新）{legend_html}</div>"
            "</th>"
        )
        table_group_cells = [
            f"<th class='sticky-top-2 group-header sticky-col' style='{fixed_group_style}' "
            f"colspan='{len(self.fixed_columns)}'></th>"
        ]
        for label, cols in table_groups:
            table_group_cells.append(
                f"<th class='sticky-top-2 group-header' data-group='{label}' "
                f"data-count='{len(cols)}' colspan='{len(cols)}'>{label}</th>"
            )

        header_cells = []
        for idx, col in enumerate(self.fixed_columns):
            style = build_sticky_style(left_offsets[idx], fixed_widths[idx])
            header_cells.append(
                f"<th class='sticky-col sticky-top-3' style='{style}'>{col}</th>"
            )
        for col in grouped_columns:
            group = col_group_map.get(col, "")
            header_cells.append(
                f"<th class='sticky-top-3' data-group='{group}'>{col}</th>"
            )

        body_rows = []
        for event in events:
            operation = (event.get("operation") or "").lower()
            row_class = f"op-{operation}" if operation else ""
            table_value = escape_html(event.get("table", ""))
            row_cells = []

            fixed_values = [
                event.get("case_id", ""),
                event.get("table", ""),
                event.get("operation", ""),
                event.get("trigger", ""),
            ]
            for idx, value in enumerate(fixed_values):
                style = build_sticky_style(left_offsets[idx], fixed_widths[idx])
                row_cells.append(
                    f"<td class='sticky-col' style='{style}'>{escape_html(value)}</td>"
                )

            for col in grouped_columns:
                change = event["changes"].get(col)
                if not change:
                    group = col_group_map.get(col, "")
                    row_cells.append(f"<td class='empty' data-group='{group}'></td>")
                    continue
                cell_html = render_change(
                    event.get("case_id", ""),
                    col,
                    change.get("before", ""),
                    change.get("after", ""),
                    self.null_values,
                    event.get("operation", ""),
                    event.get("trigger", ""),
                )
                group = col_group_map.get(col, "")
                row_cells.append(f"<td data-group='{group}'>{cell_html}</td>")

            body_rows.append(
                f"<tr class='{row_class}' data-table='{table_value}'>"
                + "".join(row_cells)
                + "</tr>"
            )

        meta_html = build_meta(
            generated_at,
            input_csv,
            self.config["display"].get("show_generated_at", True),
            self.config["display"].get("show_input_name", True),
        )
        controls_html = build_controls(events)
        script_html = build_filter_script()

        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <title>Data Flow Portal</title>
  <link rel="stylesheet" href="{css_path}">
</head>
<body>
  <div class="portal-container">
    <h1>Data Flow Portal</h1>
    <div class="meta">{meta_html}</div>
    {controls_html}
    <div class="table-wrap">
      <table>
        <thead>
          <tr>{header_group}</tr>
          <tr>{''.join(table_group_cells)}</tr>
          <tr>{''.join(header_cells)}</tr>
        </thead>
        <tbody>
          {''.join(body_rows)}
        </tbody>
      </table>
    </div>
  </div>
  {script_html}
</body>
</html>
"""


def build_css():
    return """
:root {
  --bg: #f6f7f9;
  --line: #e2e5ea;
  --text: #1f2a37;
  --muted: #6b7280;
  --added: #0f766e;
  --removed: #b91c1c;
  --changed: #111827;
  --same: #9ca3af;
  --insert: #10b981;
  --update: #f59e0b;
  --delete: #ef4444;
}

body {
  font-family: "Segoe UI", "Hiragino Kaku Gothic ProN", Meiryo, sans-serif;
  background: var(--bg);
  color: var(--text);
  margin: 0;
  padding: 24px;
}

.portal-container {
  max-width: 1400px;
  margin: 0 auto;
}

h1 {
  margin: 0 0 8px 0;
}

.meta {
  color: var(--muted);
  margin-bottom: 8px;
}

.legend {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.legend.inline {
  display: inline-flex;
  gap: 6px;
  margin-left: 10px;
}

.controls {
  margin: 8px 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.controls select {
  padding: 4px 6px;
  border-radius: 6px;
  border: 1px solid var(--line);
  background: #fff;
}

.badge {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid var(--line);
  background: #fff;
}

.badge.added { color: var(--added); }
.badge.removed { color: var(--removed); }
.badge.changed { color: var(--changed); }
.badge.same { color: var(--same); }

.table-wrap {
  overflow: auto;
  border: 1px solid var(--line);
  background: #fff;
}

table {
  border-collapse: collapse;
  width: max-content;
  min-width: 100%;
  font-size: 13px;
  table-layout: fixed;
}

th, td {
  border: 1px solid var(--line);
  padding: 8px 10px;
  text-align: left;
  white-space: nowrap;
  box-sizing: border-box;
}

th {
  position: sticky;
  top: 0;
  background: #f9fafb;
  z-index: 3;
}

.sticky-top-1 {
  position: sticky;
  top: 0;
  z-index: 5;
  background: #eef2f7;
  font-weight: 600;
}

.sticky-top-2 {
  position: sticky;
  top: 28px;
  z-index: 4;
  background: #f3f4f6;
}

.sticky-top-3 {
  position: sticky;
  top: 56px;
  z-index: 3;
  background: #f9fafb;
}

.group-header {
  text-align: center;
  letter-spacing: 0.02em;
}

.group-title {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

tr:hover td {
  background: #f3f4f6;
}

td.empty {
  background: #fafafa;
}

.sticky-col {
  position: sticky;
  left: 0;
  background: #fff;
  z-index: 2;
  box-shadow: 2px 0 0 var(--line);
}

th.sticky-col {
  z-index: 7;
}

td.sticky-col {
  z-index: 3;
}

.op-insert td:first-child {
  border-left: 4px solid var(--insert);
}

.op-update td:first-child {
  border-left: 4px solid var(--update);
}

.op-delete td:first-child {
  border-left: 4px solid var(--delete);
}

.op-insert td.sticky-col {
  background: #ecfdf3;
}

.op-update td.sticky-col {
  background: #fff7ed;
}

.op-delete td.sticky-col {
  background: #f3f4f6;
  color: var(--muted);
}

.change {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.change .before {
  color: var(--same);
}

.change .after.added {
  color: var(--added);
  font-weight: 600;
}

.change .after.removed {
  color: var(--removed);
  font-weight: 600;
}

.change .after.changed {
  color: var(--changed);
  font-weight: 700;
}

.change.same {
  color: var(--same);
}

.detail-hover {
  position: relative;
  cursor: help;
}

.detail-hover:hover::after,
.detail-hover:focus::after {
  content: attr(data-detail);
  white-space: pre-line;
  position: absolute;
  left: 0;
  bottom: 120%;
  min-width: 220px;
  max-width: 320px;
  padding: 8px 10px;
  background: #111827;
  color: #f9fafb;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.4;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.2);
  z-index: 10;
}

.detail-hover:hover::before,
.detail-hover:focus::before {
  content: "";
  position: absolute;
  left: 12px;
  bottom: 110%;
  border-width: 6px 6px 0 6px;
  border-style: solid;
  border-color: #111827 transparent transparent transparent;
  z-index: 10;
}
"""


def build_fixed_widths(columns):
    defaults = {
        "case_id": 110,
        "table": 140,
        "operation": 110,
        "trigger": 150,
    }
    widths = []
    for col in columns:
        widths.append(defaults.get(col, 140))
    return widths


def build_left_offsets(widths):
    offsets = []
    current = 0
    for width in widths:
        offsets.append(current)
        current += width
    return offsets


def build_sticky_style(left, width):
    return (
        f"left: {left}px; width: {width}px; min-width: {width}px; "
        f"max-width: {width}px;"
    )


def render_change(case_id, attr_type, before, after, null_values, operation, trigger):
    detail_text = (
        f"{case_id} / {attr_type}\n"
        f"operation: {operation}\n"
        f"trigger: {trigger}\n"
        "詳細は後で追記"
    )
    before_text = display_value(before, null_values)
    after_text = display_value(after, null_values)
    before_is_null = is_null(before, null_values)
    after_is_null = is_null(after, null_values)

    if before_is_null and after_is_null:
        return (
            f"<span class='change same detail-hover' data-detail='{escape_html(detail_text)}'>"
            f"{before_text}</span>"
        )
    if not before_is_null and not after_is_null and before_text == after_text:
        return (
            f"<span class='change same detail-hover' data-detail='{escape_html(detail_text)}'>"
            f"{before_text}</span>"
        )
    if before_is_null and not after_is_null:
        return (
            f"<span class='change detail-hover' data-detail='{escape_html(detail_text)}'>"
            f"<span class='after added'>{after_text}</span>"
            "</span>"
        )
    if not before_is_null and after_is_null:
        return (
            f"<span class='change detail-hover' data-detail='{escape_html(detail_text)}'>"
            f"<span class='before'>{before_text}</span>"
            "<span class='arrow'>→</span>"
            f"<span class='after removed'>{after_text}</span>"
            "</span>"
        )
    return (
        f"<span class='change detail-hover' data-detail='{escape_html(detail_text)}'>"
        f"<span class='before'>{before_text}</span>"
        "<span class='arrow'>→</span>"
        f"<span class='after changed'>{after_text}</span>"
        "</span>"
    )


def display_value(value, null_values):
    if is_null(value, null_values):
        return "NULL"
    return escape_html(str(value))


def is_null(value, null_values):
    if value is None:
        return True
    text = str(value).strip()
    if text == "":
        return True
    return text.lower() in null_values


def escape_html(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def build_table_filter(events):
    tables = []
    seen = set()
    for event in events:
        table = (event.get("table") or "").strip()
        if table and table not in seen:
            seen.add(table)
            tables.append(table)
    options = ["<option value=''>すべて</option>"]
    for table in tables:
        options.append(f"<option value='{escape_html(table)}'>{escape_html(table)}</option>")
    return f"<select id='tableFilter'>{''.join(options)}</select>"


def build_controls(events):
    return (
        "<div class=\"controls\">"
        "<label for=\"tableFilter\">テーブル絞り込み:</label>"
        f"{build_table_filter(events)}"
        "</div>"
    )


def build_meta(generated_at, input_csv, show_generated_at, show_input_name):
    meta_parts = []
    if show_generated_at:
        meta_parts.append(f"Generated: {generated_at}")
    if show_input_name:
        meta_parts.append(f"Input: {os.path.basename(input_csv)}")
    return " | ".join(meta_parts)


def build_filter_script():
    return """
  <script>
    const tableFilter = document.getElementById('tableFilter');
    if (tableFilter) {
      const changeGroupHeader = document.getElementById('changeGroupHeader');
      const groupHeaderCells = document.querySelectorAll('th.group-header[data-group]');
      const columnCells = document.querySelectorAll('th.sticky-top-3[data-group], td[data-group]');
      tableFilter.addEventListener('change', () => {
        const value = tableFilter.value;
        document.querySelectorAll('tbody tr').forEach((row) => {
          const table = row.getAttribute('data-table') || '';
          row.style.display = (value === '' || table === value) ? '' : 'none';
        });

        const visibleGroups = new Map();
        groupHeaderCells.forEach((th) => {
          const group = th.getAttribute('data-group') || '';
          const count = parseInt(th.getAttribute('data-count') || '0', 10);
          const visible = (value === '' || group === value);
          th.style.display = visible ? '' : 'none';
          if (visible) {
            visibleGroups.set(group, count);
            th.setAttribute('colspan', String(count));
          }
        });

        columnCells.forEach((cell) => {
          const group = cell.getAttribute('data-group') || '';
          const visible = (value === '' || group === value);
          cell.style.display = visible ? '' : 'none';
        });

        if (changeGroupHeader) {
          let total = 0;
          visibleGroups.forEach((count) => { total += count; });
          if (value === '') {
            total = parseInt(changeGroupHeader.getAttribute('data-count') || '0', 10);
          }
          changeGroupHeader.setAttribute('colspan', String(total));
        }
      });
    }
  </script>
    """


def build_table_groups(events, columns):
    table_names = []
    seen = set()
    for event in events:
        table = (event.get("table") or "").strip()
        if table and table not in seen:
            seen.add(table)
            table_names.append(table)

    attr_table_map = {}
    for event in events:
        table = (event.get("table") or "").strip()
        if not table:
            continue
        for attr in event.get("changes", {}).keys():
            if attr not in attr_table_map:
                attr_table_map[attr] = table

    def resolve_group(col):
        if col in attr_table_map:
            return attr_table_map[col]
        for table in table_names:
            prefixes = [f"{table}_"]
            if table.endswith("s") and len(table) > 1:
                prefixes.append(f"{table[:-1]}_")
            for prefix in prefixes:
                if col.startswith(prefix):
                    return table
        return ""

    grouped = []
    used = set()
    for table in table_names:
        cols = [col for col in columns if resolve_group(col) == table]
        if cols:
            grouped.append((table, cols))
            used.update(cols)

    leftover = [col for col in columns if col not in used]
    if leftover:
        label = table_names[-1] if table_names else ""
        if grouped and grouped[-1][0] == label:
            grouped[-1] = (label, grouped[-1][1] + leftover)
        else:
            grouped.append((label, leftover))

    return grouped
