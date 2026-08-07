"""add risk prediction fields to loan_applications

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    risk_category_enum = postgresql.ENUM(
        "low", "medium", "high", name="risk_category", create_type=True
    )
    risk_category_enum.create(op.get_bind(), checkfirst=True)

    recommendation_enum = postgresql.ENUM(
        "approved", "review", "reject", name="recommendation", create_type=True
    )
    recommendation_enum.create(op.get_bind(), checkfirst=True)

    op.add_column("loan_applications", sa.Column("risk_score", sa.Integer(), nullable=True))
    op.add_column(
        "loan_applications",
        sa.Column(
            "risk_category",
            postgresql.ENUM("low", "medium", "high", name="risk_category", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        "loan_applications",
        sa.Column(
            "recommendation",
            postgresql.ENUM("approved", "review", "reject", name="recommendation", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        "loan_applications", sa.Column("prediction_timestamp", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("loan_applications", sa.Column("model_version", sa.String(length=50), nullable=True))
    op.add_column("loan_applications", sa.Column("top_risk_factors", sa.JSON(), nullable=True))

    op.create_index("ix_loan_applications_risk_category", "loan_applications", ["risk_category"])


def downgrade() -> None:
    op.drop_index("ix_loan_applications_risk_category", table_name="loan_applications")
    op.drop_column("loan_applications", "top_risk_factors")
    op.drop_column("loan_applications", "model_version")
    op.drop_column("loan_applications", "prediction_timestamp")
    op.drop_column("loan_applications", "recommendation")
    op.drop_column("loan_applications", "risk_category")
    op.drop_column("loan_applications", "risk_score")

    postgresql.ENUM(name="recommendation").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="risk_category").drop(op.get_bind(), checkfirst=True)