from datetime import datetime, timedelta

from app.services.analyzer import (
    find_duplicates,
    find_stale,
    find_wrong_tier,
    find_compression_candidates,
    estimate_monthly_savings,
)

NOW = datetime(2026, 7, 12)


def make_file(key, size_bytes=1000, etag="etag1", days_old=1,
              content_type="application/octet-stream", storage_class="STANDARD"):
    return dict(
        file_key=key,
        size_bytes=size_bytes,
        etag_hash=etag,
        last_modified=NOW - timedelta(days=days_old),
        content_type=content_type,
        storage_class=storage_class,
    )


def test_find_duplicates_keeps_oldest_flags_rest():
    files = [
        make_file("a/copy1.bin", etag="dup", days_old=10),  # older -> kept
        make_file("a/copy2.bin", etag="dup", days_old=5),   # newer -> flagged
        make_file("a/unique.bin", etag="solo", days_old=5),
    ]
    dupes = find_duplicates(files)
    assert {f["file_key"] for f in dupes} == {"a/copy2.bin"}


def test_find_duplicates_ignores_files_without_etag():
    files = [make_file("a.bin", etag=None), make_file("b.bin", etag=None)]
    assert find_duplicates(files) == []


def test_find_stale_respects_threshold():
    files = [make_file("old.bin", days_old=200), make_file("new.bin", days_old=5)]
    stale = find_stale(files, now=NOW, threshold_days=90)
    assert {f["file_key"] for f in stale} == {"old.bin"}


def test_find_wrong_tier_requires_size_age_and_standard_class():
    files = [
        make_file("big-old-standard.bin", size_bytes=200 * 1024 * 1024, days_old=60, storage_class="STANDARD"),
        make_file("small-old-standard.bin", size_bytes=1024, days_old=60, storage_class="STANDARD"),
        make_file("big-old-glacier.bin", size_bytes=200 * 1024 * 1024, days_old=60, storage_class="GLACIER"),
        make_file("big-new-standard.bin", size_bytes=200 * 1024 * 1024, days_old=5, storage_class="STANDARD"),
    ]
    flagged = find_wrong_tier(files, now=NOW)
    assert {f["file_key"] for f in flagged} == {"big-old-standard.bin"}


def test_find_compression_candidates_skips_already_compressed():
    files = [
        make_file("data.csv", content_type="text/csv"),
        make_file("data.csv.gz", content_type="text/csv"),  # already compressed
        make_file("image.png", content_type="image/png"),
    ]
    flagged = find_compression_candidates(files)
    assert {f["file_key"] for f in flagged} == {"data.csv"}


def test_estimate_monthly_savings_end_to_end():
    files = [
        make_file("dup1.bin", etag="d", size_bytes=1024**3, days_old=10, storage_class="STANDARD"),
        make_file("dup2.bin", etag="d", size_bytes=1024**3, days_old=5, storage_class="STANDARD"),
        make_file("stale.bin", etag="s", size_bytes=1024**3, days_old=200, storage_class="STANDARD"),
    ]
    result = estimate_monthly_savings(files, now=NOW)

    assert result["total_files"] == 3
    assert result["duplicate_files"] == 1
    assert result["stale_files"] == 1
    assert result["archive_candidates"] == 1
    assert result["estimated_monthly_savings_usd"] > 0
    # dup2 (the newer copy) is the one flagged, not dup1
    assert result["flagged_keys"]["duplicate"] == ["dup2.bin"]
    assert result["flagged_keys"]["archive_candidate"] == ["stale.bin"]


def test_archive_candidates_does_not_double_count_stale_and_wrong_tier_overlap():
    # A file that is BOTH stale (>90 days) AND wrong-tier (big, old, Standard)
    # must only be counted once in archive_candidates -- this is the bug
    # that was previously inflating the summary text ("9 archive candidates"
    # out of 8 total files).
    files = [
        make_file("big-old.bin", size_bytes=200 * 1024 * 1024, days_old=200,
                   etag="unique1", storage_class="STANDARD"),
    ]
    result = estimate_monthly_savings(files, now=NOW)

    assert result["stale_files"] == 1
    assert result["wrong_tier_files"] == 1
    assert result["archive_candidates"] == 1  # not 2


def test_estimate_monthly_savings_handles_empty_bucket():
    result = estimate_monthly_savings([], now=NOW)
    assert result["total_files"] == 0
    assert result["estimated_monthly_savings_usd"] == 0
