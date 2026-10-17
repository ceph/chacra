"""make binaries unique

Revision ID: 7a3c1e9d2b4f
Revises: 52d176771ae6
Create Date: 2026-10-17 18:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = '7a3c1e9d2b4f'
down_revision = '52d176771ae6'
branch_labels = None
depends_on = None

from alembic import op


COLUMNS = ['project_id', 'name', 'ref', 'sha1', 'distro', 'distro_version',
           'arch', 'flavor']


def upgrade():
    # keep the newest row of the binaries that were stored more than once
    op.execute(
        'DELETE FROM binaries WHERE id NOT IN '
        '(SELECT MAX(id) FROM binaries GROUP BY %s)' % ', '.join(COLUMNS))
    with op.batch_alter_table('binaries') as batch_op:
        batch_op.create_unique_constraint('uq_binaries_identity', COLUMNS)


def downgrade():
    with op.batch_alter_table('binaries') as batch_op:
        batch_op.drop_constraint('uq_binaries_identity', type_='unique')
