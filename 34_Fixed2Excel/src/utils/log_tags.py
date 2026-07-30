TAG_START = "START"
TAG_END = "END"


def log_start(logger, message):
    """一連の処理の開始を示すログを出す（GUIでは他のINFOと別の色で表示される）"""
    logger.info(message, extra={"tag": TAG_START})


def log_end(logger, message):
    """一連の処理の完了を示すログを出す（GUIでは他のINFOと別の色で表示される）"""
    logger.info(message, extra={"tag": TAG_END})
