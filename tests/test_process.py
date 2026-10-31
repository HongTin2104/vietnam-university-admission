"""Tests for data cleaning pipeline."""

import pandas as pd

from src.process.clean import _normalize_combo, _normalize_major_code, _normalize_name, clean


def test_normalize_combo_valid():
    assert _normalize_combo("A00") == "A00"
    assert _normalize_combo("a01") == "A01"
    assert _normalize_combo("Tổ hợp D01") == "D01"


def test_normalize_combo_unknown_returns_extracted():
    result = _normalize_combo("X99")
    # X is not a valid prefix — returns raw stripped uppercase
    assert result == "X99"


def test_normalize_name_strips_whitespace():
    assert _normalize_name("  Công  nghệ  thông  tin  ") == "Công nghệ thông tin"


def test_normalize_major_code_extracts_7_digits():
    assert _normalize_major_code("Mã ngành: 7480201") == "7480201"
    assert _normalize_major_code("7480201") == "7480201"


def test_normalize_major_code_no_digits_returns_stripped():
    assert _normalize_major_code("  N/A  ") == "N/A"


def test_clean_removes_invalid_scores():
    records = [
        {
            "year": 2024,
            "university_code": "BKA",
            "university_name": "Bách Khoa",
            "major_code": "7480201",
            "major_name": "CNTT",
            "score_combo": "A00",
            "cutoff_score": 27.5,
            "region_priority": 0,
        },
        {
            "year": 2024,
            "university_code": "BKA",
            "university_name": "Bách Khoa",
            "major_code": "7480201",
            "major_name": "CNTT",
            "score_combo": "A00",
            "cutoff_score": 99.0,  # invalid
            "region_priority": 0,
        },
    ]
    df = clean(records)
    assert len(df) == 1
    assert df.iloc[0]["cutoff_score"] == 27.5


def test_clean_deduplicates_keeps_highest():
    records = [
        {
            "year": 2024,
            "university_code": "BKA",
            "university_name": "Bách Khoa",
            "major_code": "7480201",
            "major_name": "CNTT",
            "score_combo": "A00",
            "cutoff_score": 27.5,
            "region_priority": 0,
        },
        {
            "year": 2024,
            "university_code": "BKA",
            "university_name": "Bách Khoa",
            "major_code": "7480201",
            "major_name": "CNTT",
            "score_combo": "A00",
            "cutoff_score": 28.0,  # duplicate, higher
            "region_priority": 0,
        },
    ]
    df = clean(records)
    assert len(df) == 1
    assert df.iloc[0]["cutoff_score"] == 28.0


def test_clean_empty_input():
    df = clean([])
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
