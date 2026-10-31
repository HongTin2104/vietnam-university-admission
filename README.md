# Vietnam University Admission Scores

> Bộ dữ liệu điểm chuẩn đại học Việt Nam 2020–2026 kèm hệ gợi ý ngành/trường có giải thích lý do.

<!-- TODO: replace with real GIF after Streamlit Community Cloud deploy -->
<!-- ![Demo](docs/demo.gif) -->

[![CI](https://github.com/HongTin2104/vietnam-university-admission/actions/workflows/ci.yml/badge.svg)](https://github.com/HongTin2104/vietnam-university-admission/actions)

## Problem

Every July–August, thousands of Vietnamese students search for university cutoff scores to plan
which schools and majors to apply to. Existing GitHub repositories either:

- Stop at 2018 and have no demo (3 stars)
- Are plain notebooks with no processing pipeline
- Show only a single year, no trend

This project provides:

- A **clean, reproducible dataset** covering 2020–2026 with a full data card.
- A **recommendation engine** that takes a student's scores and subject combination, and returns
  ranked university/major pairs in three tiers (target / safety / reach), each with a
  plain-Vietnamese explanation of *why* that school was suggested.
- A **Streamlit web app** — try it without installing anything.

## Dataset

| Metric       | Value                          |
| ------------ | ------------------------------ |
| Years        | 2020 – 2026                    |
| Source       | Official university portals + Bộ GD&ĐT |
| License      | CC BY 4.0                      |

→ Full data card: [data/DATASET.md](data/DATASET.md)

To reproduce the full dataset from scratch:

```bash
python -m src.crawl.run_crawl --years 2020 2021 2022 2023 2024 2025 2026
python -m src.process.run_process
```

## How It Works

```
Official university portals
        │
        ▼ src/crawl/     rate-limited (2 s/req), respects robots.txt
        │
        ▼ src/process/   normalize names, deduplicate, filter invalid scores
        │
        ▼ data/processed/scores.csv
        │
        ▼ src/model/     score-range filter + tier ranking + explanation
        │
        ▼ src/app/       Streamlit UI (3 tabs)
```

## Results

Recommendation quality on 2024 data (32 manually verified records):

| Metric                      | Value  |
| --------------------------- | ------ |
| Target-tier precision\*     | —      |
| Safety-tier recall\*        | —      |

\* Will be filled after full dataset is collected.

## Quickstart

```bash
git clone https://github.com/HongTin2104/vietnam-university-admission
cd vietnam-university-admission
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
streamlit run src/app/main.py
```

Or with Docker:

```bash
docker build -t vn-admission .
docker run -p 8501:8501 vn-admission
```

## Project Structure

```
vietnam-university-admission/
├── data/
│   ├── raw/             # scraped HTML (not committed — too large)
│   ├── processed/       # scores.csv (committed)
│   └── DATASET.md       # data card
├── src/
│   ├── crawl/           # run_crawl.py, tuyensinh247.py, base.py
│   ├── process/         # clean.py, run_process.py
│   ├── model/           # recommend.py
│   └── app/             # main.py (Streamlit)
├── tests/
├── .github/workflows/ci.yml
└── requirements.txt
```

## Limitations & Roadmap

- v0.1 covers national-exam admissions only; *xét học bạ* is not included.
- Cutoff scores before 2020 are excluded due to format inconsistencies.
- v0.2 plans: add *xét học bạ* scores, expose a REST API, add per-province filtering.

---

## Dành cho sinh viên Việt Nam

Nếu bạn muốn dùng repo này làm tài liệu tham khảo cho đồ án tốt nghiệp:

- **Dữ liệu**: thu thập từ trang chính thức các trường và Bộ GD&ĐT — không lấy từ Kaggle.
- **Quy trình có thể chạy lại**: từ `run_crawl.py` → `run_process.py` → `streamlit run` là đủ.
- **Hệ gợi ý đơn giản**: content-based filtering theo điểm và tổ hợp môn — phù hợp làm baseline
  để so sánh với collaborative filtering hoặc mô hình học máy nếu bạn muốn mở rộng.
- **Test**: `pytest` chạy được ngay, coverage được theo dõi tự động qua CI.
- Nếu bạn dùng repo này, hãy ghi nguồn theo phần Citation bên dưới.

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
