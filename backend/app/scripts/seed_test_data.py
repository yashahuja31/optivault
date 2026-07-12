"""
Seed the local DB with a fake CloudAccount + FileMetadata rows, so you can
exercise the full Analyzer pipeline without a real AWS account or bucket.

Usage (run inside the running api container):
    docker compose exec api python -m app.scripts.seed_test_data you@example.com

Sign up that email via POST /auth/signup first if you haven't already --
this script attaches the fake data to an existing user, it doesn't create one.
"""
import sys
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import User, CloudAccount, FileMetadata


def seed(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"No user with email '{email}' found. Sign up via POST /auth/signup first.")
            sys.exit(1)

        account = CloudAccount(user_id=user.id, provider="aws", bucket_name="demo-bucket-seeded")
        db.add(account)
        db.commit()
        db.refresh(account)

        now = datetime.utcnow()

        def f(key, size_bytes, etag, days_old, content_type, storage_class="STANDARD"):
            return dict(
                file_key=key,
                size_bytes=size_bytes,
                etag_hash=etag,
                last_modified=now - timedelta(days=days_old),
                content_type=content_type,
                storage_class=storage_class,
            )

        files = [
            # Three exact duplicates (same etag) -- a 2GB DB dump backed up 3x
            f("backups/db-dump-jan.sql", 2 * 1024**3, "etag-dup-1", 200, "application/octet-stream"),
            f("backups/db-dump-jan-copy.sql", 2 * 1024**3, "etag-dup-1", 195, "application/octet-stream"),
            f("backups/db-dump-jan-copy2.sql", 2 * 1024**3, "etag-dup-1", 190, "application/octet-stream"),
            # Large, old, still on Standard -> wrong-tier candidate
            f("archive/2023-access-logs.tar", 500 * 1024**2, "etag-archive-1", 400, "application/octet-stream"),
            # Old and small -> stale but below the wrong-tier size threshold
            f("archive/old-report.pdf", 3 * 1024**2, "etag-archive-2", 150, "application/octet-stream"),
            # Uncompressed logs -> compression candidates
            f("logs/app-2026-06.log", 100 * 1024**2, "etag-log-1", 20, "text/plain"),
            f("logs/app-2026-07.log", 50 * 1024**2, "etag-log-2", 2, "text/plain"),
            # Recently active, nothing wrong with it
            f("app/current-config.json", 2048, "etag-config-1", 1, "application/json"),
        ]

        for file_data in files:
            db.add(FileMetadata(account_id=account.id, bucket_name=account.bucket_name, **file_data))
        db.commit()

        print(f"Seeded cloud account {account.id} ({account.bucket_name}) with {len(files)} files.")
        print(f"Next: POST /cloud-accounts/{account.id}/analyze")

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m app.scripts.seed_test_data <email-you-signed-up-with>")
        sys.exit(1)
    seed(sys.argv[1])
