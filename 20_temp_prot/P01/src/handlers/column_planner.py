def plan_columns(rows, priority_columns):
    counts = {}
    order = {}

    for idx, row in enumerate(rows):
        attr = row["attr_type"]
        counts[attr] = counts.get(attr, 0) + 1
        if attr not in order:
            order[attr] = idx

    sorted_columns = sorted(
        counts.keys(),
        key=lambda col: (-counts[col], order[col]),
    )

    priority = [col for col in priority_columns if col in sorted_columns]
    remaining = [col for col in sorted_columns if col not in priority]
    return priority + remaining
