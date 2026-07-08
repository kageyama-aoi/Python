"""
crowdlog工数入力UI（pywebview）のエントリーポイント。
サブプロセスとして起動されることを想定。
"""
import json
import os
import datetime
import webview

DRAFTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "drafts")


def draft_path(date_iso: str) -> str:
    return os.path.join(DRAFTS_DIR, f"{date_iso}.json")


def load_draft(date_iso: str) -> list:
    path = draft_path(date_iso)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("entries", [])
    return []


def build_html(html_content: str, today: str, draft_json: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  :root {{
    --font-sans: 'Hiragino Sans', 'Yu Gothic', sans-serif;
    --color-text-primary: #1a1a1a;
    --color-text-secondary: #555;
    --color-text-tertiary: #999;
    --color-text-info: #1d6fa4;
    --color-text-danger: #c0392b;
    --color-background-primary: #fff;
    --color-background-secondary: #f5f5f5;
    --color-background-info: #e8f4fc;
    --color-border-primary: #888;
    --color-border-secondary: #ccc;
    --color-border-tertiary: #e0e0e0;
    --border-radius-md: 6px;
    --border-radius-lg: 10px;
  }}
  body {{ margin: 0; background: var(--color-background-primary); }}
</style>
</head>
<body>
{html_content}
<script>
  window.addEventListener('load', () => {{
    setDate('{today}');
    loadDraft({draft_json});
  }});
</script>
</body>
</html>"""


class Api:
    def __init__(self, today: str):
        self._today = today

    def save_draft(self, payload):
        os.makedirs(DRAFTS_DIR, exist_ok=True)
        date_iso = payload.get("date", self._today)
        path = draft_path(date_iso)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"[Python] 下書き保存: {path}", flush=True)
        return "saved"

    def submit(self, payload):
        print(f"[Python] 登録して同期:\n{json.dumps(payload, ensure_ascii=False, indent=2)}", flush=True)
        return "submitted"


def main():
    today = datetime.date.today().isoformat()
    draft_entries = load_draft(today)
    draft_json = json.dumps(draft_entries, ensure_ascii=False)

    html_path = os.path.join(os.path.dirname(__file__), "crowdlog_dur_input.html")
    with open(html_path, encoding="utf-8") as f:
        html_content = f.read()

    api = Api(today)
    window = webview.create_window(
        title=f"工数入力 - {today}",
        html=build_html(html_content, today, draft_json),
        width=680,
        height=700,
        js_api=api,
    )
    webview.start()


if __name__ == "__main__":
    main()
