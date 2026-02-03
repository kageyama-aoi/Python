from src.utils.errors import UserInputError


def fill_context(rows, carry_columns, required_columns):
    filled = []
    context = {}
    current_event_id = None

    for row in rows:
        line_no = row.get("_line_no")
        event_id = row.get("event_id", "")
        if is_blank(event_id):
            raise UserInputError("event_id が欠落しています。", line_no, row)

        if event_id != current_event_id:
            context = {}
            current_event_id = event_id

        for column in carry_columns:
            value = row.get(column, "")
            if is_blank(value):
                if column in context:
                    row[column] = context[column]
            else:
                context[column] = value

        for column in required_columns:
            if is_blank(row.get(column, "")):
                raise UserInputError(f"{column} が欠落しています。", line_no, row)

        filled.append(row)

    return filled


def is_blank(value):
    return value is None or str(value).strip() == ""
