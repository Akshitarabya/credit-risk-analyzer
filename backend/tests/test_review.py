"""
Tests for the Module 4 staff review workflow:
  GET   /loans/pending
  PATCH /loans/{id}/decision
  PATCH /loans/{id}/notes
"""


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


VALID_APPLICATION = {
    "full_name": "Jordan Rivera",
    "date_of_birth": "1995-04-12",
    "annual_income": 68000,
    "employment_status": "employed",
    "existing_debt": 5000,
    "credit_history_years": 6,
    "loan_amount": 15000,
    "loan_purpose": "auto",
    "loan_tenure_months": 48,
}


def _submit_application(client, applicant_headers, **overrides):
    payload = {**VALID_APPLICATION, **overrides}
    response = client.post("/api/v1/loans", json=payload, headers=applicant_headers)
    assert response.status_code == 201
    return response.json()


# ---------------------------------------------------------------------------
# GET /loans/pending
# ---------------------------------------------------------------------------


def test_pending_requires_authentication(client):
    response = client.get("/api/v1/loans/pending")
    assert response.status_code == 401


def test_applicant_cannot_access_pending_queue(client):
    applicant_token = _register(client, "jordan@example.com")
    response = client.get(
        "/api/v1/loans/pending", headers={"Authorization": f"Bearer {applicant_token}"}
    )
    assert response.status_code == 403


def test_staff_can_list_pending_applications(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    _submit_application(client, applicant_headers)

    response = client.get("/api/v1/loans/pending", headers=staff_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_pending_queue_only_returns_scored_and_manual_review_applications(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # One application left as SCORED (never decided) — should appear.
    still_pending = _submit_application(client, applicant_headers)

    # A second application, approved — should NOT appear once decided.
    decided = _submit_application(client, applicant_headers, loan_amount=5000)
    client.patch(
        f"/api/v1/loans/{decided['id']}/decision",
        json={"decision": "approved"},
        headers=staff_headers,
    )

    response = client.get("/api/v1/loans/pending", headers=staff_headers)
    assert response.status_code == 200
    ids_in_queue = {application["id"] for application in response.json()}
    assert still_pending["id"] in ids_in_queue
    assert decided["id"] not in ids_in_queue


def test_pending_queue_includes_manual_review_applications(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)
    client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "manual_review"},
        headers=staff_headers,
    )

    response = client.get("/api/v1/loans/pending", headers=staff_headers)
    assert response.status_code == 200
    ids_in_queue = {application["id"] for application in response.json()}
    assert created["id"] in ids_in_queue


# ---------------------------------------------------------------------------
# PATCH /loans/{id}/decision
# ---------------------------------------------------------------------------


def test_decision_requires_authentication(client):
    response = client.patch(
        "/api/v1/loans/00000000-0000-0000-0000-000000000000/decision",
        json={"decision": "approved"},
    )
    assert response.status_code == 401


def test_applicant_cannot_submit_decision(client):
    applicant_token = _register(client, "jordan@example.com")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    created = _submit_application(client, applicant_headers)

    response = client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "approved"},
        headers=applicant_headers,
    )
    assert response.status_code == 403


def test_staff_can_approve_a_scored_application(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)
    assert created["status"] == "scored"

    response = client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "approved"},
        headers=staff_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["final_decision"] == "approved"


def test_staff_can_reject_a_scored_application(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)

    response = client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "rejected"},
        headers=staff_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "rejected"
    assert body["final_decision"] == "rejected"


def test_valid_transition_scored_to_manual_review_to_approved(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)

    to_review = client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "manual_review"},
        headers=staff_headers,
    )
    assert to_review.status_code == 200
    assert to_review.json()["status"] == "manual_review"
    assert to_review.json()["final_decision"] is None

    to_approved = client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "approved"},
        headers=staff_headers,
    )
    assert to_approved.status_code == 200
    assert to_approved.json()["status"] == "approved"
    assert to_approved.json()["final_decision"] == "approved"


def test_invalid_transition_manual_review_to_manual_review_returns_409(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)
    client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "manual_review"},
        headers=staff_headers,
    )

    response = client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "manual_review"},
        headers=staff_headers,
    )
    assert response.status_code == 409


def test_double_approval_returns_409(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)
    first = client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "approved"},
        headers=staff_headers,
    )
    assert first.status_code == 200

    second = client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "approved"},
        headers=staff_headers,
    )
    assert second.status_code == 409


def test_cannot_change_decision_after_it_is_final(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)
    client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "approved"},
        headers=staff_headers,
    )

    response = client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "rejected"},
        headers=staff_headers,
    )
    assert response.status_code == 409


def test_decision_on_nonexistent_application_returns_404(client):
    staff_token = _register(client, "alex@bank.com", role="staff")
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    response = client.patch(
        "/api/v1/loans/00000000-0000-0000-0000-000000000000/decision",
        json={"decision": "approved"},
        headers=staff_headers,
    )
    assert response.status_code == 404


