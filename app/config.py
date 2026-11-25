"""Shared configuration for isolated prediction and RAG paths."""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "model" / "amyloid_svm_champion_9306.joblib"
DATA_DIR = PROJECT_ROOT / "data"
PDF_DIR = DATA_DIR / "pdfs"
DATABASE_PATH = DATA_DIR / "app.db"
MODEL_VERSION = "amyloid_svm_champion_9306"
REQUIRED_SKLEARN_VERSION = "1.6.1"


def _load_environment_file() -> None:
    """Load project-local key/value settings without logging secret values."""
    environment_file = PROJECT_ROOT / ".env"
    if not environment_file.exists():
        return
    for line in environment_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


_load_environment_file()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.7-flash")
GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "45"))
GEMINI_RETRY_ATTEMPTS = int(os.getenv("GEMINI_RETRY_ATTEMPTS", "2"))
RAG_TOP_K = 4
RAG_MAX_DISTANCE = 1.2

# This order is defined by the loaded artifact's feature_names_in_.
FEATURE_ORDER = (
    "pT217_F",
    "GFAP_to_AB_ratio",
    "pT217_to_AB_ratio",
    "AB42_AB40_F",
    "AGE",
    "APOE4",
    "SEX",
)

# The only values accepted from a person using the dashboard. The remaining
# two model columns are deterministically engineered in ``app.predict``.
RAW_INPUT_ORDER = (
    "pT217_F",
    "AB42_AB40_F",
    "GFAP_Q",
    "APOE4",
    "AGE",
    "SEX",
)
FEATURE_ENGINEERING_EPSILON = 1e-6

# Presentation bands only. They do not control the SVM class decision.
MODERATE_RISK_THRESHOLD = 1 / 3
ELEVATED_RISK_THRESHOLD = 2 / 3

# Observed bounds of notebooks/data/processed/blood_only.csv. They support
# deterministic local sensitivity calculations, not clinical reference ranges.
FEATURE_REFERENCE_VALUES = {
    "pT217_F": (0.030 + 1.938) / 2,
    "GFAP_to_AB_ratio": (301.322009 + 5689.488910) / 2,
    "pT217_to_AB_ratio": (0.306289 + 15.387183) / 2,
    "AB42_AB40_F": (0.0615 + 0.1323) / 2,
    "AGE": (51.014374 + 91.137577) / 2,
    "APOE4": 0.5,
    "SEX": 0.5,
}
