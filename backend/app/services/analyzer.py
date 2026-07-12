"""
Pure analysis logic. Every function here takes plain dicts in and returns
plain dicts/lists out -- no DB session, no SQLAlchemy models. That's
deliberate: it means the detection rules can be unit tested with a list of
Python dicts, and the DB-facing orchestration (querying FileMetadata,
writing an OptimizationReport) stays in analysis_service.py, separate from
the logic that actually decides what's wasteful.

Each `file` dict is expected to have:
    file_key, size_bytes, etag_hash, last_modified (datetime),
    content_type, storage_class
"""
from datetime import datetime, timedelta
from collections import defaultdict

from app.services.pricing import monthly_cost_usd, DEFAULT_ARCHIVE_TARGET

STALE_DAYS_THRESHOLD = 90
WRONG_TIER_MIN_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
WRONG_TIER_MIN_AGE_DAYS = 30
COMPRESSIBLE_TYPES = {"text/plain", "text/csv", "application/json"}
COMPRESSED_EXTENSIONS = (".gz", ".zip", ".bz2", ".xz")


def find_duplicates(files: list[dict]) -> list[dict]:
    """Group by etag_hash. Within each group, keep the oldest copy and
    flag every other copy as a duplicate -- oldest is assumed to be the
    'original' in the absence of any other signal."""
    groups = defaultdict(list)
    for f in files:
        if f.get("etag_hash"):
            groups[f["etag_hash"]].append(f)

    duplicates = []
    for group in groups.values():
        if len(group) > 1:
            ordered = sorted(group, key=lambda f: f["last_modified"])
            duplicates.extend(ordered[1:])
    return duplicates


def find_stale(files: list[dict], now: datetime = None, threshold_days: int = STALE_DAYS_THRESHOLD) -> list[dict]:
    now = now or datetime.utcnow()
    cutoff = now - timedelta(days=threshold_days)
    return [f for f in files if f["last_modified"] < cutoff]


def find_wrong_tier(files: list[dict], now: datetime = None) -> list[dict]:
    now = now or datetime.utcnow()
    cutoff = now - timedelta(days=WRONG_TIER_MIN_AGE_DAYS)
    return [
        f for f in files
        if f["storage_class"] == "STANDARD"
        and f["size_bytes"] >= WRONG_TIER_MIN_SIZE_BYTES
        and f["last_modified"] < cutoff
    ]


def find_compression_candidates(files: list[dict]) -> list[dict]:
    return [
        f for f in files
        if f.get("content_type") in COMPRESSIBLE_TYPES
        and not f["file_key"].lower().endswith(COMPRESSED_EXTENSIONS)
    ]


def estimate_monthly_savings(files: list[dict], now: datetime = None) -> dict:
    """Runs every detector and rolls the results up into a single report,
    including a dollar estimate. Compression candidates are flagged but not
    priced -- actual compression ratio depends on content and we'd rather
    under-promise than invent a number."""
    now = now or datetime.utcnow()

    duplicates = find_duplicates(files)
    stale = find_stale(files, now=now)
    wrong_tier = find_wrong_tier(files, now=now)
    compressible = find_compression_candidates(files)

    duplicate_keys = {f["file_key"] for f in duplicates}
    archive_candidate_keys = {f["file_key"] for f in stale} | {f["file_key"] for f in wrong_tier}
    archive_candidate_keys -= duplicate_keys  # don't double-count a file that's both

    current_monthly_cost = sum(monthly_cost_usd(f["size_bytes"], f["storage_class"]) for f in files)

    duplicate_waste = sum(monthly_cost_usd(f["size_bytes"], f["storage_class"]) for f in duplicates)

    archive_savings = 0.0
    files_by_key = {f["file_key"]: f for f in files}
    for key in archive_candidate_keys:
        f = files_by_key[key]
        current = monthly_cost_usd(f["size_bytes"], f["storage_class"])
        archived = monthly_cost_usd(f["size_bytes"], DEFAULT_ARCHIVE_TARGET)
        archive_savings += max(current - archived, 0)

    return {
        "total_files": len(files),
        "current_monthly_cost_usd": round(current_monthly_cost, 4),
        "estimated_monthly_savings_usd": round(duplicate_waste + archive_savings, 4),
        "duplicate_files": len(duplicates),
        "duplicate_waste_usd": round(duplicate_waste, 4),
        "stale_files": len(stale),
        "wrong_tier_files": len(wrong_tier),
        "archive_savings_usd": round(archive_savings, 4),
        "compression_candidates": len(compressible),
        "flagged_keys": {
            "duplicate": sorted(duplicate_keys),
            "archive_candidate": sorted(archive_candidate_keys),
            "compression_candidate": sorted(f["file_key"] for f in compressible),
        },
    }
