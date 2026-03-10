#!/usr/bin/env sh
set -ex
/opt/venv/bin/python - <<'PY'
try:
    import pkg_resources
except Exception:
    import sys, subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", "setuptools"])
PY
# Use module path suitable for installed package
exec /opt/venv/bin/celery -A chacra.asynch worker \
     --loglevel=INFO -Q poll_repos,celery,build_repos --hostname=worker@%h
