FROM ubuntu:20.04

ARG APP_NAME="chacra"
# please do not pass env to container while start container.
# those env is valid on build image,not run time.
ENV APP_NAME=${APP_NAME}
ENV APP_HOME="/opt/${APP_NAME}"
ENV DEBIAN_FRONTEND=noninteractive

# In Ubuntu 20.04, createrepo cannot be installed. In Ubuntu 22.04, we may be able to use createrepo-c instead of createrepo, but in Ubuntu 22.04, chacra has some Python problems(install celery[librabbitmq] will crash). Since the current chacra works fine in Ubuntu 20.04, we'll just ignore createrepo for now.
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    virtualenv \
    librabbitmq-dev \
    libffi-dev \
    pkg-config \
    postgresql-client \
    sudo \
    git cmake libtool autoconf nginx reprepro \
    && mkdir -p /var/log/celery /etc/nginx/sites-available /etc/nginx/sites-enabled \
    && rm -f /etc/nginx/sites-enabled/default \
    && mkdir -p /var/lib/nginx/body /var/log/nginx \
    && useradd --system --no-create-home --shell /bin/false --user-group nginx \
    && chown -R nginx:nginx /var/lib/nginx /var/log/nginx \
    && chmod -R 755 /var/lib/nginx /var/log/nginx

# In Ubuntu 20.04, the Python version is 3.8. For chacra, we need to make some changes to satisfy Python 3.8 compatibility. So I use my repository instead of ceph/chakra.
RUN virtualenv ${APP_HOME} \
    && . ${APP_HOME}/bin/activate \
    && pip install --upgrade pip setuptools\
    && pip install -I -e git+https://github.com/ceph/chacra@main#egg=chacra \
    && pip install librabbitmq && pip install -r  ${APP_HOME}/src/${APP_NAME}/requirements.txt

COPY ./py3.8.patch ${APP_HOME}/src/${APP_NAME}/py3.8.patch

RUN cd ${APP_HOME}/src/${APP_NAME} && git apply py3.8.patch

COPY ./main.sh /bin/main.sh
COPY ./init-chacra-db.sh ${APP_HOME}/init-chacra-db.sh

COPY ./conf/*.py ${APP_HOME}/src/${APP_NAME}/
COPY ./conf/alembic-prod.ini ${APP_HOME}/src/${APP_NAME}/alembic-prod.ini

COPY ./conf/nginx.conf /etc/nginx/nginx.conf
COPY ./conf/nginx_site.conf /etc/nginx/sites-available/${APP_NAME}.conf

RUN ln -s /etc/nginx/sites-available/${APP_NAME}.conf  /etc/nginx/sites-enabled/${APP_NAME}.conf

ENV PECAN_CONFIG=${APP_HOME}/src/${APP_NAME}/prod.py


CMD ["/bin/sh","-c","/bin/main.sh"]