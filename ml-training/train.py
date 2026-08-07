"""
Offline training script for the credit risk model.

WHY SYNTHETIC DATA: this project has no access to a real historical loan
book (no real applicants have defaulted on real loans yet — this is a new
product). Rather than hand-coding an if/else scoring formula and calling it
"AI", this script generates a synthetic-but-realistic dataset from known
credit-risk relationships (higher debt-to-income => higher default risk,
longer credit history => lower risk, etc.), adds noise, and then trains a
real scikit-learn classifier on it. This is a legitimate, common way to
bootstrap a scoring model before real repayment outcomes exist — the model
learns the *shape* of the relationships from data, it isn't just replaying
a formula. When real repayment outcomes accumulate in production, this
script is where you'd swap in the real dataset and retrain.

WHAT THIS PRODUCES:
  backend/app/ml/model.pkl           - the trained GradientBoostingClassifier
  backend/app/ml/model_metadata.json - feature order + model version, so the
                                        backend can build an identical feature
                                        vector at inference time

Run with:
    cd ml-training
    pip install -r requirements.txt
    python train.py
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

RANDOM_SEED = 42
N_SAMPLES = 8000
MODEL_VERSION = "gbc_v1_2026"

EMPLOYMENT_STATUSES = ["employed", "self_employed", "unemployed", "student"]
LOAN_PURPOSES = ["personal", "auto", "education", "business", "home"]

# The exact, ordered list of columns the model is trained on. The backend's
# ml_service.py must build feature vectors with these same columns, in this
# same order — this file is the single source of truth for that contract.
FEATURE_COLUMNS = [
    "annual_income",
    "existing_debt",
    "credit_history_years",
    "loan_amount",
    "loan_tenure_months",
    "debt_to_income",
    "loan_to_income",
    "employment_employed",
    "employment_self_employed",
    "employment_student",
    "employment_unemployed",
    "purpose_personal",
    "purpose_auto",
    "purpose_education",
    "purpose_business",
    "purpose_home",
]


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-x))


def generate_synthetic_dataset(n_samples: int, rng: np.random.Generator) -> pd.DataFrame:
    annual_income = rng.lognormal(mean=10.8, sigma=0.45, size=n_samples).clip(12_000, 400_000)
    credit_history_years = rng.integers(0, 30, size=n_samples)
    employment_status = rng.choice(EMPLOYMENT_STATUSES, size=n_samples, p=[0.62, 0.18, 0.08, 0.12])
    loan_purpose = rng.choice(LOAN_PURPOSES, size=n_samples, p=[0.35, 0.2, 0.15, 0.15, 0.15])

    # Existing debt and loan amount are drawn relative to income, so the
    # dataset naturally covers a realistic range of debt/loan-to-income
    # ratios rather than being independent of income entirely.
    existing_debt = (annual_income * rng.uniform(0, 0.6, size=n_samples)).round(2)
    loan_amount = (annual_income * rng.uniform(0.05, 1.5, size=n_samples)).round(2)
    loan_tenure_months = rng.choice([12, 24, 36, 48, 60, 84, 120, 180, 240, 360], size=n_samples)

    df = pd.DataFrame({
        "annual_income": annual_income,
        "existing_debt": existing_debt,
        "credit_history_years": credit_history_years,
        "loan_amount": loan_amount,
        "loan_tenure_months": loan_tenure_months,
        "employment_status": employment_status,
        "loan_purpose": loan_purpose,
    })

    df["debt_to_income"] = df["existing_debt"] / df["annual_income"]
    df["loan_to_income"] = df["loan_amount"] / df["annual_income"]

    employment_risk = df["employment_status"].map({
        "employed": -0.5,
        "self_employed": -0.1,
        "student": 0.5,
        "unemployed": 1.3,
    })

    # The "true" (unobserved in real life) risk relationship used to generate
    # labels. Coefficients are illustrative, not fitted to any real data.
    risk_logit = (
        2.6 * df["debt_to_income"]
        + 1.7 * df["loan_to_income"]
        - 0.07 * df["credit_history_years"]
        + employment_risk
        + 0.0015 * df["loan_tenure_months"]
        - 2.65  # baseline offset so the overall default rate is realistic (~15-20%)
    )
    noise = rng.normal(0, 0.6, size=n_samples)
    probability_of_default = _sigmoid(risk_logit + noise)
    df["defaulted"] = rng.binomial(1, probability_of_default)

    return df


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    employment_dummies = pd.get_dummies(df["employment_status"], prefix="employment")
    purpose_dummies = pd.get_dummies(df["loan_purpose"], prefix="purpose")

    for status in EMPLOYMENT_STATUSES:
        col = f"employment_{status}"
        if col not in employment_dummies:
            employment_dummies[col] = 0

    for purpose in LOAN_PURPOSES:
        col = f"purpose_{purpose}"
        if col not in purpose_dummies:
            purpose_dummies[col] = 0

    features = pd.concat(
        [df[["annual_income", "existing_debt", "credit_history_years",
             "loan_amount", "loan_tenure_months", "debt_to_income", "loan_to_income"]],
         employment_dummies, purpose_dummies],
        axis=1,
    )
    return features[FEATURE_COLUMNS].astype(float)


def main() -> None:
    rng = np.random.default_rng(RANDOM_SEED)
    dataset = generate_synthetic_dataset(N_SAMPLES, rng)

    X = build_feature_matrix(dataset)
    y = dataset["defaulted"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )

    model = GradientBoostingClassifier(
        n_estimators=150,
        max_depth=3,
        learning_rate=0.08,
        random_state=RANDOM_SEED,
    )
    model.fit(X_train, y_train)

    test_probabilities = model.predict_proba(X_test)[:, 1]
    test_predictions = (test_probabilities >= 0.5).astype(int)
    auc = roc_auc_score(y_test, test_probabilities)

    print(f"Training complete. Default rate in dataset: {y.mean():.1%}")
    print(f"Test AUC-ROC: {auc:.4f}")
    print(classification_report(y_test, test_predictions, target_names=["No default", "Default"]))

    backend_ml_dir = Path(__file__).resolve().parent.parent / "backend" / "app" / "ml"
    backend_ml_dir.mkdir(parents=True, exist_ok=True)

    model_path = backend_ml_dir / "model.pkl"
    joblib.dump(model, model_path)

    metadata = {
        "model_version": MODEL_VERSION,
        "feature_columns": FEATURE_COLUMNS,
        "employment_statuses": EMPLOYMENT_STATUSES,
        "loan_purposes": LOAN_PURPOSES,
        "test_auc_roc": round(float(auc), 4),
        "training_samples": int(len(X_train)),
    }
    metadata_path = backend_ml_dir / "model_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))

    print(f"\nSaved model to: {model_path}")
    print(f"Saved metadata to: {metadata_path}")


if __name__ == "__main__":
    main()