def is_null(value, null_values):
    """値がNULL相当かどうかを判定する。null_values は小文字化済みの集合を期待する。"""
    if value is None:
        return True
    text = str(value).strip()
    if text == "":
        return True
    return text.lower() in {str(v).lower() for v in null_values}


def is_blank(value):
    """値が空白・None かどうかを判定する。"""
    return value is None or str(value).strip() == ""
