"""
ML service: the only module that touches the trained scikit-learn model
directly. Everything else (business thresholds, DB writes) lives in
scoring_service.py — this module's job is purely "given applicant + loan
data, return a probability of default and the top contributing factors."

The model is loaded once, at import time (i.e. once per process, not per
request) — the same pattern used for get_settings(), for the same reason:
loading a model file and building a SHAP explainer are both too expensive
to redo on every API call.
"""
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap

_ML_DIR = Path(__file__).resolve().parent.parent / "ml"
_MODEL_PATH = _ML_DIR / "model.pkl"
_METADATA_PATH = _ML_DIR / "model_metadata.json"


class ModelNotAvailableError(Exception):
    """Raised when model.pkl / model_metadata.json haven't been generated yet."""
    pass


def _load_model_and_metadata() -> tuple[Any, dict]:
    if not _MODEL_PATH.exists() or not _METADATA_PATH.exists():
        raise ModelNotAvailableError(
            f"Model artifacts not found at {_ML_DIR}. Run `python train.py` from the "
            "ml-training/ directory first — see ml-training/train.py for instructions."
        )
    model = joblib.load(_MODEL_PATH)
    metadata = json.loads(_METADATA_PATH.read_text())
    return model, metadata


try:
    _model, _metadata = _load_model_and_metadata()
    _feature_columns: list[str] = _metadata["feature_columns"]
    _model_version: str = _metadata["model_version"]
    # TreeExplainer is built once here (not per-request) since constructing it
    # from the trained trees has non-trivial one-time cost.
    _explainer = shap.TreeExplainer(_model)
    MODEL_LOAD_ERROR: str | None = None
except ModelNotAvailableError as exc:
    # Deferred failure: importing this module doesn't crash the whole app
    # (e.g. during a docs-only browse), but any actual prediction attempt
    # will raise a clear, actionable error instead of a confusing one.
    _model = _metadata = _feature_columns = _model_version = _explainer = None
    MODEL_LOAD_ERROR = str(exc)


def build_feature_vector(applicant_data: dict, loan_data: dict) -> pd.DataFrame:
    """
    Builds a single-row feature DataFrame with columns in the exact order
    the model was trained on (see ml-training/train.py FEATURE_COLUMNS).

    NOTE ON TRAIN/SERVING PARITY: this feature-building logic intentionally
    mirrors ml-training/train.py's build_feature_matrix(). At this project's
    scale they're kept as two clearly-commented, matching implementations
    rather than a shared package — a "feature store" (see the original
    architecture doc) is how you'd eliminate this duplication at real scale.
    """
    annual_income = float(applicant_data["annual_income"])
    existing_debt = float(applicant_data["existing_debt"])
    loan_amount = float(loan_data["loan_amount"])

    row = {
        "annual_income": annual_income,
        "existing_debt": existing_debt,
        "credit_history_years": float(applicant_data["credit_history_years"]),
        "loan_amount": loan_amount,
        "loan_tenure_months": float(loan_data["loan_tenure_months"]),
        "debt_to_income": existing_debt / annual_income if annual_income > 0 else 0.0,
        "loan_to_income": loan_amount / annual_income if annual_income > 0 else 0.0,
    }

    employment_status = applicant_data["employment_status"]
    for status in ("employed", "self_employed", "student", "unemployed"):
        row[f"employment_{status}"] = 1.0 if employment_status == status else 0.0

    loan_purpose = loan_data["loan_purpose"]
    for purpose in ("personal", "auto", "education", "business", "home"):
        row[f"purpose_{purpose}"] = 1.0 if loan_purpose == purpose else 0.0

    return pd.DataFrame([row], columns=_feature_columns)


def predict_default_probability(features: pd.DataFrame) -> float:
    if _model is None:
        raise ModelNotAvailableError(MODEL_LOAD_ERROR or "Model is not loaded.")
    probability = _model.predict_proba(features)[0, 1]
    return float(probability)


def top_contributing_factors(features: pd.DataFrame, top_n: int = 3) -> list[dict]:
    """
    Returns the top_n features with the largest absolute SHAP contribution
    to this specific prediction, e.g.:
        [{"feature": "loan_to_income", "impact": 0.42, "direction": "increases_risk"}, ...]
    """
    if _explainer is None:
        raise ModelNotAvailableError(MODEL_LOAD_ERROR or "Model is not loaded.")

    shap_values = _explainer.shap_values(features)
    # GradientBoostingClassifier + TreeExplainer returns a single array for
    # the positive class in binary classification (not a per-class list).
    row_values = np.asarray(shap_values)[0]

    contributions = list(zip(_feature_columns, row_values))
    contributions.sort(key=lambda item: abs(item[1]), reverse=True)

    return [
        {
            "feature": feature_name,
            "impact": round(float(impact), 4),
            "direction": "increases_risk" if impact > 0 else "decreases_risk",
        }
        for feature_name, impact in contributions[:top_n]
    ]


def get_model_version() -> str:
    if _model_version is None:
        raise ModelNotAvailableError(MODEL_LOAD_ERROR or "Model is not loaded.")
    return _model_version