#!/usr/bin/env sh
set -ex
/opt/venv/bin/python - <<'PY'
try:
    import pkg_resources
except Exception:
    import sys, subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", "setuptools"])
PY
exec /opt/venv/bin/celery -A chacra.asynch beat --loglevel=INFO
❯ cat entrypoint-api.sh
#!/usr/bin/env bash
set -euo pipefail

export ALEMBIC_CONFIG=/etc/chacra/alembic.ini

# Wait for Postgres
until pg_isready -h "${CHACRA_DB_HOST}" -p "${CHACRA_DB_PORT}" -U "${CHACRA_DB_USER}"; do
  echo "Waiting for Postgres..."
  sleep 2
done

# DB migrations + seed (idempotent)
alembic upgrade head || true
pecan populate /etc/chacra/prod.py || true

# Serve API
exec gunicorn --workers="${GUNICORN_WORKERS:-4}" --timeout=1200 \
  --bind 0.0.0.0:8000 'pecan:make_app("/etc/chacra/prod.py")'
