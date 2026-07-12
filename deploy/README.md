# Deploying OptiVault to AWS (ECS/Fargate)

This is the concrete path from "runs on my laptop" to "runs in production."
It's written as a checklist you work through once, most of which only has
to be done a single time (the CI pipeline handles redeploys after that).

## 1. Provision the stateful pieces first

These outlive any single deploy, so set them up before touching ECS:

- **RDS PostgreSQL** (`db.t4g.micro` is plenty to start) in a private subnet.
- **ElastiCache Redis** (`cache.t4g.micro`) in the same VPC, private subnet.
- **3 Secrets Manager entries**: `optivault/database-url`, `optivault/redis-url`,
  `optivault/jwt-secret` (generate with `python -c "import secrets; print(secrets.token_hex(32))"`).

Both task definitions in this folder read `DATABASE_URL` / `REDIS_URL` /
`SECRET_KEY` from Secrets Manager at container start — nothing is ever
baked into the image or committed to the repo.

## 2. ECR repositories

```bash
aws ecr create-repository --repository-name optivault-api
aws ecr create-repository --repository-name optivault-worker
```

## 3. IAM roles

- `optivault-ecs-execution-role` — standard ECS execution role (pull image,
  write logs, read the three secrets above).
- `optivault-api-task-role` — no AWS permissions needed; it never talks to
  customer buckets directly.
- `optivault-worker-task-role` — needs `sts:AssumeRole` scoped to the
  external ID pattern customers use when granting you their read-only role.
  This is the one role that actually touches customer AWS accounts, so keep
  its policy as narrow as possible.

## 4. Cluster, services, load balancer

```bash
aws ecs create-cluster --cluster-name optivault
```

Register both task definitions in this folder (fill in `<ACCOUNT_ID>`,
`<REGION>`, `<IMAGE_TAG>` first):

```bash
aws ecs register-task-definition --cli-input-json file://deploy/ecs-task-definition-api.json
aws ecs register-task-definition --cli-input-json file://deploy/ecs-task-definition-worker.json
```

Create an Application Load Balancer in front of the `api` service (target
group on port 8000, health check path `/health`), then create both ECS
services pointing at the cluster — `api` behind the ALB, `worker` with no
load balancer since it only consumes from the Celery queue.

## 5. Database migrations

Run once against the new RDS instance, from anywhere with network access
to it (a bastion, or a one-off ECS task using the API image):

```bash
alembic upgrade head
```

## 6. Wire up CI/CD

`.github/workflows/ci.yml` already builds both images on every push to
`main`. The remaining piece — logging into ECR, pushing the tagged images,
and calling `aws ecs update-service --force-new-deployment` — is a natural
next step once steps 1-4 are actually provisioned; there's no point
automating a deploy target that doesn't exist yet.

## Cost note

RDS + ElastiCache + ALB + 2 Fargate tasks runs roughly $60-90/month even at
idle on the smallest viable instance sizes — worth knowing before you spin
this up, since none of it is in the AWS free tier long-term. Fine for a
resume demo you spin up, screenshot, and tear down; worth revisiting
Render/Fly if you want something to stay live indefinitely without cost.
