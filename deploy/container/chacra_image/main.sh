#! /bin/sh
# env is pass by dockerfile
echo $APP_NAME
echo $APP_HOME
cd ${APP_HOME}/src/${APP_NAME}/${APP_NAME}

sleep 10
${APP_HOME}/bin/celery multi start 5 -Q:1,2 poll_repos,celery -Q:3-5 build_repos -A asynch --logfile=/var/log/celery/%n%I.log

${APP_HOME}/bin/celery -A asynch beat --loglevel=info --logfile=/var/log/celery/beat.log &

/usr/sbin/nginx -g 'daemon off;' &


sleep 10
env APP_HOME=${APP_HOME} APP_NAME=${APP_NAME} ${APP_HOME}/init-chacra-db.sh

${APP_HOME}/bin/gunicorn_pecan -w 10 -t 1200 ${APP_HOME}/src/${APP_NAME}/prod.py