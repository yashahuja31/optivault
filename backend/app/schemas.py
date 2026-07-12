from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# --- Auth ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Cloud Account ---
class CloudAccountCreate(BaseModel):
    provider: str = "aws"
    bucket_name: str
    role_arn: Optional[str] = None
    access_key_ref: Optional[str] = None


class CloudAccountOut(BaseModel):
    id: str
    provider: str
    bucket_name: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Scan ---
class ScanJobOut(BaseModel):
    id: str
    account_id: str
    status: str
    objects_scanned: int
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class FileMetadataOut(BaseModel):
    file_key: str
    size_bytes: int
    etag_hash: Optional[str]
    last_modified: datetime
    content_type: Optional[str]
    storage_class: str
    status: str

    class Config:
        from_attributes = True


# --- Analysis ---
class AnalysisResultOut(BaseModel):
    total_files: int
    current_monthly_cost_usd: float
    estimated_monthly_savings_usd: float
    duplicate_files: int
    duplicate_waste_usd: float
    stale_files: int
    wrong_tier_files: int
    archive_savings_usd: float
    compression_candidates: int


class OptimizationReportOut(BaseModel):
    id: str
    total_savings_usd: float
    summary_text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
