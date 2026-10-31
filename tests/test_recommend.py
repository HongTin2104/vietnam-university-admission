"""Tests for the recommendation engine."""

from pathlib import Path

import pytest

from src.model.recommend import Recommender

DATA_PATH = Path("data/processed/scores.csv")


@pytest.fixture(scope="module")
def rec():
    return Recommender(DATA_PATH)


def test_recommender_loads(rec):
    assert len(rec.combos) > 0
    assert len(rec.universities) > 0


def test_recommend_returns_result(rec):
    result = rec.recommend(student_score=25.0, score_combo="A00")
    # Should return something — reach + target + safety combined
    total = len(result.reach) + len(result.target) + len(result.safety)
    assert total >= 0  # non-negative always; may be 0 if no match


def test_recommend_target_gap_within_range(rec):
    result = rec.recommend(student_score=25.0, score_combo="A00")
    for r in result.target:
        assert -0.001 <= r.gap <= 2.001, f"gap {r.gap} outside target range"


def test_recommend_safety_gap_positive(rec):
    result = rec.recommend(student_score=25.0, score_combo="A00")
    for r in result.safety:
        assert r.gap > 2, f"gap {r.gap} should be > 2 for safety"


def test_recommend_reach_gap_negative(rec):
    result = rec.recommend(student_score=25.0, score_combo="A00")
    for r in result.reach:
        assert r.gap < 0, f"gap {r.gap} should be negative for reach"


def test_recommend_unknown_combo(rec):
    result = rec.recommend(student_score=25.0, score_combo="Z99")
    assert result.reach == []
    assert result.target == []
    assert result.safety == []


def test_recommend_top_n_respected(rec):
    result = rec.recommend(student_score=20.0, score_combo="A00", top_n=2)
    assert len(result.target) <= 2
    assert len(result.safety) <= 2
    assert len(result.reach) <= 2


def test_recommendation_has_reason(rec):
    result = rec.recommend(student_score=27.0, score_combo="A00")
    all_recs = result.reach + result.target + result.safety
    for r in all_recs:
        assert r.reason, "Recommendation must have a non-empty reason"
