i
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

## Mandatory Steps Before Deployment

Before deploying Chacra, you must edit the following files:
```
openshift/deploy/chacra-data-rwx-pvc.yaml
openshift/deploy/secret.yaml.example
```
1. **Persistent Volume Claim (PVC) Configuration**


   Chacra requires a ReadWriteMany (RWX) PersistentVolumeClaim for shared data.

   
   File location: `openshift/deploy/chacra-data-rwx-pvc.yaml`

   In this file, **replace the placeholder values** shown below with values that are valid for your Kubernetes/OpenShift cluster.
   ```
   storageClassName: STORAGE_CLASS_NAME
   storage: STORAGE_SIZE
   ```
**What to replace**

- `STORAGE_CLASS_NAME`
  
  Replace this with the name of an RWX‑capable StorageClass available in your cluster.
  
  Common examples include:

  - `cephfs-rwx`
  - `ocs-storagecluster-cephfs`
  - `nfs-rwx`

- `STORAGE_SIZE`
  
  Replace this with the desired size for the persistent volume.
  
  Examples:

  - `50Gi`
  - `100Gi`
  - `200Gi`

**EXAMPLE**
```
storageClassName: cephfs-rwx
storage: 200Gi
```

2. `openshift/deploy/secret.yaml.example`

    This is a template secret file and must be customized before deployment:

    **How to create the Secret**

    1. Copy the example file
       ```
       cp openshift/deploy/secret.yaml.example openshift/deploy/secret.yaml
       ```
    2. Edit the secret file
       Open openshift/deploy/secret.yaml and replace all placeholder values with values appropriate for your environment.
   
       | Placeholder | Description | Example |
       | -------- | -------- | -------- |
       | DATABASE_CONNECTION_URL | PostgreSQL connection URL | postgresql://chacra:<password>@postgres:5432/chacra |
       | DB_USERNAME | Database user | chacra |
       | DB_PASSWORD | Database password | strongpassword |
       | API_USERNAME | Chacra API user | admin |
       | API_KEY | Chacra API key | <generated-api-key> |
       | RABBITMQ_URL | RabbitMQ connection URL | amqp://user:password@rabbitmq:5672/%2f |
       | CHACRA_HOSTNAME | External Chacra hostname | chacra.apps.example.com |
       | CHACRA_CALLBACK_URL | Callback service URL | https://shaman.apps.example.com/api/repos/ |
       | CALLBACK_API_KEY | Callback authentication key | <callback-key> |
       | HEALTH_PING_URL | Health ping endpoint | https://shaman.apps.example.com/api/nodes/ |
  
   Do not leave any placeholder values unchanged

## Deployment Steps 
(All the commands below assume the namespace is Chacra)

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
oc -n chacra apply -f openshift/deploy/service.yaml
oc -n chacra apply -f openshift/deploy/route.yaml
oc -n chacra apply -f openshift/deploy/chacra-nginx.yaml
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
