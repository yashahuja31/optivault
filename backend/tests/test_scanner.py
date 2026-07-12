import boto3
from moto import mock_aws

from app.services.scanner import scan_bucket

TEST_BUCKET = "optivault-test-bucket"


@mock_aws
def test_scan_bucket_returns_normalized_metadata():
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket=TEST_BUCKET)

    client.put_object(Bucket=TEST_BUCKET, Key="logs/app.log", Body=b"log line one")
    client.put_object(Bucket=TEST_BUCKET, Key="images/photo.png", Body=b"\x89PNG fake bytes")

    results = list(scan_bucket(TEST_BUCKET))

    assert len(results) == 2

    keys = {r["file_key"] for r in results}
    assert keys == {"logs/app.log", "images/photo.png"}

    log_entry = next(r for r in results if r["file_key"] == "logs/app.log")
    assert log_entry["content_type"] == "text/plain"
    assert log_entry["size_bytes"] == len(b"log line one")
    assert log_entry["etag_hash"]  # ETag should be present and unquoted

    png_entry = next(r for r in results if r["file_key"] == "images/photo.png")
    assert png_entry["content_type"] == "image/png"


@mock_aws
def test_scan_bucket_detects_duplicate_etags():
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket=TEST_BUCKET)

    # Identical content -> identical ETag -> this is what the Analyzer
    # will later group as a duplicate.
    client.put_object(Bucket=TEST_BUCKET, Key="a/copy1.csv", Body=b"same,data,here")
    client.put_object(Bucket=TEST_BUCKET, Key="a/copy2.csv", Body=b"same,data,here")
    client.put_object(Bucket=TEST_BUCKET, Key="a/different.csv", Body=b"totally,different")

    results = list(scan_bucket(TEST_BUCKET))
    etags = [r["etag_hash"] for r in results]

    assert len(etags) == 3
    assert len(set(etags)) == 2  # two unique etags -> one duplicate pair
