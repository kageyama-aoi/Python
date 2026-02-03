def aggregate_events(rows):
    events = []
    index = {}

    for row in rows:
        event_id = row["event_id"]
        if event_id not in index:
            event = {
                "event_id": event_id,
                "table": row.get("table", ""),
                "operation": row.get("operation", ""),
                "trigger": row.get("trigger", ""),
                "sql": row.get("sql", ""),
                "changes": {},
            }
            index[event_id] = event
            events.append(event)
        else:
            event = index[event_id]

        attr_type = row["attr_type"]
        event["changes"][attr_type] = {
            "before": row.get("before", ""),
            "after": row.get("after", ""),
            "note": row.get("note", ""),
        }

    return events
