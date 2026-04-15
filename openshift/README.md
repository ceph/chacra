# Chacra on OpenShift — Quick Start

This guide helps you build and deploy **Chacra** on OpenShift using the provided manifests.

---

## Prerequisites

- OpenShift cluster access and `oc` CLI installed.
- Logged in to the right cluster:  
  ```bash
  oc whoami
  oc project

Need sufficient permissions to create namespace/projects, routes, deployments, and PVCs.

## All commands below assume the namespace is Chacra.

1. (One‑time) Create the namespace
``` 
oc apply -f openshift/deploy/namespace.yaml
```
2. Build pipeline (ImageStream + BuildConfigs)
```
oc -n chacra apply -f openshift/build/
```
3. (a) Build from upstream Git
```
oc -n chacra start-build bc/chacra-git --follow
```
3. (b) OR build from your working tree (binary build)

Use this when you want to build the image from your local repo state.
```
oc -n chacra start-build bc/chacra-binary --from-dir=. --follow
```
4. Deploy infra and app configs

Apply app configuration, secrets, and infra components (Postgres, RabbitMQ, PVC):
```
oc -n chacra apply -f openshift/deploy/configmap.yaml
oc -n chacra apply -f openshift/deploy/alembic-configmap.yaml
oc -n chacra apply -f openshift/deploy/secret.yaml
oc -n chacra apply -f openshift/deploy/chacra-callbacks-secret.yaml
oc -n chacra apply -f openshift/serviceaccount.yaml
oc -n chacra apply -f openshift/deploy/postgres.yaml
oc -n chacra apply -f openshift/deploy/rabbitmq.yaml
oc -n chacra apply -f openshift/deploy/postgres-pvc.yaml
oc -n chacra apply -f openshift/deploy/chacra-data-rwx-pvc.yaml
```
5. Run DB migrations
```bash
# Run once per brand‑new database
oc -n chacra apply -f openshift/deploy/db-bootstrap-job.yaml

# Run only when a new release adds Alembic revisions
oc -n chacra apply -f openshift/deploy/db-migration-job.yaml
```
6. Deploy Chacra API, Celery, Beat and Nginx pod
```
oc -n chacra apply -f openshift/deploy/deployment.yaml
oc -n chacra apply -f openshift/deploy/chacra-nginx.yaml
oc -n chacra apply -f openshift/deploy/service.yaml
oc -n chacra apply -f openshift/deploy/route.yaml
```
7. Verify the rollout

Wait for the Chacra API, Celery and Beat deployments to be ready
```
oc -n chacra rollout status deploy/chacra-api
oc -n chacra rollout status deploy/chacra-celery
oc -n chacra rollout status deploy/chacra-beat
oc -n chacra rollout status deploy/chacra-repos
```
Get the public host
```
oc -n chacra get route chacra -o jsonpath='{.spec.host}{"\n"}'
```
Open the URL in your browser:
```
https://<printed-host>/
```
