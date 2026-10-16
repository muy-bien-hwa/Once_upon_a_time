"""add report reason and detail

Revision ID: 903220f4e8d4
Revises: d75be7e1aa7b
Create Date: 2026-10-16 23:32:14.158099

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '903220f4e8d4'
down_revision: Union[str, Sequence[str], None] = 'd75be7e1aa7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 신고 사유 1개 + 설명 500자 (D-93)
    # 이미 있던 신고 줄에도 값이 필요해서 잠깐 'other'를 기본값으로 두고 바로 거둠
    # → 앞으로 들어오는 신고는 사유를 반드시 보내야 함
    op.add_column(
        'reports',
        sa.Column('reason', sa.String(length=20), nullable=False, server_default='other'),
    )
    op.alter_column('reports', 'reason', server_default=None)
    op.add_column(
        'reports',
        sa.Column('detail', sa.String(length=500), nullable=False, server_default=''),
    )
    # 사유는 7종 중 하나만 (자동 생성이 CHECK는 못 알아보므로 직접 적음)
    op.create_check_constraint(
        'reason_valid',
        'reports',
        "reason IN ('abuse', 'sexual', 'violence', 'spam', 'privacy', 'plagiarism', 'other')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('ck_reports_reason_valid'), 'reports', type_='check')
    op.drop_column('reports', 'detail')
    op.drop_column('reports', 'reason')
