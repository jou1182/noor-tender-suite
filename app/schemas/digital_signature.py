"""
Digital Signature & Certified Stamping — Pydantic schemas.

Typed contracts for signature requests, certified document metadata,
signature validation reports, and public QR verification payloads.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SignatureRequest(BaseModel):
    """Request to stamp + cryptographically sign a proposal PDF."""

    document_id: str = ""
    pdf_path: str = ""
    signer_name: str = ""
    signer_title: str = ""
    certificate_path: Optional[str] = None
    verification_base_url: str = "http://localhost:8000/api/v1/public/verify"
    stamp_fields: Dict[str, str] = Field(default_factory=dict)  # overlay text fields


class CertifiedDocumentMetadata(BaseModel):
    """Metadata recorded for a certified signed document."""

    document_id: str = ""
    sha256_hash: str = ""
    signer_name: str = ""
    signed_at: str = ""
    signature_field: str = ""
    qr_content: str = ""
    sbc_clearance: bool = False
    storage_path: str = ""


class SignatureValidationReport(BaseModel):
    """Result of validating a signed PDF's cryptographic integrity."""

    document_id: str = ""
    valid: bool = False
    signer_credentials: str = ""
    signing_timestamp: str = ""
    docmdp_permissions: str = ""
    integrity_message: str = ""
    sbc_clearance_status: str = "UNKNOWN"  # CLEARED | NOT_CLEARED | UNKNOWN


class QRVerificationPayload(BaseModel):
    """Payload encoded into the QR stamp on certified documents."""

    document_id: str
    verification_url: str
    sha256_hash: str
    issued_at: str = ""
