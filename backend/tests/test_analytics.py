def _register(client, email, role="applicant"):
    response = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Test User", "email": email, "password": "StrongPass123", "role": role},
    )
    return response.json()["access_token"]


BASE_APPLICATION = {
    "full_name": "Jordan Rivera",
    "date_of_birth": "1990-01-01",
    "employment_status": "employed",
    "credit_history_years": 8,
    "loan_purpose": "auto",
    "loan_tenure_months": 36,
}


def _submit(client, headers, annual_income, existing_debt, loan_amount):
    payload = {
        **BASE_APPLICATION,
        "annual_income": annual_income,
        "existing_debt": existing_debt,
        "loan_amount": loan_amount,
    }
    response = client.post("/api/v1/loans", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_summary_requires_authentication(client):
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 401


def test_applicant_cannot_access_summary(client):
    token = _register(client, "jordan@example.com")
    response = client.get(
        "/api/v1/analytics/summary", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_staff_can_access_summary(client):
    token = _register(client, "alex@bank.com", role="staff")
    response = client.get(
        "/api/v1/analytics/summary", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


def test_admin_can_access_summary(client):
    token = _register(client, "admin@bank.com", role="admin")
    response = client.get(
        "/api/v1/analytics/summary", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


def test_summary_on_empty_database_returns_zeroed_shape(client):
    token = _register(client, "alex@bank.com", role="staff")
    response = client.get(
        "/api/v1/analytics/summary", headers={"Authorization": f"Bearer {token}"}
    )
    body = response.json()
    assert body["total_applications"] == 0
    assert body["status_counts"] == []
    assert body["risk_category_counts"] == []
    assert body["average_loan_amount"] is None
    assert body["average_risk_score"] is None
    assert body["approved_count"] == 0
    assert body["rejected_count"] == 0
    assert body["approval_rate"] is None
    assert body["applications_trend"] == []


def test_summary_reflects_submitted_applications(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # Low risk (high income, low debt/loan) and high risk (low income, high debt/loan)
    _submit(client, applicant_headers, annual_income=150000, existing_debt=2000, loan_amount=5000)
    _submit(client, applicant_headers, annual_income=20000, existing_debt=15000, loan_amount=18000)

    response = client.get("/api/v1/analytics/summary", headers=staff_headers)
    body = response.json()

    assert body["total_applications"] == 2
    assert sum(s["count"] for s in body["status_counts"]) == 2
    assert sum(r["count"] for r in body["risk_category_counts"]) == 2
    assert body["average_loan_amount"] == 11500.0
    assert body["average_risk_score"] is not None
    assert len(body["applications_trend"]) == 1  # both submitted today -> one date bucket
    assert body["applications_trend"][0]["count"] == 2


def test_summary_approval_rate_reflects_decisions(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    loan_a = _submit(client, applicant_headers, annual_income=150000, existing_debt=2000, loan_amount=5000)
    loan_b = _submit(client, applicant_headers, annual_income=150000, existing_debt=2000, loan_amount=5000)

    client.patch(
        f"/api/v1/loans/{loan_a['id']}/decision", json={"decision": "approved"}, headers=staff_headers
    )
    client.patch(
        f"/api/v1/loans/{loan_b['id']}/decision", json={"decision": "rejected"}, headers=staff_headers
    )

    response = client.get("/api/v1/analytics/summary", headers=staff_headers)
    body = response.json()

    assert body["approved_count"] == 1
    assert body["rejected_count"] == 1
    assert body["approval_rate"] == 0.5