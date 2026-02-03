import csv
import os

from src.utils.errors import UserInputError


def load_csv(path, required_columns):
    if not os.path.exists(path):
        raise UserInputError(f"input CSV not found: {path}")

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise UserInputError("CSVヘッダが読み取れません。")

        missing = [col for col in required_columns if col not in reader.fieldnames]
        if missing:
            raise UserInputError(f"CSVヘッダ不足: {', '.join(missing)}")

        rows = []
        for idx, row in enumerate(reader, start=2):
            row["_line_no"] = idx
            rows.append(row)
        return rows
