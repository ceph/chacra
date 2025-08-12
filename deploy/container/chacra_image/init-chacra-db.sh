#!/usr/bin/env bash
# env like APP_NAME,APP_HOME is pass by dockerfile
echo $APP_NAME
echo $APP_HOME
echo "init chacra database..."

psql -v ON_ERROR_STOP=1 -h 127.0.0.1 -p 5432 --username postgres --dbname postgres -tc \
    "SELECT 1 FROM pg_database WHERE datname = 'chacra'" | grep -q 1 || \
psql -v ON_ERROR_STOP=1 -h 127.0.0.1 -p 5432 --username postgres --dbname postgres -c \
    "CREATE DATABASE chacra;"

echo "init success"
echo "chacra database is prepare done."
echo "check chacra database weather to be fill data..."

res=$(psql -v ON_ERROR_STOP=1 -h 127.0.0.1 -p 5432 --username postgres --dbname "chacra" -t -c "SELECT COUNT(*) FROM projects;")
DATABASE_CHECK_RC=$?

echo "check result: code=$DATABASE_CHECK_RC"

if [ $DATABASE_CHECK_RC -ne 0 ] || [ "$res" = "0" ]; then
    echo "need to fill data for ${APP_NAME}..."
    
    if [ -f "${APP_HOME}/bin/pecan" ] && [ -f "${APP_HOME}/src/${APP_NAME}/prod.py" ]; then
        echo "fill data is started..."
        export ALEMBIC_CONFIG="${APP_HOME}/src/${APP_NAME}/alembic-prod.ini"
        if ${APP_HOME}/bin/pecan populate ${APP_HOME}/src/${APP_NAME}/prod.py; then
            echo "fill data done"
        else
            echo "warn: fill ddta fail,but start container continue"
        fi
    else
        echo "warn: pecan isn't exist"
        exit 1
    fi
else
    echo "skip fill data"
fi