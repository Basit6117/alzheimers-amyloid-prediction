"""Inspect the saved amyloid SVM artifact without modifying it."""

from __future__ import annotations

import platform
import sys
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.pipeline import Pipeline

try:
    import pandas as pd
except ImportError:
    pd = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# The repository currently stores the provided artifact in ``model/``.
MODEL_PATH = PROJECT_ROOT / "model" / "amyloid_svm_champion_9306.joblib"


def main() -> None:
    model = joblib.load(MODEL_PATH)

    print(f"model_path: {MODEL_PATH}")
    print(f"object_type: {type(model).__module__}.{type(model).__qualname__}")
    if isinstance(model, Pipeline):
        print("pipeline_steps:")
        for name, step in model.steps:
            print(f"  - {name}: {type(step).__module__}.{type(step).__qualname__}")
    else:
        print("pipeline_steps: not a Pipeline")

    for attribute in ("feature_names_in_", "n_features_in_", "classes_"):
        if hasattr(model, attribute):
            value = getattr(model, attribute)
            print(f"{attribute}: {value.tolist() if hasattr(value, 'tolist') else value}")
        else:
            print(f"{attribute}: unavailable")
    print(f"has_predict_proba: {callable(getattr(model, 'predict_proba', None))}")

    print("versions:")
    print(f"  python: {platform.python_version()} ({sys.executable})")
    print(f"  scikit-learn: {sklearn.__version__}")
    print(f"  numpy: {np.__version__}")
    print(f"  pandas: {pd.__version__ if pd is not None else 'not installed'}")
    print(f"  joblib: {joblib.__version__}")

    if not hasattr(model, "n_features_in_"):
        raise RuntimeError("Cannot construct a dummy input: n_features_in_ is unavailable.")
    feature_count = model.n_features_in_
    columns = getattr(model, "feature_names_in_", None)
    dummy = (
        pd.DataFrame([[0.0] * feature_count], columns=columns)
        if columns is not None and pd is not None
        else np.zeros((1, feature_count))
    )
    print(f"dummy_predict: {model.predict(dummy).tolist()}")
    if callable(getattr(model, "predict_proba", None)):
        print(f"dummy_predict_proba: {model.predict_proba(dummy).tolist()}")


if __name__ == "__main__":
    main()
