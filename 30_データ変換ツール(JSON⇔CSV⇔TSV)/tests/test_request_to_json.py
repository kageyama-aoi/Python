import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import request_to_json as m


def test_request_to_json_basic():
    result = m.request_to_json("loginId=0190019&pwd=n6hj%2AoA&smsgroup=teacher")
    assert result == {"loginId": "0190019", "pwd": "n6hj*oA", "smsgroup": "teacher"}


def test_request_to_json_single_param():
    assert m.request_to_json("loginId=abc") == {"loginId": "abc"}


def test_request_to_json_empty_string_returns_empty_dict():
    assert m.request_to_json("") == {}


def test_request_to_json_duplicate_key_keeps_first_value():
    # urllib.parse.parse_qs は同じキーが複数あると値のリストになる。
    # request_to_json は [0] を採用するため、最初の値が残る仕様。
    result = m.request_to_json("id=1&id=2")
    assert result == {"id": "1"}
