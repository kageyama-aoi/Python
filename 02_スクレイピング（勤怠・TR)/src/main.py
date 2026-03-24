"""
自動操作ツールのエントリーポイント。
ユーザー入力を受け付け、ブラウザを起動し、フォーム自動入力処理を実行します。
"""
import os
import re
import time
import datetime
import tkinter as tk
from tkinter import messagebox
from urllib.parse import urljoin, quote
from selenium import webdriver

import config
import browser_utils
import file_utils
from form_handler import FormAutomationHandler
import gui

# ログファイル名の設定
log_folder = '{0}.log'.format(datetime.date.today())


def main():
    # 設定ファイルの読み込み
    config.load_config("config/main.yaml")
    logger = config.setup_logger(log_folder)

    # GUIによるユーザー入力の取得
    user_select_school, environment_name, search_keyword = gui.get_user_input_gui()

    # ユーザーがキャンセルまたは閉じた場合
    if user_select_school is None:
        print("操作がキャンセルされました。")
        return

    # ブラウザの初期化
    driver = webdriver.Chrome()
    driver.set_window_size(1000, 1000)
    driver.implicitly_wait(10)

    try:
        print(f"DEBUG: Selected School Type: {user_select_school}")

        if user_select_school == 'cl':
            target_url = config.CONF.get('crowdlog_settings', {}).get('entry_url', '')
        else:
            target_url = config.CONF.get('task_report_settings', {}).get('entry_url', '')

        # 検索モード
        if user_select_school == 'search':
            shimamura_search_conf = config.CONF.get('task_report_settings', {}).get('shimamura_search', {})
            TARGET_STATUS = shimamura_search_conf.get('target_status', '')
            NEW_STATUS    = shimamura_search_conf.get('new_status', '')
            search_url = f"{target_url}?bugsearch={quote(search_keyword)}"
            print(f"DEBUG: Navigating to search URL -> {search_url}")
            browser_utils.navigate(driver, search_url)

            # 検索結果行の情報を全件先に抽出
            base_url = target_url.rsplit("/", 1)[0] + "/"
            rows = browser_utils.find_elements(driver, "css", "tr[onclick*='idbug']")
            print(f"DEBUG: Found {len(rows)} result row(s)")

            results = []
            for row in rows:
                tds = browser_utils.find_child_elements(row, "tag", "td")
                task_id = tds[0].text.strip() if tds else "?"
                status  = tds[11].text.strip() if len(tds) > 11 else "?"
                onclick = browser_utils.get_attribute(row, "onclick")
                match = re.search(r"location\.href='([^']+)'", onclick)
                detail_url = urljoin(base_url, match.group(1)) if match else None
                results.append({"task_id": task_id, "status": status, "url": detail_url})

            # Task ID / Status 一覧を表形式で出力
            print("\n" + "="*50)
            print(f"{'Task ID':<12} {'Status'}")
            print("-"*50)
            for r in results:
                print(f"{r['task_id']:<12} {r['status']}")
            print("="*50 + "\n")

            # 各詳細ページへ遷移 → 条件チェック → 処理 → スクリーンショット → 検索結果に戻る
            for i, r in enumerate(results, start=1):
                print(f"[{i}/{len(results)}] Task ID: {r['task_id']} / Status: {r['status']}")

                if r['status'] != TARGET_STATUS:
                    print(f"  ⚠ WARNING: Status が '{TARGET_STATUS}' ではないためスキップします。")
                    continue

                print(f"  → 詳細ページへ遷移: {r['url']}")
                browser_utils.navigate(driver, r['url'])

                # コメント欄の先頭にテンプレートを追記（日付プレースホルダを置換）
                today = datetime.date.today()
                comment_template = shimamura_search_conf.get('comment_template', '')
                comment = (comment_template
                           .replace("[DATE_MD]", f"{today.month}/{today.day}")
                           .replace("[DATE_YYYYMMDD]", today.strftime("%Y%m%d")))
                browser_utils.prepend_text(driver, "name", "comments", comment)
                print(f"  → コメント追記完了")

                # ステータスを変更（CSSで<select>要素を明示指定、表示テキストで選択）
                browser_utils.select_option_by_text(driver, "css", "select[name='status']", NEW_STATUS)
                print(f"  → ステータス変更完了: {NEW_STATUS}")

                # Owned By 隣のカレンダーアイコンをクリック（保存・遷移）
                browser_utils.click_element_by_script(driver, "css", "img[onclick=\"setContent('a')\"]")
                print(f"  → カレンダーアイコンクリック完了")

                # 保存処理完了を待つ
                time.sleep(3)

                # スクリーンショット（保存後の画面を撮影）
                screenshot_path = f"data/detail_{i}_{datetime.date.today()}.png"
                browser_utils.save_screenshot(driver, screenshot_path)
                print(f"  → Screenshot saved -> {screenshot_path}")

                # 検索結果に戻る
                browser_utils.navigate(driver, search_url)

            input(f"\n全{len(results)}件の確認が完了しました。Enterで終了...")
            return

        # 初期遷移
        print(f"DEBUG: Navigating to {target_url}")
        browser_utils.navigate(driver, target_url)

        # 初期アクション（タスクレポート作成系のみ）
        if user_select_school != 'cl':
            tr_settings = config.CONF.get('task_report_settings', {})
            btn_selector = tr_settings.get('selectors', {}).get('new_bug_button_dom_attribute')

            if btn_selector and browser_utils.is_element_present(driver, "name", btn_selector):
                browser_utils.click_element(driver, "name", btn_selector)
            elif btn_selector:
                print(f"Warning: New bug button ({btn_selector}) not found on page.")

        # メイン処理：フォーム入力の実行
        context = {
            'schools_type': user_select_school,
            'environment_name': environment_name
        }
        form_handler = FormAutomationHandler(driver, context)
        form_handler.fill_form()

        # CrowdLogの場合、ファイルのダウンロード完了を待って移動
        if user_select_school == 'cl':
            default_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            target_dir = config.CONF['app'].get('download_dir', 'data/downloads/')

            moved_path = file_utils.move_latest_downloaded_file(default_download_dir, target_dir)

            if moved_path:
                msg = f'CSVのダウンロードと移動が完了しました！\n保存先: {moved_path}'
            else:
                msg = 'ダウンロードのタイムアウト、またはファイルが見つかりませんでした。'
        else:
            msg = '下書きを作成しました！'

        # 完了通知
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo('完了メッセージ', msg)

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        raise e


if __name__ == "__main__":
    main()
