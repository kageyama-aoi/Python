def aggregate_events(rows, null_values):
    events = []
    index = {}
    latest_by_table = {}

    for row in rows:
        case_id = row["case_id"]
        table = row.get("table", "")
        if case_id not in index:
            current_values = dict(latest_by_table.get(table, {}))
            event = {
                "case_id": case_id,
                "table": table,
                "operation": row.get("operation", ""),
                "trigger": row.get("trigger", ""),
                "sql": row.get("sql", ""),
                "changes": {},
                "current_values": current_values,
            }
            index[case_id] = event
            events.append(event)
        else:
            event = index[case_id]

        attr_type = row["attr_type"]
        before = row.get("before", "")
        after = row.get("after", "")
        event["changes"][attr_type] = {
            "before": before,
            "after": after,
            "note": row.get("note", ""),
        }

        if is_null(after, null_values):
            event["current_values"][attr_type] = None
        else:
            event["current_values"][attr_type] = after
        latest_by_table[table] = dict(event["current_values"])

    return events


def is_null(value, null_values):
    if value is None:
        return True
    text = str(value).strip()
    if text == "":
        return True
    return text.lower() in {str(v).lower() for v in null_values}
