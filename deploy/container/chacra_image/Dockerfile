FROM ubuntu:24.04

ARG APP_NAME="chacra"
# please do not pass env to container while start container.
# those env is valid on build image,not run time.
ENV APP_NAME=${APP_NAME}
ENV APP_HOME="/opt/${APP_NAME}"
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    virtualenv \
    librabbitmq-dev \
    libffi-dev \
    pkg-config \
    postgresql-client \
    sudo \
    git cmake libtool autoconf nginx reprepro createrepo-c\
    && mkdir -p /var/log/celery /etc/nginx/sites-available /etc/nginx/sites-enabled \
    && rm -f /etc/nginx/sites-enabled/default \
    && mkdir -p /var/lib/nginx/body /var/log/nginx \
    && useradd --system --no-create-home --shell /bin/false --user-group nginx \
    && chown -R nginx:nginx /var/lib/nginx /var/log/nginx \
    && chmod -R 755 /var/lib/nginx /var/log/nginx

RUN virtualenv ${APP_HOME} \
    && . ${APP_HOME}/bin/activate \
    && pip install --upgrade pip setuptools\
    && pip install -I -e git+https://github.com/ceph/chacra@main#egg=chacra \
    && pip install -r  ${APP_HOME}/src/${APP_NAME}/requirements.txt \
    && pip install tox uv \
    && uv python install 3.11 3.12 3.13

COPY ./main.sh /bin/main.sh
COPY ./init-chacra-db.sh ${APP_HOME}/init-chacra-db.sh

COPY ./conf/prod.py ${APP_HOME}/src/${APP_NAME}/prod.py
COPY ./conf/prod_db.py ${APP_HOME}/src/${APP_NAME}/${APP_NAME}/prod_db.py
COPY ./conf/prod_api_creds.py ${APP_HOME}/src/${APP_NAME}/${APP_NAME}/prod_api_creds.py

# override origin conf.py to pass tox
COPY ./conf/conftest.py ${APP_HOME}/src/${APP_NAME}/${APP_NAME}/tests/conftest.py

COPY ./conf/alembic-prod.ini ${APP_HOME}/src/${APP_NAME}/alembic-prod.ini

COPY ./conf/nginx.conf /etc/nginx/nginx.conf
COPY ./conf/nginx_site.conf /etc/nginx/sites-available/${APP_NAME}.conf

RUN ln -s /etc/nginx/sites-available/${APP_NAME}.conf  /etc/nginx/sites-enabled/${APP_NAME}.conf \
    && sed -i 's/2\.9\.9/2.9.10/g' ${APP_HOME}/src/${APP_NAME}/setup.py \
    && sed -i 's/2\.9\.9/2.9.10/g' ${APP_HOME}/src/${APP_NAME}/requirements.txt

ENV PECAN_CONFIG=${APP_HOME}/src/${APP_NAME}/prod.py


CMD ["/bin/sh","-c","/bin/main.sh"]