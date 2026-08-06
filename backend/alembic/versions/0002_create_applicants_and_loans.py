"""create applicants and loan_applications tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-06

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    employment_status_enum = postgresql.ENUM(
        "employed", "self_employed", "unemployed", "student",
        name="employment_status", create_type=True,
    )
    employment_status_enum.create(op.get_bind(), checkfirst=True)

    loan_purpose_enum = postgresql.ENUM(
        "personal", "auto", "education", "business", "home",
        name="loan_purpose", create_type=True,
    )
    loan_purpose_enum.create(op.get_bind(), checkfirst=True)

    loan_status_enum = postgresql.ENUM(
        "submitted", "scored", "approved", "rejected", "manual_review",
        name="loan_status", create_type=True,
    )
    loan_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "applicants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("annual_income", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "employment_status",
            postgresql.ENUM(
                "employed", "self_employed", "unemployed", "student",
                name="employment_status", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("existing_debt", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("credit_history_years", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_applicants_user_id"),
    )
    op.create_index("ix_applicants_user_id", "applicants", ["user_id"], unique=True)

    op.create_table(
        "loan_applications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("applicant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("loan_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "loan_purpose",
            postgresql.ENUM(
                "personal", "auto", "education", "business", "home",
                name="loan_purpose", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("loan_tenure_months", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "submitted", "scored", "approved", "rejected", "manual_review",
                name="loan_status", create_type=False,
            ),
            nullable=False,
            server_default="submitted",
        ),
        sa.Column(
            "submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(
            ["applicant_id"], ["applicants.id"], name="fk_loan_applications_applicant_id"
        ),
    )
    op.create_index("ix_loan_applications_applicant_id", "loan_applications", ["applicant_id"])
    op.create_index("ix_loan_applications_status", "loan_applications", ["status"])


def downgrade() -> None:
    op.drop_index("ix_loan_applications_status", table_name="loan_applications")
    op.drop_index("ix_loan_applications_applicant_id", table_name="loan_applications")
    op.drop_table("loan_applications")

    op.drop_index("ix_applicants_user_id", table_name="applicants")
    op.drop_table("applicants")

    postgresql.ENUM(name="loan_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="loan_purpose").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="employment_status").drop(op.get_bind(), checkfirst=True)