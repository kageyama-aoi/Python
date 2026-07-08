import csv
from pathlib import Path

from utils import load_postcodes, POSTCODE_COL

ROOT_DIR = Path(__file__).parent.parent
INPUT_DIR = ROOT_DIR / "input"
OUTPUT_DIR = ROOT_DIR / "output"

OLD_FILE = INPUT_DIR / "0305_1518_yubin.csv"
NEW_FILE = INPUT_DIR / "0305_1518_yubin_new.csv"


def write_diff(only_old: set[str], only_new: set[str], both: set[str]) -> None:
    def _write(path: Path, postcodes: set[str]) -> None:
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow([POSTCODE_COL])
            for postcode in sorted(postcodes):
                writer.writerow([postcode])

    _write(OUTPUT_DIR / f"postcode_only_in_{OLD_FILE.stem}.csv", only_old)
    _write(OUTPUT_DIR / f"postcode_only_in_{NEW_FILE.stem}.csv", only_new)
    _write(OUTPUT_DIR / "postcode_in_both.csv", both)

    print("=== Postcode Diff Result ===")
    print(f"old_file : {OLD_FILE.name} ({len(only_old) + len(both)} unique postcodes)")
    print(f"new_file : {NEW_FILE.name} ({len(only_new) + len(both)} unique postcodes)")
    print(f"only_in_old : {len(only_old)}")
    print(f"only_in_new : {len(only_new)}")
    print(f"in_both     : {len(both)}")


def enrich_new_file(old_postcodes: set[str]) -> None:
    # この比較は2ファイル間の観測差分ベース。
    # 公式な「発行日」そのものは元データにないため、観測上の推定情報として付与する。
    output_file = OUTPUT_DIR / f"{NEW_FILE.stem}_with_issue_info.csv"

    with open(NEW_FILE, "r", encoding="utf-8", newline="") as src, open(
        output_file, "w", encoding="utf-8", newline=""
    ) as dst:
        reader = csv.DictReader(src)
        if reader.fieldnames is None or POSTCODE_COL not in reader.fieldnames:
            raise ValueError(f"{NEW_FILE.name} に '{POSTCODE_COL}' 列がありません")

        extra_cols = ["issue_info", "issue_date_estimate", "issue_note"]
        writer = csv.DictWriter(
            dst, fieldnames=reader.fieldnames + extra_cols, quoting=csv.QUOTE_ALL
        )
        writer.writeheader()

        existing_count = 0
        new_count = 0

        for row in reader:
            postcode = (row.get(POSTCODE_COL) or "").strip()

            if postcode and postcode in old_postcodes:
                row["issue_info"] = "already_exists_in_old_file"
                row["issue_date_estimate"] = "<=2026-03-05"
                row["issue_note"] = "旧ファイルにも存在するため、この日以前に発行済みと推定"
                existing_count += 1
            else:
                row["issue_info"] = "new_in_current_file"
                row["issue_date_estimate"] = "2026-03-05"
                row["issue_note"] = "旧ファイルに無く新ファイルで初観測（この日付で推定）"
                new_count += 1

            writer.writerow(row)

    print("=== Enriched CSV Created ===")
    print(f"output_file             : {output_file.name}")
    print(f"already_exists_in_old   : {existing_count}")
    print(f"new_in_current_file     : {new_count}")


def main() -> None:
    for path in (OLD_FILE, NEW_FILE):
        if not path.exists():
            raise FileNotFoundError(f"入力ファイルが見つかりません: {path}")

    OUTPUT_DIR.mkdir(exist_ok=True)

    old_postcodes = load_postcodes(OLD_FILE)
    new_postcodes = load_postcodes(NEW_FILE)

    write_diff(
        only_old=old_postcodes - new_postcodes,
        only_new=new_postcodes - old_postcodes,
        both=old_postcodes & new_postcodes,
    )
    print()
    enrich_new_file(old_postcodes)
    print()
    print(f"output_dir: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
