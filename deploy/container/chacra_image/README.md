## 1. APP_NAME

The default APP_NAME is chacra.

If you need to modify APP_NAME, please manually modify files including but not limited to nginx.conf,nginx_site.conf, etc. The reason one-click modification is not supported is that there are too many highly customized areas, and automatic modification would result in loss of universality. Therefore, if modification is needed, it can be implemented manually, which is actually not troublesome. Finally, pass this parameter when building.

Please note that passing this parameter when starting the container is ineffective.


## 2. how to start this container

This container cannot be started independently. You need to use docker compose to start postgresql and rabbitmq, and then the chacra container needs to be able to access the other two services via localhost.