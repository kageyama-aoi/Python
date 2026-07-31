TAG_START = "START"
TAG_END = "END"
TAG_DIFF = "DIFF"


def log_start(logger, message):
    """一連の処理の開始を示すログを出す（GUIでは他のINFOと別の色で表示される）"""
    logger.info(message, extra={"tag": TAG_START})


def log_end(logger, message):
    """一連の処理の完了を示すログを出す（GUIでは他のINFOと別の色で表示される）"""
    logger.info(message, extra={"tag": TAG_END})


def log_diff(logger, message):
    """差分チェックの項目単位の差分detail行を示すログを出す（GUIでは他のINFOと別の色で表示される）"""
    logger.info(message, extra={"tag": TAG_DIFF})
