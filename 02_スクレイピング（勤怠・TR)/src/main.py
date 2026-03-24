"""
自動操作ツールのエントリーポイント。
ユーザー入力を受け付け、ブラウザを起動し、フォーム自動入力処理を実行します。
"""
import os
import datetime

import config
import browser_utils
import file_utils
from handler_factory import HandlerFactory
from handlers import ShimamuraSearchHandler
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
    driver = browser_utils.create_driver()

    try:
        print(f"DEBUG: Selected School Type: {user_select_school}")

        if user_select_school == 'cl':
            target_url = config.CONF.get('crowdlog_settings', {}).get('entry_url', '')
        else:
            target_url = config.CONF.get('task_report_settings', {}).get('entry_url', '')

        # 検索モード
        if user_select_school == 'search':
            handler = ShimamuraSearchHandler(driver, {
                'search_keyword': search_keyword,
                'target_url': target_url,
            })
            handler.execute()
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
        HandlerFactory(driver, context).execute()

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
        gui.show_completion_message(msg)

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        raise e


if __name__ == "__main__":
    main()
