# OptiVault — AI Cloud Storage Cost Optimizer

Connects to a customer's AWS S3 account (read-only), scans object metadata,
detects duplicate files / stale data / wrong storage tiers, and proposes
optimization actions the customer reviews and approves before anything
executes. Never reads or stores file contents — only metadata.

## Status

Backend: Scanner, Analyzer, and Optimizer-adjacent reporting are live and
tested. Frontend: auth + dashboard are live and wired to the real API.
Payments (Razorpay) and Google OAuth are scaffolded but need your own
free test credentials before they can go further (see Roadmap).

## Architecture

```
Next.js dashboard (this repo: /frontend)
        │
        ▼
FastAPI backend  ──►  PostgreSQL (users, accounts, file metadata, reports)
        │
        ▼
Celery + Redis   ──►  Scanner (boto3, paginated, metadata-only)
                       Analyzer (duplicate/stale/wrong-tier detection, pure Python, unit tested)
```

Full request-level detail is in the original architecture doc; this repo
implements it with a couple of deliberate simplifications for the current
stage — no DynamoDB sharding or Step Functions, since neither is a real
constraint yet at pre-launch scale.

## Running locally

**Backend:**
```bash
cp .env.example .env          # then edit SECRET_KEY at minimum
docker compose up --build
cd backend && alembic revision --autogenerate -m "init" && alembic upgrade head
```
- API: http://localhost:8000/docs

**Frontend:**
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```
- App: http://localhost:3000

## Try it without an AWS account

```bash
docker compose exec api python -m app.scripts.seed_test_data you@example.com
```
Seeds a fake bucket with duplicates, stale files, and wrong-tier files
directly into Postgres — sign up with that email first via the frontend
or `/docs`, then hit Scan → Analyze on the dashboard.

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```
The scanner tests mock S3 via `moto`; the analyzer tests are pure Python
with no external dependency at all. Both run in CI on every push.

## Roadmap

- [x] Scanner: paginated S3 metadata indexing, tested against mocked S3
- [x] Analyzer: duplicate/stale/wrong-tier detection with real AWS pricing, unit tested
- [x] Auth, cloud account management, scan job tracking
- [x] Local dev environment (Docker Compose), CI (lint + test), ECS/Fargate deploy scaffolding
- [x] Frontend dashboard (Next.js) — signup/login, connect bucket, scan, analyze, waste breakdown
- [ ] Optimizer: manifest generation, dry-run preview, execute (move/delete/compress)
- [ ] Google OAuth — code path ready, needs a free Google Cloud OAuth client ID from you
- [ ] Razorpay checkout — needs a free Razorpay test-mode account from you (no KYC required for test mode)
- [ ] Deploy frontend to Vercel (no blocker, can do anytime)
- [ ] Deploy backend per `deploy/README.md` (needs an AWS account first)
- [ ] Predictor: simple ML model for access-likelihood scoring

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
- **Why is the Analyzer pure functions instead of DB queries directly?**
  It means the detection rules (what counts as a duplicate, what counts
  as stale) can be unit tested with plain Python dicts in milliseconds,
  with zero database or AWS dependency — which is also how a real bug
  (double-counted archive candidates from overlapping stale/wrong-tier
  sets) got caught with a regression test instead of shipping silently.
