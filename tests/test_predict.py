"""Regression checks for raw-input feature engineering and prediction."""

from app.predict import build_model_input, load_model, predict_probability


RAW_VALUES = {
    "pT217_F": 0.386,
    "AB42_AB40_F": 0.0973,
    "GFAP_Q": 175.1418,
    "APOE4": 0,
    "AGE": 73.0,
    "SEX": 1,
}


def test_raw_values_are_engineered_in_saved_model_order() -> None:
    frame = build_model_input(RAW_VALUES)

    assert list(frame.columns) == [
        "pT217_F",
        "GFAP_to_AB_ratio",
        "pT217_to_AB_ratio",
        "AB42_AB40_F",
        "AGE",
        "APOE4",
        "SEX",
    ]
    assert abs(frame.loc[0, "GFAP_to_AB_ratio"] - 1800.0) < 1e-10
    assert abs(frame.loc[0, "pT217_to_AB_ratio"] - (0.386 / (0.0973 + 1e-6))) < 1e-12


def test_real_model_accepts_raw_values() -> None:
    probability = predict_probability(load_model(), RAW_VALUES)

    assert 0.0 <= probability <= 1.0
