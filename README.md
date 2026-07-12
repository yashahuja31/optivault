# OptiVault — AI Cloud Storage Cost Optimizer

Connects to a customer's AWS S3 account (read-only), scans object metadata,
detects duplicate files / stale data / wrong storage tiers, and proposes
optimization actions the customer reviews and approves before anything
executes. Never reads or stores file contents — only metadata.

## Status

This is the Week 1 milestone: Scanner is live and tested. Analyzer,
Optimizer, and the frontend dashboard are the next iterations (see Roadmap).

## Architecture

```
React/Next.js dashboard
        │
        ▼
FastAPI backend  ──►  PostgreSQL (users, accounts, file metadata, manifests)
        │
        ▼
Celery + Redis   ──►  Scanner (boto3, paginated, metadata-only)
```

Full request-level detail is in the original architecture doc; this repo
implements it with a couple of deliberate simplifications for the current
stage — no DynamoDB sharding or Step Functions, since neither is a real
constraint yet at pre-launch scale.

## Running locally

```bash
cp .env.example .env          # then edit SECRET_KEY at minimum
docker compose up --build
```

- API: http://localhost:8000/docs (FastAPI auto-generated Swagger UI)
- Postgres: localhost:5432
- Redis: localhost:6379

First time only, once the containers are up:

```bash
cd backend
alembic revision --autogenerate -m "init"
alembic upgrade head
```

(`docker compose up` also runs `create_all()` as a local-only convenience,
so the app works even before you've run migrations — but Alembic is the
real source of truth for schema changes from here on.)

## Try the scan flow end to end

```bash
# 1. Sign up
curl -X POST localhost:8000/auth/signup -d '{"email":"you@example.com","password":"..."}' -H 'Content-Type: application/json'

# 2. Log in, grab the access_token
curl -X POST localhost:8000/auth/login -d 'username=you@example.com&password=...'

# 3. Connect a bucket (needs real AWS creds available to the worker container,
#    or a role_arn if you've set up cross-account access)
curl -X POST localhost:8000/cloud-accounts -H "Authorization: Bearer <token>" \
     -d '{"bucket_name": "your-test-bucket"}' -H 'Content-Type: application/json'

# 4. Kick off a scan
curl -X POST localhost:8000/cloud-accounts/<id>/scan -H "Authorization: Bearer <token>"

# 5. Poll status, then list results
curl localhost:8000/cloud-accounts/<id>/scan-status -H "Authorization: Bearer <token>"
curl localhost:8000/cloud-accounts/<id>/files -H "Authorization: Bearer <token>"
```

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

The scanner tests use `moto` to mock S3, so they run with no real AWS
account or credentials — this is also what CI runs on every push.

## Roadmap

- [x] Scanner: paginated S3 metadata indexing, tested against mocked S3
- [x] Auth, cloud account management, scan job tracking
- [x] Local dev environment (Docker Compose), CI (lint + test), ECS/Fargate deploy scaffolding
- [ ] Analyzer: duplicate grouping, stale-data detection, tier-mismatch detection, cost estimate
- [ ] Optimizer: manifest generation, dry-run preview, execute (move/delete/compress)
- [ ] Predictor: simple ML model for access-likelihood scoring
- [ ] Frontend dashboard (Next.js)
- [ ] Terraform for the AWS resources described in `deploy/README.md`
- [ ] Real cross-account IAM role flow (currently supports it in code, untested against a real second account)

## Why these particular tradeoffs

Worth having answers ready for, since these are the questions an
interviewer or a technical cofounder will actually ask:

- **Why metadata-only, never file contents?** It's the entire security
  pitch — a data breach here can leak "you have a 4GB file called
  `q3-layoffs-draft.xlsx`," not the file itself. Removes most of the
  compliance burden too.
- **Why Celery/Redis instead of doing scans inline in the API?** Scanning
  a bucket with millions of objects can take minutes; you can't hold an
  HTTP request open for that, and a background worker gives you retries
  and observability for free.
- **Why dry-run before every destructive action?** Because "AI deleted my
  production logs" is the single fastest way to lose a customer's trust —
  the entire product only works if people trust it enough to grant it
  write access at all.
