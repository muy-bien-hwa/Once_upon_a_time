"""first sentence cannot be deleted

Revision ID: 43cf3d122faa
Revises: 085be33de338
Create Date: 2026-09-21 18:16:01.292002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43cf3d122faa'
down_revision: Union[str, Sequence[str], None] = '085be33de338'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 직접 작성: autogenerate는 이미 있는 테이블에 추가한 CHECK 조건을 감지하지 못함
    # 첫 문장은 삭제될 수 없음 (D-66)
    op.create_check_constraint(
        op.f("ck_sentences_root_not_deleted"),
        "sentences",
        "parent_id IS NOT NULL OR status <> 'deleted'",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f("ck_sentences_root_not_deleted"), "sentences", type_="check")
