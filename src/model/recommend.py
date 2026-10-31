"""Score-based university/major recommendation with plain-language explanations.

Algorithm:
1. Filter by score_combo matching the student's subject combination.
2. Keep only majors whose cutoff_score <= student's score + tolerance.
3. Rank by (cutoff_score DESC, year DESC) — closest to cutoff first,
   favouring the most recent year's data.
4. Build a human-readable reason for each recommendation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_DATA_PATH = Path("data/processed/scores.csv")

# How many points above student score to include (catches schools they can safely aim for)
REACH_MARGIN = 1.0
# How many points below to include (safety schools)
SAFETY_MARGIN = 5.0


@dataclass
class Recommendation:
    university_name: str
    university_code: str
    major_name: str
    major_code: str
    cutoff_score: float
    year: int
    score_combo: str
    gap: float  # student_score - cutoff_score (positive = comfortable)
    reason: str
    trend: str = ""  # e.g. "↑ tăng 0.5đ so với 2023"


@dataclass
class RecommendationResult:
    student_score: float
    score_combo: str
    reach: list[Recommendation] = field(default_factory=list)
    target: list[Recommendation] = field(default_factory=list)
    safety: list[Recommendation] = field(default_factory=list)


def _build_reason(row: pd.Series, gap: float) -> str:
    if gap > 2:
        comfort = f"điểm của bạn cao hơn điểm chuẩn {gap:.2f} điểm — an toàn"
    elif gap > 0:
        comfort = f"điểm của bạn cao hơn điểm chuẩn {gap:.2f} điểm"
    elif gap == 0:
        comfort = "điểm của bạn đúng bằng điểm chuẩn"
    else:
        comfort = f"điểm chuẩn cao hơn {abs(gap):.2f} điểm — cần phấn đấu thêm"
    return (
        f"Tổ hợp {row['score_combo']} · Điểm chuẩn {row['year']}: {row['cutoff_score']} · {comfort}"
    )


def _score_trend(df_uni_major: pd.DataFrame) -> str:
    """Return a short trend string comparing the two most recent years."""
    years = sorted(df_uni_major["year"].unique(), reverse=True)
    if len(years) < 2:
        return ""
    latest = df_uni_major[df_uni_major["year"] == years[0]]["cutoff_score"].mean()
    prev = df_uni_major[df_uni_major["year"] == years[1]]["cutoff_score"].mean()
    delta = latest - prev
    if abs(delta) < 0.05:
        return f"→ ổn định so với {years[1]}"
    direction = "↑ tăng" if delta > 0 else "↓ giảm"
    return f"{direction} {abs(delta):.2f}đ so với {years[1]}"


class Recommender:
    def __init__(self, data_path: Path = DEFAULT_DATA_PATH):
        self._df = pd.read_csv(data_path, encoding="utf-8-sig")
        self._df["cutoff_score"] = pd.to_numeric(self._df["cutoff_score"], errors="coerce")
        self._df = self._df.dropna(subset=["cutoff_score"])

    @property
    def universities(self) -> list[str]:
        return sorted(self._df["university_name"].dropna().unique().tolist())

    @property
    def combos(self) -> list[str]:
        return sorted(self._df["score_combo"].dropna().unique().tolist())

    def recommend(
        self,
        student_score: float,
        score_combo: str,
        top_n: int = 10,
        year: int | None = None,
    ) -> RecommendationResult:
        result = RecommendationResult(student_score=student_score, score_combo=score_combo)

        df = self._df[self._df["score_combo"] == score_combo.upper()].copy()
        if df.empty:
            logger.warning("No data for combo %s", score_combo)
            return result

        # Use most recent year per (university, major, combo) if year not specified
        if year is not None:
            df = df[df["year"] == year]
        else:
            df = df.loc[
                df.groupby(["university_code", "major_code", "score_combo"])["year"].idxmax()
            ]

        df = df[df["cutoff_score"] >= (student_score - SAFETY_MARGIN)]
        df = df[df["cutoff_score"] <= (student_score + REACH_MARGIN)]
        df = df.sort_values("cutoff_score", ascending=False).head(top_n * 3)

        for _, row in df.iterrows():
            gap = round(student_score - row["cutoff_score"], 2)
            trend = _score_trend(
                self._df[
                    (self._df["university_code"] == row["university_code"])
                    & (self._df["major_code"] == row["major_code"])
                    & (self._df["score_combo"] == row["score_combo"])
                ]
            )
            rec = Recommendation(
                university_name=row["university_name"],
                university_code=row.get("university_code", ""),
                major_name=row["major_name"],
                major_code=row.get("major_code", ""),
                cutoff_score=row["cutoff_score"],
                year=int(row["year"]),
                score_combo=row["score_combo"],
                gap=gap,
                reason=_build_reason(row, gap),
                trend=trend,
            )
            if gap < 0:
                result.reach.append(rec)
            elif gap <= 2:
                result.target.append(rec)
            else:
                result.safety.append(rec)

        result.reach = result.reach[:top_n]
        result.target = result.target[:top_n]
        result.safety = result.safety[:top_n]
        return result
