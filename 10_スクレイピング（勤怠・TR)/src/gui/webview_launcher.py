"""
工数入力UI（pywebview）をサブプロセスで起動するランチャー。
"""
import os
import sys
import subprocess


def open_crowdlog_input():
    """工数入力UIをサブプロセスで起動する。"""
    script = os.path.join(os.path.dirname(__file__), "..", "crowdlog_input_ui.py")
    subprocess.Popen(
        [sys.executable, script],
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
    )
