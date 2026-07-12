from sqlalchemy.orm import Session

from app.models import FileMetadata, OptimizationReport
from app.services.analyzer import estimate_monthly_savings


def run_analysis(db: Session, account_id: str) -> tuple[OptimizationReport, dict]:
    rows = db.query(FileMetadata).filter(FileMetadata.account_id == account_id).all()

    file_dicts = [
        {
            "file_key": r.file_key,
            "size_bytes": r.size_bytes,
            "etag_hash": r.etag_hash,
            "last_modified": r.last_modified,
            "content_type": r.content_type,
            "storage_class": r.storage_class,
        }
        for r in rows
    ]

    result = estimate_monthly_savings(file_dicts)

    rows_by_key = {r.file_key: r for r in rows}
    for key in result["flagged_keys"]["duplicate"]:
        rows_by_key[key].status = "duplicate"
    for key in result["flagged_keys"]["archive_candidate"]:
        rows_by_key[key].status = "archive_candidate"

    summary = (
        f"Scanned {result['total_files']} files, currently ~"
        f"${result['current_monthly_cost_usd']}/month. "
        f"Found {result['duplicate_files']} duplicate files and "
        f"{result['stale_files'] + result['wrong_tier_files']} archive candidates. "
        f"Estimated savings: ${result['estimated_monthly_savings_usd']}/month."
    )

    report = OptimizationReport(
        account_id=account_id,
        total_savings_usd=result["estimated_monthly_savings_usd"],
        summary_text=summary,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return report, result
