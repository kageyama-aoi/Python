
import csv
from pathlib import Path

def main():
    # カレントディレクトリのCSVファイルを検索
    csv_files = list(Path.cwd().glob('*.csv'))
    
    print(f"Found {len(csv_files)} CSV files:")
    for csv_path in csv_files:
        print(f"- {csv_path.name}")

    for csv_path in csv_files:
        tsv_path = csv_path.with_suffix('.tsv')

        with csv_path.open('r', encoding='utf-8') as infile, \
             tsv_path.open('w', encoding='utf-8', newline='') as outfile:
            
            reader = csv.reader(infile)
            writer = csv.writer(outfile, delimiter='\t')

            for row in reader:
                writer.writerow(row)

        print(f"✅ Converted {csv_path.name} to {tsv_path.name}")

if __name__ == "__main__":
    main()

