from typing import Iterator, Optional
import boto3

from app.config import settings


def _get_s3_client(role_arn: Optional[str] = None):
    """
    Returns a boto3 S3 client.

    - If role_arn is provided, assumes that cross-account role via STS
      (this is the production path: customer grants us a read-only role).
    - Otherwise falls back to the default credential chain, which is what
      local/demo scans against your own bucket will use.
    """
    if role_arn:
        sts = boto3.client("sts")
        creds = sts.assume_role(
            RoleArn=role_arn, RoleSessionName="optivault-scan"
        )["Credentials"]
        return boto3.client(
            "s3",
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
            region_name=settings.aws_default_region,
        )
    return boto3.client("s3", region_name=settings.aws_default_region)


def scan_bucket(bucket_name: str, role_arn: Optional[str] = None) -> Iterator[dict]:
    """
    Paginates through every object in a bucket and yields normalized
    metadata dicts. Never reads object *content* -- only the metadata
    returned by list_objects_v2.
    """
    client = _get_s3_client(role_arn)
    paginator = client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            yield {
                "file_key": obj["Key"],
                "size_bytes": obj["Size"],
                "etag_hash": obj["ETag"].strip('"'),
                "last_modified": obj["LastModified"],
                "storage_class": obj.get("StorageClass", "STANDARD"),
                # content_type isn't returned by list_objects_v2; a real
                # scan would batch head_object calls for a sample, or infer
                # from the key's file extension -- kept simple for now.
                "content_type": _guess_content_type(obj["Key"]),
            }


def _guess_content_type(key: str) -> str:
    ext = key.rsplit(".", 1)[-1].lower() if "." in key else ""
    return {
        "log": "text/plain",
        "txt": "text/plain",
        "csv": "text/csv",
        "json": "application/json",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "mp4": "video/mp4",
        "gz": "application/gzip",
        "zip": "application/zip",
    }.get(ext, "application/octet-stream")
