import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import csv_to_tsv as m


def test_convert_csv_to_tsv_utf8(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("name,age\n田中,20\n", encoding="utf-8")

    out_dir = tmp_path / "output"
    tsv_path = m.convert_csv_to_tsv(csv_path, output_dir=out_dir)

    assert tsv_path == out_dir / "sample.tsv"
    assert tsv_path.read_text(encoding="utf-8") == "name\tage\n田中\t20\n"


def test_convert_csv_to_tsv_shift_jis_fallback(tmp_path):
    csv_path = tmp_path / "sjis.csv"
    csv_path.write_bytes("名前,年齢\n鈴木,30\n".encode("cp932"))

    out_dir = tmp_path / "output"
    tsv_path = m.convert_csv_to_tsv(csv_path, output_dir=out_dir)

    assert tsv_path.read_text(encoding="utf-8") == "名前\t年齢\n鈴木\t30\n"


def test_decode_with_fallback_raises_on_undecodable(tmp_path):
    bad_path = tmp_path / "bad.csv"
    bad_path.write_bytes(b"a,b\n\x80\x81,\xff\xfe\n")

    with pytest.raises(m.CsvToTsvError):
        m._decode_with_fallback(bad_path)


def test_convert_csv_to_tsv_output_dir_is_created(tmp_path):
    csv_path = tmp_path / "a.csv"
    csv_path.write_text("x,y\n1,2\n", encoding="utf-8")
    out_dir = tmp_path / "nested" / "output"

    assert not out_dir.exists()
    m.convert_csv_to_tsv(csv_path, output_dir=out_dir)
    assert out_dir.is_dir()
