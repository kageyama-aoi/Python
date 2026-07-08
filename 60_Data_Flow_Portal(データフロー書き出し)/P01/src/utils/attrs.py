def build_attr_key(table, attr_type):
    return f"{table}::{attr_type}"


def split_attr_key(column):
    if "::" in column:
        table, attr = column.split("::", 1)
        return table, attr
    return "", column


def extract_attr_label(column):
    _, attr = split_attr_key(column)
    return attr
