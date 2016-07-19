"""default sha1 to HEAD

Revision ID: 432dc36d3105
Revises: 375985186100
Create Date: 2016-06-10 11:21:08.357158

"""

# revision identifiers, used by Alembic.
revision = '432dc36d3105'
down_revision = '375985186100'
branch_labels = None
depends_on = None

from alembic import op
from sqlalchemy.sql import table, column
import sqlalchemy as sa


def upgrade():
    binaries = table("binaries", column("sha1", sa.String))
    op.execute(
        binaries.update().values(dict(sha1="HEAD"))
    )
    repos = table("repos", column("sha1", sa.String))
    op.execute(
        repos.update().values(dict(sha1="HEAD"))
    )


def downgrade():
    pass
