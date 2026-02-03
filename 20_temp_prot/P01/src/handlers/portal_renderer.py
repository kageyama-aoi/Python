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

        html = self._build_html(events, columns, input_csv, "assets/style.css")
        index_path = os.path.join(output_dir, "index.html")
        write_text(index_path, html)
        return index_path

    def _build_html(self, events, columns, input_csv, css_path):
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fixed_widths = build_fixed_widths(self.fixed_columns)
        left_offsets = build_left_offsets(fixed_widths)

        header_cells = []
        for idx, col in enumerate(self.fixed_columns):
            style = build_sticky_style(left_offsets[idx], fixed_widths[idx])
            header_cells.append(f"<th class='sticky-col' style='{style}'>{col}</th>")
        for col in columns:
            header_cells.append(f"<th>{col}</th>")

        body_rows = []
        for event in events:
            operation = (event.get("operation") or "").lower()
            row_class = f"op-{operation}" if operation else ""
            row_cells = []

            fixed_values = [
                event.get("event_id", ""),
                event.get("table", ""),
                event.get("operation", ""),
                event.get("trigger", ""),
            ]
            for idx, value in enumerate(fixed_values):
                style = build_sticky_style(left_offsets[idx], fixed_widths[idx])
                row_cells.append(
                    f"<td class='sticky-col' style='{style}'>{escape_html(value)}</td>"
                )

            for col in columns:
                change = event["changes"].get(col)
                if not change:
                    row_cells.append("<td class='empty'></td>")
                    continue
                cell_html = render_change(
                    change.get("before", ""),
                    change.get("after", ""),
                    self.null_values,
                )
                row_cells.append(f"<td>{cell_html}</td>")

            body_rows.append(
                f"<tr class='{row_class}'>" + "".join(row_cells) + "</tr>"
            )

        legend_html = ""
        if self.config["display"].get("show_legend", True):
            legend_html = """
            <div class="legend">
              <span class="badge added">added</span>
              <span class="badge removed">removed</span>
              <span class="badge changed">changed</span>
              <span class="badge same">same</span>
            </div>
            """

        meta_parts = []
        if self.config["display"].get("show_generated_at", True):
            meta_parts.append(f"Generated: {generated_at}")
        if self.config["display"].get("show_input_name", True):
            meta_parts.append(f"Input: {os.path.basename(input_csv)}")
        meta_html = " | ".join(meta_parts)

        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <title>Data Flow Portal</title>
  <link rel="stylesheet" href="{css_path}">
  <style>
    table {{ border-collapse: collapse; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 6px 8px; }}
  </style>
</head>
<body>
  <div class="portal-container">
    <h1>Data Flow Portal</h1>
    <div class="meta">{meta_html}</div>
    {legend_html}
    <div class="table-wrap">
      <table>
        <thead>
          <tr>{''.join(header_cells)}</tr>
        </thead>
        <tbody>
          {''.join(body_rows)}
        </tbody>
      </table>
    </div>
  </div>
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
}

th, td {
  border: 1px solid var(--line);
  padding: 8px 10px;
  text-align: left;
  white-space: nowrap;
}

th {
  position: sticky;
  top: 0;
  background: #f9fafb;
  z-index: 3;
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
"""


def build_fixed_widths(columns):
    defaults = {
        "event_id": 110,
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
    return f"left: {left}px; min-width: {width}px; max-width: {width}px;"


def render_change(before, after, null_values):
    before_text = display_value(before, null_values)
    after_text = display_value(after, null_values)
    before_is_null = is_null(before, null_values)
    after_is_null = is_null(after, null_values)

    if before_is_null and after_is_null:
        return f"<span class='change same'>{before_text}</span>"
    if not before_is_null and not after_is_null and before_text == after_text:
        return f"<span class='change same'>{before_text}</span>"
    if before_is_null and not after_is_null:
        return (
            "<span class='change'>"
            f"<span class='after added'>{after_text}</span>"
            "</span>"
        )
    if not before_is_null and after_is_null:
        return (
            "<span class='change'>"
            f"<span class='before'>{before_text}</span>"
            "<span class='arrow'>→</span>"
            f"<span class='after removed'>{after_text}</span>"
            "</span>"
        )
    return (
        "<span class='change'>"
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
