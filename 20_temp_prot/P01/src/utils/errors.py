class UserInputError(Exception):
    def __init__(self, message, line_no=None, row=None):
        super().__init__(message)
        self.message = message
        self.line_no = line_no
        self.row = row

    def __str__(self):
        parts = [self.message]
        if self.line_no is not None:
            parts.append(f"line={self.line_no}")
        if self.row:
            parts.append(f"row={format_row_excerpt(self.row)}")
        return " | ".join(parts)


def format_row_excerpt(row, max_len=160):
    items = []
    for key, value in row.items():
        items.append(f"{key}={value}")
    text = ", ".join(items)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text
