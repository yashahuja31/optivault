import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CloudAccount, ScanJob, FileMetadata, OptimizationReport, User
from app.schemas import (
    CloudAccountCreate, CloudAccountOut, ScanJobOut, FileMetadataOut,
    AnalysisResultOut, OptimizationReportOut,
)
from app.routers.auth import get_current_user
from app.tasks.scan_tasks import run_scan_task
from app.services.analysis_service import run_analysis

router = APIRouter(prefix="/cloud-accounts", tags=["cloud-accounts"])


@router.post("", response_model=CloudAccountOut, status_code=201)
def create_cloud_account(
    payload: CloudAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = CloudAccount(user_id=current_user.id, **payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("", response_model=list[CloudAccountOut])
def list_cloud_accounts(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return db.query(CloudAccount).filter(CloudAccount.user_id == current_user.id).all()


def _get_owned_account(account_id: str, db: Session, current_user: User) -> CloudAccount:
    account = (
        db.query(CloudAccount)
        .filter(CloudAccount.id == account_id, CloudAccount.user_id == current_user.id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    return account


@router.post("/{account_id}/scan", response_model=ScanJobOut, status_code=202)
def start_scan(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = _get_owned_account(account_id, db, current_user)

    job = ScanJob(id=str(uuid.uuid4()), account_id=account.id, status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)

    run_scan_task.delay(job.id, account.id)
    return job


@router.get("/{account_id}/scan-status", response_model=ScanJobOut)
def scan_status(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_account(account_id, db, current_user)
    job = (
        db.query(ScanJob)
        .filter(ScanJob.account_id == account_id)
        .order_by(ScanJob.created_at.desc())
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="No scan jobs found for this account")
    return job


@router.get("/{account_id}/files", response_model=list[FileMetadataOut])
def list_files(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 100,
):
    _get_owned_account(account_id, db, current_user)
    return (
        db.query(FileMetadata)
        .filter(FileMetadata.account_id == account_id)
        .limit(limit)
        .all()
    )


@router.post("/{account_id}/analyze", response_model=AnalysisResultOut)
def analyze_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_account(account_id, db, current_user)
    _, result = run_analysis(db, account_id)
    return result


@router.get("/{account_id}/report", response_model=OptimizationReportOut)
def get_latest_report(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_account(account_id, db, current_user)
    report = (
        db.query(OptimizationReport)
        .filter(OptimizationReport.account_id == account_id)
        .order_by(OptimizationReport.created_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="No report yet -- run /analyze first")
    return report
