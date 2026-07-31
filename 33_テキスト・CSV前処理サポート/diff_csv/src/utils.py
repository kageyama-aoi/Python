import csv
from pathlib import Path

POSTCODE_COL = "postcode"


def load_postcodes(csv_path: Path) -> set[str]:
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or POSTCODE_COL not in reader.fieldnames:
            raise ValueError(f"{csv_path.name} に '{POSTCODE_COL}' 列がありません")

        postcodes = set()
        for row in reader:
            postcode = (row.get(POSTCODE_COL) or "").strip()
            if postcode:
                postcodes.add(postcode)
    return postcodes
