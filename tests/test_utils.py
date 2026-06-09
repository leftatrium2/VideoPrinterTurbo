import pytest
from app.utils.utils import (
    get_response,
    get_uuid,
    split_string_by_punctuations,
    text_to_srt,
    time_convert_seconds_to_hmsm,
)


def test_time_convert_zero():
    assert time_convert_seconds_to_hmsm(0) == "00:00:00,000"


def test_time_convert_whole_minutes():
    assert time_convert_seconds_to_hmsm(90) == "00:01:30,000"


def test_time_convert_with_milliseconds():
    assert time_convert_seconds_to_hmsm(3723.456) == "01:02:03,456"


def test_text_to_srt_format():
    result = text_to_srt(1, "Hello world", 0.0, 1.5)
    assert "1\n" in result
    assert " --> " in result
    assert "Hello world" in result
    assert "00:00:00,000 --> 00:00:01,500" in result


def test_split_by_punctuation():
    result = split_string_by_punctuations("Hello, world.")
    assert result == ["Hello", "world"]


def test_split_preserves_decimal_numbers():
    result = split_string_by_punctuations("3.14 is pi")
    assert result == ["3.14 is pi"]


def test_get_uuid_has_hyphens():
    uid = get_uuid()
    assert len(uid) == 36
    assert "-" in uid


def test_get_uuid_without_hyphens():
    uid = get_uuid(remove_hyphen=True)
    assert len(uid) == 32
    assert "-" not in uid


def test_get_response_with_data():
    resp = get_response(200, {"key": "val"})
    assert resp["status"] == 200
    assert resp["data"] == {"key": "val"}


def test_get_response_without_data():
    resp = get_response(404)
    assert resp["status"] == 404
    assert "data" not in resp
