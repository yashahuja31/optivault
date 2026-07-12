from datetime import datetime

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import CloudAccount, ScanJob, FileMetadata
from app.services.scanner import scan_bucket

BATCH_SIZE = 500


@celery_app.task(bind=True)
def run_scan_task(self, scan_job_id: str, account_id: str):
    db = SessionLocal()
    try:
        job = db.query(ScanJob).filter(ScanJob.id == scan_job_id).first()
        account = db.query(CloudAccount).filter(CloudAccount.id == account_id).first()

        if not job or not account:
            return

        job.status = "running"
        job.celery_task_id = self.request.id
        db.commit()

        # Clear any previous scan results for this account before re-indexing.
        db.query(FileMetadata).filter(FileMetadata.account_id == account_id).delete()

        batch = []
        count = 0
        for obj in scan_bucket(account.bucket_name, account.role_arn):
            batch.append(
                FileMetadata(
                    account_id=account_id,
                    bucket_name=account.bucket_name,
                    **obj,
                )
            )
            count += 1
            if len(batch) >= BATCH_SIZE:
                db.bulk_save_objects(batch)
                db.commit()
                batch.clear()
                job.objects_scanned = count
                db.commit()

        if batch:
            db.bulk_save_objects(batch)

        job.status = "completed"
        job.objects_scanned = count
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as exc:  # noqa: BLE001
        db.rollback()
        job = db.query(ScanJob).filter(ScanJob.id == scan_job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(exc)
            db.commit()
        raise
    finally:
        db.close()
