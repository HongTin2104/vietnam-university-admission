# Dataset Card — Vietnam University Admission Scores

## Overview

Cutoff scores (điểm chuẩn) for university admissions in Vietnam, collected from official
university websites and the Ministry of Education & Training portal.

| Field          | Value                              |
| -------------- | ---------------------------------- |
| Years covered  | 2020 – 2026 (updated each August)  |
| Universities   | TBD after crawl                    |
| Total records  | TBD                                |
| Last collected | TBD                                |
| License        | CC BY 4.0                          |

## Source

- Official university admission portals (each school publishes annually)
- Ministry of Education & Training: <https://moet.gov.vn>
- Only public, non-personal data is collected.

## Columns (`data/processed/scores.csv`)

| Column             | Type    | Description                                           |
| ------------------ | ------- | ----------------------------------------------------- |
| `year`             | int     | Academic year (e.g. 2024)                             |
| `university_code`  | str     | Official university code (e.g. QHD)                   |
| `university_name`  | str     | Full university name (Vietnamese)                     |
| `major_code`       | str     | Ministry-assigned major code                          |
| `major_name`       | str     | Major name (Vietnamese)                               |
| `score_combo`      | str     | Score combination (e.g. A00, A01, B00, D01)           |
| `cutoff_score`     | float   | Cutoff score for this year / major / combo            |
| `region_priority`  | int     | Regional priority applied (0 = none, 1/2/3 = rural)  |
| `quota`            | int     | Intake quota (null if not published)                  |
| `notes`            | str     | Extra notes (scholarship track, etc.)                 |

## Limitations

- Cutoff scores before 2020 are harder to verify; not included in v0.1.
- Some universities do not publish quota or notes.
- Scores for admission methods other than the national exam (xét học bạ, etc.) are not included in v0.1.

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
