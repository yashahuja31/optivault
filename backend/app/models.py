import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, BigInteger, Float, ForeignKey, DateTime, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    cloud_accounts = relationship("CloudAccount", back_populates="owner")


class CloudAccount(Base):
    __tablename__ = "cloud_accounts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    provider = Column(String, default="aws")  # aws | gcp | azure (future)
    bucket_name = Column(String, nullable=False)
    role_arn = Column(String, nullable=True)  # preferred: cross-account IAM role
    # NOTE: never store long-lived access keys in prod; this field exists only
    # so local/demo scans work without a real cross-account trust relationship.
    access_key_ref = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="cloud_accounts")


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    account_id = Column(UUID(as_uuid=False), ForeignKey("cloud_accounts.id"), nullable=False)
    celery_task_id = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending | running | completed | failed
    objects_scanned = Column(BigInteger, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class FileMetadata(Base):
    __tablename__ = "file_metadata"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    account_id = Column(UUID(as_uuid=False), ForeignKey("cloud_accounts.id"), nullable=False)
    bucket_name = Column(String, nullable=False)
    file_key = Column(Text, nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    etag_hash = Column(String, index=True)
    last_modified = Column(DateTime, nullable=False)
    content_type = Column(String, nullable=True)
    storage_class = Column(String, default="STANDARD")
    status = Column(String, default="active")  # active | duplicate | archive_candidate
    predicted_access_score = Column(Float, nullable=True)
    indexed_at = Column(DateTime, default=datetime.utcnow)


class OptimizationManifest(Base):
    __tablename__ = "optimization_manifests"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    account_id = Column(UUID(as_uuid=False), ForeignKey("cloud_accounts.id"), nullable=False)
    type = Column(String, nullable=False)  # move_to_glacier | delete_duplicate | compress
    payload = Column(JSON, nullable=False)  # list of {file_key, action, ...}
    status = Column(String, default="pending")  # pending | executed | failed
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)


class OptimizationReport(Base):
    __tablename__ = "optimization_reports"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    account_id = Column(UUID(as_uuid=False), ForeignKey("cloud_accounts.id"), nullable=False)
    total_savings_usd = Column(Float, default=0.0)
    summary_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
