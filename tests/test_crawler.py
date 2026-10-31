"""Tests for tuyensinh_edu crawler — pure functions only (no network calls)."""

from bs4 import BeautifulSoup

from src.crawl.tuyensinh_edu import _extract_meta, _parse_table


def _make_table(rows: list[list[str]]) -> BeautifulSoup:
    header = "".join(f"<th>{h}</th>" for h in rows[0])
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows[1:])
    html = f"<table><tr>{header}</tr>{body}</table>"
    return BeautifulSoup(html, "lxml").find("table")


def test_parse_table_basic():
    table = _make_table(
        [
            ["STT", "Mã ngành", "Tên ngành", "Tổ hợp môn", "Điểm chuẩn", "Ghi chú"],
            ["1", "7480101", "Công nghệ thông tin", "A00", "27.5", ""],
        ]
    )
    records = _parse_table(table, 2021, "Test Uni", "TU")
    assert len(records) == 1
    assert records[0]["major_code"] == "7480101"
    assert records[0]["major_name"] == "Công nghệ thông tin"
    assert records[0]["score_combo"] == "A00"
    assert records[0]["cutoff_score"] == 27.5
    assert records[0]["university_name"] == "Test Uni"


def test_parse_table_multi_combo():
    """A cell like 'A00; A01' should produce two records."""
    table = _make_table(
        [
            ["STT", "Mã ngành", "Tên ngành", "Tổ hợp môn", "Điểm chuẩn", "Ghi chú"],
            ["1", "7480101", "CNTT", "A00; A01", "26.0", ""],
        ]
    )
    records = _parse_table(table, 2021, "Test Uni", "TU")
    assert len(records) == 2
    combos = {r["score_combo"] for r in records}
    assert combos == {"A00", "A01"}


def test_parse_table_skips_missing_score():
    table = _make_table(
        [
            ["STT", "Mã ngành", "Tên ngành", "Tổ hợp môn", "Điểm chuẩn", "Ghi chú"],
            ["1", "7480101", "CNTT", "A00", "Xét học bạ", ""],
            ["2", "7220201", "Kế toán", "D01", "25.0", ""],
        ]
    )
    records = _parse_table(table, 2021, "Test Uni", "TU")
    assert len(records) == 1
    assert records[0]["major_code"] == "7220201"


def test_parse_table_major_name_not_same_as_code():
    """Regression: 'ngành' in 'mã ngành' should not match major_name column."""
    table = _make_table(
        [
            ["STT", "Mã ngành", "Tên ngành", "Tổ hợp môn", "Điểm chuẩn", "Ghi chú"],
            ["1", "7340201", "Tài chính ngân hàng", "A00", "26.5", ""],
        ]
    )
    records = _parse_table(table, 2021, "Test Uni", "TU")
    assert len(records) == 1
    assert records[0]["major_name"] == "Tài chính ngân hàng"
    assert records[0]["major_name"] != records[0]["major_code"]


def test_parse_table_empty():
    table = _make_table([["STT", "Mã ngành", "Tên ngành", "Tổ hợp môn", "Điểm chuẩn", "Ghi chú"]])
    assert _parse_table(table, 2021, "Test Uni", "TU") == []


def test_extract_meta_strips_prefix_and_year():
    html = "<html><body><h1>Điểm chuẩn Đại Học Bách Khoa Hà Nội 2021</h1></body></html>"
    soup = BeautifulSoup(html, "lxml")
    code, name = _extract_meta(soup, "some-url")
    assert "2021" not in name
    assert "Điểm chuẩn" not in name
    assert "Bách Khoa" in name


def test_extract_meta_extracts_code_from_parenthetical():
    html = "<html><body><h1>Điểm chuẩn Đại Học Ngoại Thương (FTU) 2023</h1></body></html>"
    soup = BeautifulSoup(html, "lxml")
    code, name = _extract_meta(soup, "some-url")
    assert code == "FTU"
    assert "FTU" not in name


def test_extract_meta_no_h1():
    html = "<html><body><p>No heading</p></body></html>"
    soup = BeautifulSoup(html, "lxml")
    code, name = _extract_meta(soup, "some-url")
    assert code == ""
    assert name == ""
