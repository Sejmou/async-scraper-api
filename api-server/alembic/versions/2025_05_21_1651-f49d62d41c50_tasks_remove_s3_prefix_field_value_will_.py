"""tasks: remove s3_prefix field (value will be determined at runtime)

Revision ID: f49d62d41c50
Revises: b4173d74b35d
Create Date: 2025-05-21 16:51:22.435621

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f49d62d41c50'
down_revision: Union[str, None] = 'b4173d74b35d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('task', 's3_prefix')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('task', sa.Column('s3_prefix', sa.VARCHAR(), nullable=False))
    # ### end Alembic commands ###
