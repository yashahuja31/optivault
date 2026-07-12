# Source: AWS S3 pricing page, us-east-1, verified mid-2026.
# These are storage-only rates -- they intentionally ignore request/egress/
# retrieval fees, which matter for a real bill but would make "estimated
# savings" depend on usage patterns we don't have visibility into yet.
STORAGE_CLASS_PRICING_PER_GB_MONTH = {
    "STANDARD": 0.023,
    "STANDARD_IA": 0.0125,
    "GLACIER_IR": 0.004,      # Glacier Instant Retrieval
    "GLACIER": 0.0036,        # Glacier Flexible Retrieval
    "DEEP_ARCHIVE": 0.00099,
}

DEFAULT_ARCHIVE_TARGET = "GLACIER"  # what we recommend moving cold data to


def monthly_cost_usd(size_bytes: int, storage_class: str) -> float:
    gb = size_bytes / (1024 ** 3)
    rate = STORAGE_CLASS_PRICING_PER_GB_MONTH.get(
        storage_class, STORAGE_CLASS_PRICING_PER_GB_MONTH["STANDARD"]
    )
    return gb * rate
