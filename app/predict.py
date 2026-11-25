"""Isolated helpers for loading and running the prediction model."""

from collections.abc import Mapping
import logging
from pathlib import Path
from typing import Any
import warnings

import joblib
import pandas as pd
import sklearn
from sklearn.exceptions import InconsistentVersionWarning

from app.config import (
    ELEVATED_RISK_THRESHOLD,
    FEATURE_ENGINEERING_EPSILON,
    FEATURE_ORDER,
    FEATURE_REFERENCE_VALUES,
    MODEL_PATH,
    MODERATE_RISK_THRESHOLD,
    REQUIRED_SKLEARN_VERSION,
)


# Uvicorn configures this logger at startup, so the required version is visible
# in normal server logs without altering global logging configuration.
logger = logging.getLogger("uvicorn.error")


def load_model(model_path: Path = MODEL_PATH) -> Any:
    """Load the immutable saved model artifact exactly once at app startup."""
    installed_version = sklearn.__version__
    logger.info("scikit-learn version: %s", installed_version)
    if installed_version != REQUIRED_SKLEARN_VERSION:
        raise RuntimeError(
            "Model requires scikit-learn "
            f"{REQUIRED_SKLEARN_VERSION}, but {installed_version} is installed. "
            "Activate the project .venv and install requirements.txt."
        )

    with warnings.catch_warnings():
        warnings.simplefilter("error", InconsistentVersionWarning)
        return joblib.load(model_path)


def engineer_model_features(raw_values: Mapping[str, float]) -> dict[str, float]:
    """Recreate the two ratio features engineered before model training."""
    required_raw_features = ("pT217_F", "AB42_AB40_F", "GFAP_Q", "APOE4", "AGE", "SEX")
    missing = [feature for feature in required_raw_features if feature not in raw_values]
    if missing:
        raise ValueError(f"Missing required raw features: {', '.join(missing)}")

    engineered = dict(raw_values)
    denominator = float(engineered["AB42_AB40_F"]) + FEATURE_ENGINEERING_EPSILON
    engineered["GFAP_to_AB_ratio"] = float(engineered["GFAP_Q"]) / denominator
    engineered["pT217_to_AB_ratio"] = float(engineered["pT217_F"]) / denominator
    return engineered


def build_model_input(raw_values: Mapping[str, float]) -> pd.DataFrame:
    """Engineer and order model columns independently of incoming JSON order."""
    feature_values = engineer_model_features(raw_values)

    return pd.DataFrame(
        [[feature_values[feature] for feature in FEATURE_ORDER]],
        columns=FEATURE_ORDER,
    )


def predict_probability(model: Any, feature_values: Mapping[str, float]) -> float:
    """Return the probability of class 1 (Amyloid Positive)."""
    class_labels = list(model.classes_)
    class_one_index = class_labels.index(1)
    probabilities = model.predict_proba(build_model_input(feature_values))
    return float(probabilities[0][class_one_index])


def risk_category(probability: float) -> str:
    """Return the UI presentation category for a class-1 probability."""
    if probability < MODERATE_RISK_THRESHOLD:
        return "Low"
    if probability < ELEVATED_RISK_THRESHOLD:
        return "Moderate"
    return "Elevated"


def top_factors(
    model: Any, feature_values: Mapping[str, float], limit: int = 3
) -> list[dict[str, float | str]]:
    """Rank local SVM sensitivities against observed-range midpoint references.

    RBF SVC has no native per-feature coefficients. For each feature, this
    compares the current decision score with the score after substituting that
    field's observed-training-range midpoint. Contributions are signed score
    changes; ranking uses their absolute magnitude.
    """
    engineered_values = engineer_model_features(feature_values)
    current_score = float(model.decision_function(build_model_input(feature_values))[0])
    factors: list[dict[str, float | str]] = []

    for feature in FEATURE_ORDER:
        reference_values = dict(engineered_values)
        reference_values[feature] = FEATURE_REFERENCE_VALUES[feature]
        reference_score = float(
            model.decision_function(
                pd.DataFrame(
                    [[reference_values[item] for item in FEATURE_ORDER]],
                    columns=FEATURE_ORDER,
                )
            )[0]
        )
        factors.append(
            {"feature": feature, "contribution": current_score - reference_score}
        )

    return sorted(factors, key=lambda factor: abs(float(factor["contribution"])), reverse=True)[:limit]
