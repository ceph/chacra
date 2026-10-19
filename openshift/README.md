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
5. Create the schema (once per brand‑new database)
```bash
oc -n chacra apply -f openshift/deploy/db-bootstrap-job.yaml
```
Later schema changes need no manual step: every `chacra-api` pod runs
`alembic upgrade head` before it starts, see [Upgrading](#upgrading).
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

## Upgrading

Build a new image (step 3); the image trigger on each Deployment rolls
`chacra-api`, `chacra-celery` and `chacra-beat` onto it.

Rollouts migrate themselves: the `db-migrate` init container of
`chacra-api` runs `alembic upgrade head` with the api's own image,
`DATABASE_URL` and the `chacra-alembic` ConfigMap before the api
container starts, so a release that adds Alembic revisions is applied
by the rollout that ships it. The two api replicas start their init
containers at the same time; they serialise on a PostgreSQL
session-level advisory lock (`pg_advisory_lock(hashtext('chacra-alembic'))`),
so the second one waits until the first has finished and then finds
nothing to do. The lock is tied to the init container's connection and
disappears when it exits, whichever way it exits.

Watch it with:
```bash
oc -n chacra rollout status deploy/chacra-api
oc -n chacra logs deploy/chacra-api -c db-migrate
```

If a migration fails, the pod stays in `Init:Error`/`Init:CrashLoopBackOff`
and the old replicas keep serving; the kubelet restarts the init
container with backoff until the upgrade succeeds, because the migration
runs in one transaction and leaves nothing half-applied. A migration
that needs an exclusive lock on a busy table (e.g. `7a3c1e9d2b4f`, which
adds a constraint to `binaries`) gives up after 10 seconds rather than
queueing behind in-flight uploads, so under constant upload traffic it
can take a few restarts to get through.

`openshift/deploy/db-migration-job.yaml` still exists for running the
same upgrade by hand, e.g. against a restored dump before deploying.
Delete the previous Job before re-applying it:
```bash
oc -n chacra delete job chacra-db-migrate --ignore-not-found
oc -n chacra apply -f openshift/deploy/db-migration-job.yaml
oc -n chacra logs -f job/chacra-db-migrate
```

## Migrating an existing (ansible/VM) chacra into OpenShift

`binaries.path` and `repos.path` in the database are absolute on-disk paths. A VM install
uses `/opt/binaries` and `/opt/repos`; the container uses `STORAGE_ROOT=/data`, so after restoring
a `pg_dump` from a VM rewrite them, or every `/binaries/...` download 404s (chacra strips
`binary_root` from the stored path to build its `X-Accel-Redirect`):

```sql
update binaries set path = regexp_replace(path, '^/opt/binaries/', '/data/binaries/') where path like '/opt/binaries/%';
update repos    set path = regexp_replace(path, '^/opt/repos/',    '/data/repos/')    where path like '/opt/repos/%';
```

The repo trees themselves are symlinks into the binaries tree with absolute targets, so after
rsyncing a VM's `/opt/repos` into `/data/repos` rewrite those too (`/r/` downloads 404 otherwise):

```sh
find /data/repos -type l -lname '/opt/*' -print0 | while IFS= read -r -d '' l; do
  t=$(readlink "$l"); ln -sfn "/data/${t#/opt/}" "$l"
done
find /data/repos -xtype l | wc -l   # must be 0
```

## Deploying to a different namespace

Every document in `openshift/deploy/` carries an explicit
`namespace: chacra` (a partially-namespaced set silently scatters the
unnamespaced objects into whatever namespace your context points at).
To deploy under another namespace, rewrite it first, e.g.:

```
sed -i 's/namespace: chacra$/namespace: my-chacra/' openshift/deploy/*.yaml*
```

and update the in-cluster image reference in `db-bootstrap-job.yaml` /
`db-migration-job.yaml` (`image-registry.openshift-image-registry.svc:5000/chacra/chacra:latest`)
to match.
