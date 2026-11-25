"""Tests for prediction presentation helpers."""

from app.predict import load_model, risk_category, top_factors


def test_risk_category_boundaries() -> None:
    assert risk_category(0.0) == "Low"
    assert risk_category(1 / 3) == "Moderate"
    assert risk_category(2 / 3) == "Elevated"


def test_top_factors_returns_ranked_local_sensitivities() -> None:
    values = {
        "pT217_F": 0.386,
        "AB42_AB40_F": 0.0973,
        "GFAP_Q": 175.1418,
        "APOE4": 0,
        "AGE": 73.0,
        "SEX": 1,
    }

    factors = top_factors(load_model(), values)

    assert len(factors) == 3
    assert {factor["feature"] for factor in factors}.issubset({
        "pT217_F", "GFAP_to_AB_ratio", "pT217_to_AB_ratio", "AB42_AB40_F", "AGE", "APOE4", "SEX"
    })
    assert all(isinstance(factor["contribution"], float) for factor in factors)
    assert [abs(float(factor["contribution"])) for factor in factors] == sorted(
        (abs(float(factor["contribution"])) for factor in factors), reverse=True
    )
