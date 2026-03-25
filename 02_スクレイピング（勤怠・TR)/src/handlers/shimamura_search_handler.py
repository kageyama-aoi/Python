"""
Shimamura マージ依頼検索フローのハンドラ。
検索結果を一覧表示し、対象ステータスの詳細ページへコメント追記・ステータス変更・スクリーンショット撮影を行う。
"""
import re
import time
import datetime
from urllib.parse import urljoin, quote

import config
import browser_utils
from .base_handler import BaseHandler


class ShimamuraSearchHandler(BaseHandler):
    """
    Shimamura タスクレポートの一括マージ依頼処理ハンドラ。
    """

    def execute(self):
        search_keyword = self.context['search_keyword']
        target_url     = self.context['target_url']

        conf = config.CONF.get('task_report_settings', {}).get('shimamura_search', {})
        target_status   = conf.get('target_status', '')
        new_status      = conf.get('new_status', '')
        comment_template = conf.get('comment_template', '')

        search_url = f"{target_url}?bugsearch={quote(search_keyword)}"
        print(f"DEBUG: Navigating to search URL -> {search_url}")
        browser_utils.navigate(self.driver, search_url)

        results = self._extract_results(target_url)
        self._print_results_table(results)

        summary = []
        for i, r in enumerate(results, start=1):
            result_label = self._process_row(i, len(results), r, target_status, new_status, comment_template, search_url)
            summary.append({**r, 'result': result_label})

        self._print_summary(summary)
        input(f"\n全{len(results)}件の確認が完了しました。Enterで終了...")

    # ------------------------------------------------------------------
    # private
    # ------------------------------------------------------------------

    def _extract_results(self, target_url: str) -> list:
        """検索結果行から task_id / status / detail_url を抽出して返す。"""
        base_url = target_url.rsplit("/", 1)[0] + "/"
        rows = browser_utils.find_elements(self.driver, "css", "tr[onclick*='idbug']")
        print(f"DEBUG: Found {len(rows)} result row(s)")

        results = []
        for row in rows:
            tds     = browser_utils.find_child_elements(row, "tag", "td")
            task_id = tds[0].text.strip() if tds else "?"
            title   = tds[1].text.strip() if len(tds) > 1 else "?"
            status  = tds[11].text.strip() if len(tds) > 11 else "?"
            onclick = browser_utils.get_attribute(row, "onclick")
            match   = re.search(r"location\.href='([^']+)'", onclick)
            detail_url = urljoin(base_url, match.group(1)) if match else None
            results.append({"task_id": task_id, "title": title, "status": status, "url": detail_url})
        return results

    def _print_results_table(self, results: list):
        print("\n" + "=" * 70)
        print(f"{'Task ID':<12} {'Title':<30} {'Status'}")
        print("-" * 70)
        for r in results:
            print(f"{r['task_id']:<12} {r['title']:<30} {r['status']}")
        print("=" * 70 + "\n")

    def _print_summary(self, summary: list):
        print("\n" + "=" * 70)
        print(" 処理結果サマリー")
        print("=" * 70)
        print(f"{'No':<4} {'Task ID':<12} {'Title':<30} {'結果'}")
        print("-" * 70)
        for i, r in enumerate(summary, start=1):
            print(f"{i:<4} {r['task_id']:<12} {r['title']:<30} {r['result']}")
        print("=" * 70)

    def _process_row(self, i: int, total: int, r: dict,
                     target_status: str, new_status: str,
                     comment_template: str, search_url: str) -> str:
        print(f"[{i}/{total}] Task ID: {r['task_id']} / Status: {r['status']}")

        if r['status'] != target_status:
            print(f"  ⚠ WARNING: Status が '{target_status}' ではないためスキップします。")
            return "⚠ スキップ"

        print(f"  → 詳細ページへ遷移: {r['url']}")
        browser_utils.navigate(self.driver, r['url'])

        self._prepend_comment(comment_template)
        self._change_status(new_status)
        self._save_and_screenshot(i, search_url)
        return "✓ 処理済み"

    def _prepend_comment(self, comment_template: str):
        today   = datetime.date.today()
        comment = (comment_template
                   .replace("[DATE_MD]", f"{today.month}/{today.day}")
                   .replace("[DATE_YYYYMMDD]", today.strftime("%Y%m%d")))
        browser_utils.prepend_text(self.driver, "name", "comments", comment)
        print("  → コメント追記完了")

    def _change_status(self, new_status: str):
        browser_utils.select_option_by_text(self.driver, "css", "select[name='status_edit']", new_status)
        print(f"  → ステータス変更完了: {new_status}")

        actual = browser_utils.get_selected_option_text(self.driver, "css", "select[name='status_edit']")
        if actual == new_status:
            print(f"  ✓ ステータス確認OK: {actual}")
        else:
            print(f"  ✗ ステータス不一致 期待値='{new_status}' 実際='{actual}'")

    def _save_and_screenshot(self, i: int, search_url: str):
        browser_utils.click_element_by_script(self.driver, "css", "img[onclick=\"setContent('a')\"]")
        print("  → カレンダーアイコンクリック完了")

        time.sleep(3)
        browser_utils.wait_for_page_load(self.driver)
        print("  → ページ遷移確認")

        browser_utils.click_element_by_script(self.driver, "css", "input[name='send'][value='Update Task Report Information']")
        print("  → 保存ボタンクリック完了")

        time.sleep(3)
        browser_utils.wait_for_page_load(self.driver)
        print("  → 保存完了")

        browser_utils.scroll_to_top(self.driver)
        screenshot_path = f"data/detail_{i}_{datetime.date.today()}.png"
        browser_utils.save_screenshot(self.driver, screenshot_path)
        print(f"  → Screenshot saved -> {screenshot_path}")

        browser_utils.navigate(self.driver, search_url)
        print("  → 検索結果に戻りました")
