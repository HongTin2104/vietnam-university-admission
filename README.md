# Vietnam University Admission Scores

> Bộ dữ liệu điểm chuẩn đại học Việt Nam 2020–2026 kèm hệ gợi ý ngành/trường có giải thích lý do.

<!-- TODO: add demo GIF and Streamlit link after Phase 5 -->

## Problem

Every July–August, thousands of Vietnamese students search for university cutoff scores to decide
which schools and majors to apply to. Existing GitHub repositories either stop at 2018, publish
only raw notebooks with no demo, or lack multi-year trend data. This project provides:

- A **clean, reproducible dataset** covering 2020–2026 with a documented data card.
- A **recommendation system** that takes a student's scores and subject combination and returns
  ranked university/major pairs, with a plain-language explanation for each suggestion.
- A **Streamlit web app** — no local install needed.

## Dataset

| Metric           | Value                          |
| ---------------- | ------------------------------ |
| Years            | 2020 – 2026                    |
| Universities     | TBD                            |
| Total records    | TBD                            |
| License          | CC BY 4.0                      |

→ See [data/DATASET.md](data/DATASET.md) for full data card and column descriptions.

## How It Works

```
Official university portals
        │
        ▼
  src/crawl/       ← rate-limited scraper, respects robots.txt
        │
        ▼
  src/process/     ← normalize scores, fix encoding, deduplicate
        │
        ▼
  data/processed/scores.csv
        │
        ▼
  src/model/       ← content-based filtering + score-range matching
        │
        ▼
  src/app/         ← Streamlit UI
```

## Results

<!-- TODO: add evaluation table after Phase 4 -->

## Quickstart

```bash
git clone https://github.com/HongTin2104/vietnam-university-admission
cd vietnam-university-admission
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
streamlit run src/app/main.py
```

Or run with Docker:

```bash
docker build -t vn-admission .
docker run -p 8501:8501 vn-admission
```

## Project Structure

```
vietnam-university-admission/
├── data/
│   ├── raw/            # scraped JSON (not committed — too large)
│   ├── processed/      # clean CSV (committed)
│   └── DATASET.md
├── src/
│   ├── crawl/
│   ├── process/
│   ├── model/
│   └── app/
├── notebooks/          # EDA (01_explore.ipynb, ...)
├── tests/
└── requirements.txt
```

## Limitations & Roadmap

- v0.1 covers only national-exam admission (thi THPT); xét học bạ is not included.
- Scores before 2020 are harder to verify and excluded for now.
- Planned: v0.2 will add xét học bạ scores and a REST API.

---

## Dành cho sinh viên Việt Nam

Nếu bạn muốn dùng repo này làm tài liệu tham khảo cho đồ án, đây là những điểm đáng chú ý:

- **Dữ liệu**: thu thập từ các trang chính thức của trường và Bộ GD&ĐT, không dùng Kaggle.
- **Xử lý tiếng Việt**: chuẩn hoá tên ngành có dấu/không dấu và mã tổ hợp môn.
- **Mô hình**: content-based filtering đơn giản, có thể thay bằng collaborative filtering nếu có dữ liệu lựa chọn của sinh viên.
- **Chạy lại**: mọi bước từ crawl → app đều có script; metric trong README có thể tái tạo bằng `pytest`.

## Citation

```bibtex
@dataset{vn_admission_scores_2026,
  title   = {Vietnam University Admission Scores 2020--2026},
  author  = {HongTin2104},
  year    = {2026},
  url     = {https://github.com/HongTin2104/vietnam-university-admission},
  license = {CC BY 4.0}
}
```

## License

Code: MIT · Data: CC BY 4.0
