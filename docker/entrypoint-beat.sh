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
