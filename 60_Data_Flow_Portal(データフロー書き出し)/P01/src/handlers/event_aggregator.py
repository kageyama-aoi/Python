from src.utils.attrs import build_attr_key
from src.utils.null_check import is_null


def aggregate_events(rows, null_values):
    events = []
    index = {}
    latest_by_table = {}

    for row in rows:
        case_id = row["case_id"]
        table = row.get("table", "")
        attr_key = build_attr_key(table, row["attr_type"])
        key = (case_id, table)
        if key not in index:
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
            index[key] = event
            events.append(event)
        else:
            event = index[key]

        before = row.get("before", "")
        after = row.get("after", "")
        event["changes"][attr_key] = {
            "before": before,
            "after": after,
            "note": row.get("note", ""),
        }

        if is_null(after, null_values):
            event["current_values"][attr_key] = None
        else:
            event["current_values"][attr_key] = after
        latest_by_table[table] = dict(event["current_values"])

    return events
