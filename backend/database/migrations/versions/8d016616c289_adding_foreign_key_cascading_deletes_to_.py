"""Adding foreign key cascading deletes to help with cleaner report deletion.

Revision ID: 8d016616c289
Revises: 7a3161d8f5d7
Create Date: 2025-06-03 13:09:13.194107

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8d016616c289"
down_revision = "7a3161d8f5d7"
branch_labels = None
depends_on = None


def upgrade():
    # Update foreign keys to use cascading deletes
    op.drop_constraint(
        "violation_images_violation_id_fkey", "violation_images", type_="foreignkey"
    )
    op.create_foreign_key(
        "violation_images_violation_id_fkey",
        "violation_images",
        "violations",
        ["violation_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("violations_report_id_fkey", "violations", type_="foreignkey")
    op.create_foreign_key(
        "violations_report_id_fkey",
        "violations",
        "violation_reports",
        ["report_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Now delete the violation reports with ids 44 to 61
    connection = op.get_bind()
    connection.execute(
        sa.text("DELETE FROM violation_reports WHERE id BETWEEN :start_id AND :end_id"),
        {"start_id": 44, "end_id": 61},
    )


def downgrade():
    # Reverse the cascading delete FK changes
    op.drop_constraint(
        "violation_images_violation_id_fkey", "violation_images", type_="foreignkey"
    )
    op.create_foreign_key(
        "violation_images_violation_id_fkey",
        "violation_images",
        "violations",
        ["violation_id"],
        ["id"],
    )

    op.drop_constraint("violations_report_id_fkey", "violations", type_="foreignkey")
    op.create_foreign_key(
        "violations_report_id_fkey",
        "violations",
        "violation_reports",
        ["report_id"],
        ["id"],
    )
