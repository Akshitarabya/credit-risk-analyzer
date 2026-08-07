def _register(client, email, role="applicant"):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test User",
            "email": email,
            "password": "StrongPass123",
            "role": role,
        },
    )
    return response.json()["access_token"]


LOW_RISK_APPLICATION = {
    "full_name": "Jordan Rivera",
    "date_of_birth": "1980-04-12",
    "annual_income": 150000,
    "employment_status": "employed",
    "existing_debt": 2000,
    "credit_history_years": 20,
    "loan_amount": 5000,
    "loan_purpose": "auto",
    "loan_tenure_months": 24,
}

HIGH_RISK_APPLICATION = {
    "full_name": "Taylor Kim",
    "date_of_birth": "2000-01-01",
    "annual_income": 20000,
    "employment_status": "unemployed",
    "existing_debt": 15000,
    "credit_history_years": 0,
    "loan_amount": 18000,
    "loan_purpose": "personal",
    "loan_tenure_months": 60,
}


def test_submission_response_includes_prediction_fields(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/v1/loans", json=LOW_RISK_APPLICATION, headers=headers)
    assert response.status_code == 201
    body = response.json()

    assert isinstance(body["risk_score"], int)
    assert 0 <= body["risk_score"] <= 100
    assert body["risk_category"] in ("low", "medium", "high")
    assert body["recommendation"] in ("approved", "review", "reject")
    assert body["prediction_timestamp"] is not None
    assert body["model_version"]
    assert isinstance(body["top_risk_factors"], list)
    assert len(body["top_risk_factors"]) > 0


def test_low_risk_profile_scores_low_and_is_approved(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/v1/loans", json=LOW_RISK_APPLICATION, headers=headers)
    body = response.json()

    assert body["risk_category"] == "low"
    assert body["recommendation"] == "approved"
    assert body["risk_score"] < 30


def test_high_risk_profile_scores_high_and_is_rejected(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/v1/loans", json=HIGH_RISK_APPLICATION, headers=headers)
    body = response.json()

    assert body["risk_category"] == "high"
    assert body["recommendation"] == "reject"
    assert body["risk_score"] >= 70


def test_oversized_loan_forces_reject_regardless_of_model_score(client):
    """
    The sanity-check rule layer: a loan amount far beyond the applicant's
    income must be rejected even if other factors look otherwise fine.
    """
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {**LOW_RISK_APPLICATION, "loan_amount": 150000 * 6}  # 6x annual income
    response = client.post("/api/v1/loans", json=payload, headers=headers)
    body = response.json()

    assert body["risk_category"] == "high"
    assert body["recommendation"] == "reject"


def test_top_risk_factors_have_expected_shape(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/v1/loans", json=LOW_RISK_APPLICATION, headers=headers)
    factors = response.json()["top_risk_factors"]

    for factor in factors:
        assert "feature" in factor
        assert "impact" in factor
        assert factor["direction"] in ("increases_risk", "decreases_risk")


def test_dedicated_prediction_endpoint_returns_same_data(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post("/api/v1/loans", json=LOW_RISK_APPLICATION, headers=headers).json()

    response = client.get(f"/api/v1/loans/{created['id']}/prediction", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["loan_application_id"] == created["id"]
    assert body["risk_score"] == created["risk_score"]
    assert body["risk_category"] == created["risk_category"]
    assert body["recommendation"] == created["recommendation"]


def test_prediction_endpoint_requires_auth(client):
    response = client.get(
        "/api/v1/loans/00000000-0000-0000-0000-000000000000/prediction"
    )
    assert response.status_code == 401


def test_other_applicant_cannot_view_someone_elses_prediction(client):
    token_a = _register(client, "jordan@example.com")
    token_b = _register(client, "taylor@example.com")

    created = client.post(
        "/api/v1/loans", json=LOW_RISK_APPLICATION, headers={"Authorization": f"Bearer {token_a}"}
    ).json()

    response = client.get(
        f"/api/v1/loans/{created['id']}/prediction",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 403


def test_staff_can_view_any_applicants_prediction(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")

    created = client.post(
        "/api/v1/loans",
        json=LOW_RISK_APPLICATION,
        headers={"Authorization": f"Bearer {applicant_token}"},
    ).json()

    response = client.get(
        f"/api/v1/loans/{created['id']}/prediction",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 200


def test_loan_detail_view_includes_prediction_fields(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post("/api/v1/loans", json=LOW_RISK_APPLICATION, headers=headers).json()
    response = client.get(f"/api/v1/loans/{created['id']}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["risk_score"] == created["risk_score"]
    assert body["recommendation"] == created["recommendation"]