"""add staff review workflow fields to loan_applications

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    final_decision_enum = postgresql.ENUM(
        "approved", "rejected", name="final_decision", create_type=True
    )
    final_decision_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "loan_applications",
        sa.Column(
            "reviewer_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "loan_applications",
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "loan_applications",
        sa.Column(
            "review_notes",
            sa.Text(),
            nullable=True,
        ),
    )
    op.add_column(
        "loan_applications",
        sa.Column(
            "final_decision",
            postgresql.ENUM(
                "approved",
                "rejected",
                name="final_decision",
                create_type=False,
            ),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_loan_applications_reviewer_id",
        "loan_applications",
        "users",
        ["reviewer_id"],
        ["id"],
    )
    op.create_index(
        "ix_loan_applications_reviewer_id",
        "loan_applications",
        ["reviewer_id"],
    )
    op.create_index(
        "ix_loan_applications_final_decision",
        "loan_applications",
        ["final_decision"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_loan_applications_final_decision",
        table_name="loan_applications",
    )
    op.drop_index(
        "ix_loan_applications_reviewer_id",
        table_name="loan_applications",
    )
    op.drop_constraint(
        "fk_loan_applications_reviewer_id",
        "loan_applications",
        type_="foreignkey",
    )

    op.drop_column("loan_applications", "final_decision")
    op.drop_column("loan_applications", "review_notes")
    op.drop_column("loan_applications", "reviewed_at")
    op.drop_column("loan_applications", "reviewer_id")

    postgresql.ENUM(
        name="final_decision"
    ).drop(op.get_bind(), checkfirst=True)