def test_decision_with_invalid_action_value_returns_422(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)

    response = client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "not_a_real_action"},
        headers=staff_headers,
    )
    assert response.status_code == 422


def test_decision_persists_reviewer_identity_and_timestamp(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)
    response = client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "approved"},
        headers=staff_headers,
    )
    body = response.json()

    assert body["reviewer_id"] is not None
    assert body["reviewer_name"] == "Test User"
    assert body["reviewed_at"] is not None
    assert body["final_decision"] == "approved"

    # Persistence check: fetching independently shows the same recorded data.
    fetched = client.get(f"/api/v1/loans/{created['id']}", headers=staff_headers).json()
    assert fetched["reviewer_id"] == body["reviewer_id"]
    assert fetched["reviewed_at"] == body["reviewed_at"]
    assert fetched["final_decision"] == "approved"


def test_decision_with_notes_persists_notes(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)
    response = client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "approved", "notes": "Strong income-to-debt ratio, approving."},
        headers=staff_headers,
    )
    assert response.status_code == 200
    assert response.json()["review_notes"] == "Strong income-to-debt ratio, approving."


def test_cannot_decide_an_application_that_has_not_been_scored(client, db_session):
    """
    Scoring is synchronous at creation, so an application only sits at
    SUBMITTED in the rare case scoring never completed. Simulated here by
    forcing the row back to SUBMITTED directly, to prove the guard exists.
    """
    import uuid

    from app.models.loan_application import LoanApplication, LoanStatus

    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)

    # created["id"] is a plain string from the JSON response — db_session.get()
    # needs an actual uuid.UUID (the same conversion FastAPI normally does
    # automatically for path params via the `loan_application_id: uuid.UUID`
    # type annotation), so it's done explicitly here.
    loan_row = db_session.get(LoanApplication, uuid.UUID(created["id"]))
    loan_row.status = LoanStatus.SUBMITTED
    db_session.add(loan_row)
    db_session.commit()

    response = client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "approved"},
        headers=staff_headers,
    )
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# PATCH /loans/{id}/notes
# ---------------------------------------------------------------------------


def test_notes_requires_authentication(client):
    response = client.patch(
        "/api/v1/loans/00000000-0000-0000-0000-000000000000/notes",
        json={"notes": "hello"},
    )
    assert response.status_code == 401


def test_applicant_cannot_submit_notes(client):
    applicant_token = _register(client, "jordan@example.com")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    created = _submit_application(client, applicant_headers)

    response = client.patch(
        f"/api/v1/loans/{created['id']}/notes",
        json={"notes": "trying to self-annotate"},
        headers=applicant_headers,
    )
    assert response.status_code == 403


def test_staff_can_add_notes(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)
    response = client.patch(
        f"/api/v1/loans/{created['id']}/notes",
        json={"notes": "Waiting on updated bank statement."},
        headers=staff_headers,
    )
    assert response.status_code == 200
    assert response.json()["review_notes"] == "Waiting on updated bank statement."


def test_notes_can_be_updated(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)
    client.patch(
        f"/api/v1/loans/{created['id']}/notes",
        json={"notes": "First pass: looks fine."},
        headers=staff_headers,
    )
    response = client.patch(
        f"/api/v1/loans/{created['id']}/notes",
        json={"notes": "Second pass: confirmed, approving."},
        headers=staff_headers,
    )
    assert response.status_code == 200
    assert response.json()["review_notes"] == "Second pass: confirmed, approving."


def test_notes_are_persisted_across_requests(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)
    client.patch(
        f"/api/v1/loans/{created['id']}/notes",
        json={"notes": "Persisted note."},
        headers=staff_headers,
    )

    fetched = client.get(f"/api/v1/loans/{created['id']}", headers=staff_headers)
    assert fetched.status_code == 200
    assert fetched.json()["review_notes"] == "Persisted note."


def test_notes_cannot_be_edited_after_final_decision(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)
    client.patch(
        f"/api/v1/loans/{created['id']}/decision",
        json={"decision": "rejected"},
        headers=staff_headers,
    )

    response = client.patch(
        f"/api/v1/loans/{created['id']}/notes",
        json={"notes": "Trying to edit after rejection."},
        headers=staff_headers,
    )
    assert response.status_code == 409


def test_notes_on_nonexistent_application_returns_404(client):
    staff_token = _register(client, "alex@bank.com", role="staff")
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    response = client.patch(
        "/api/v1/loans/00000000-0000-0000-0000-000000000000/notes",
        json={"notes": "hello"},
        headers=staff_headers,
    )
    assert response.status_code == 404


def test_empty_notes_rejected_by_validation(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    created = _submit_application(client, applicant_headers)
    response = client.patch(
        f"/api/v1/loans/{created['id']}/notes",
        json={"notes": ""},
        headers=staff_headers,
    )
    assert response.status_code == 422