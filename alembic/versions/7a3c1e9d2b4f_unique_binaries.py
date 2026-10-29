"""make binaries unique

Revision ID: 7a3c1e9d2b4f
Revises: 52d176771ae6
Create Date: 2026-10-17 18:00:00.000000

On PostgreSQL the ADD CONSTRAINT needs an ACCESS EXCLUSIVE lock on
binaries. Every in-flight upload holds a share lock on the table for the
whole request, so on a live node the ALTER queues behind them and, while
it waits, blocks every other query on the table. The migration therefore
takes that lock itself, up front, with lock_timeout set to 10 seconds:
if the lock cannot be taken in time the migration fails before it has
done anything, and it can simply be run again when the node is quieter.
Holding the lock from the start also means no upload can store a new
duplicate between the dedup and the constraint, which would make the
ADD CONSTRAINT fail.

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
    if op.get_bind().dialect.name == 'postgresql':
        # fail fast instead of queueing behind uploads, see the docstring
        op.execute("SET LOCAL lock_timeout = '10s'")
        op.execute('LOCK TABLE binaries IN ACCESS EXCLUSIVE MODE')
    # keep the newest row of the binaries that were stored more than once.
    # PARTITION BY groups NULLs together like GROUP BY does. Unlike
    # "id NOT IN (SELECT MAX(id) ... GROUP BY ...)", which PostgreSQL
    # evaluates once per row unless the subquery fits in work_mem, this is
    # a hash semi join, so the delete is linear whatever work_mem is.
    op.execute(
        'DELETE FROM binaries WHERE id IN ('
        'SELECT id FROM ('
        'SELECT id, ROW_NUMBER() OVER (PARTITION BY %s ORDER BY id DESC) AS rn '
        'FROM binaries) dup WHERE rn > 1)' % ', '.join(COLUMNS))
    with op.batch_alter_table('binaries') as batch_op:
        batch_op.create_unique_constraint('uq_binaries_identity', COLUMNS)


def downgrade():
    with op.batch_alter_table('binaries') as batch_op:
        batch_op.drop_constraint('uq_binaries_identity', type_='unique')
