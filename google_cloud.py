"""
Google Cloud utilities for file uploads and URL generation.

This module centralizes interactions with Google Cloud Storage (GCS) so
pipeline steps can remain clean. It supports making objects public or
generating time-limited signed URLs.

Configuration via environment variables (optional):
- `GCS_BUCKET` or `GCS_BUCKET_NAME`: default target bucket name.
- `GCS_MAKE_PUBLIC`: 'true'/'false' to make uploaded objects public (default: false).
- `GCS_SIGN_URL`: 'true'/'false' to return a signed URL if not public (default: false).
- `GCS_URL_BASE`: optional custom base like 'https://storage.googleapis.com'.

Credentials: relies on Application Default Credentials or a service account.
Do not commit keys; configure locally via env or gcloud.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache


def _bool_env(var: str, default: bool) -> bool:
    val = os.getenv(var)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


def _safe_import_storage():
    try:
        from google.cloud import storage  # type: ignore

        return storage
    except Exception as e:  # pragma: no cover - import-time error surfaced at runtime
        raise RuntimeError(
            "google-cloud-storage is required. Add it to requirements and install."
        ) from e


def _find_service_account_file() -> Optional[Path]:
    """Find a service account JSON file to use by default.

    Precedence:
    1) `GCP_SERVICE_ACCOUNT_FILE` env var
    2) `GOOGLE_APPLICATION_CREDENTIALS` env var
    3) `./service-account.json` (cwd)
    4) `<repo>/service-account.json` (same dir as this module)
    """
    candidates = []

    env1 = os.getenv("GCP_SERVICE_ACCOUNT_FILE")
    if env1:
        candidates.append(Path(env1))

    env2 = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if env2:
        candidates.append(Path(env2))

    candidates.append(Path.cwd() / "service-account.json")
    candidates.append(Path(__file__).resolve().parent / "service-account.json")

    for p in candidates:
        try:
            if p and Path(p).exists():
                return Path(p)
        except Exception:
            continue
    return None


@lru_cache(maxsize=1)
def _get_storage_client():
    """Return a configured Storage client, preferring a local service account JSON.

    Falls back to Application Default Credentials if no JSON is found.
    """
    storage = _safe_import_storage()

    sa_path = _find_service_account_file()
    if sa_path is not None:
        try:
            from google.oauth2 import service_account  # type: ignore

            scopes = [
                "https://www.googleapis.com/auth/devstorage.read_write",
                # "https://www.googleapis.com/auth/cloud-platform",  # optional broader scope
            ]
            creds = service_account.Credentials.from_service_account_file(
                str(sa_path), scopes=scopes
            )
            project = getattr(creds, "project_id", None)
            return storage.Client(project=project, credentials=creds)
        except Exception as e:
            # Fallback to ADC if SA load fails
            print(f"Warning: failed to load service account from {sa_path}: {e}")

    # Default: ADC
    return storage.Client()


def upload_to_gcs(
    local_path: str | Path,
    *,
    bucket_name: Optional[str] = None,
    blob_path: Optional[str] = None,
    content_type: Optional[str] = None,
    make_public: Optional[bool] = None,
    sign_url: Optional[bool] = None,
    signed_url_expiration_seconds: int = 7 * 24 * 3600,
    cache_control: Optional[str] = None,
) -> str:
    """Upload a file to GCS and return an accessible URL.

    - If `make_public` is True (default), the object is made public-read and
      a public URL is returned.
    - Else if `sign_url` is True, returns a V4 signed URL with the given
      expiration.
    - Else returns the canonical HTTPS URL (may require IAM to access).
    """
    storage = _safe_import_storage()

    lp = Path(local_path)
    if not lp.exists():
        raise FileNotFoundError(f"Local file not found: {lp}")

    bucket_default = os.getenv("GCS_BUCKET") or os.getenv("GCS_BUCKET_NAME") or "bda_auto_pdf_reports"
    bucket = bucket_name or bucket_default
    if not bucket:
        raise ValueError("GCS bucket name not provided. Set GCS_BUCKET or pass bucket_name.")

    # Resolve blob path
    blob_name = blob_path or lp.name

    client = _get_storage_client()
    bucket_ref = client.bucket(bucket)
    blob = bucket_ref.blob(blob_name)

    # Infer content type if not provided
    ct = content_type
    if ct is None:
        if lp.suffix.lower() == ".pdf":
            ct = "application/pdf"
        else:
            ct = "application/octet-stream"

    # Upload
    blob.cache_control = cache_control or "public, max-age=3600"
    blob.upload_from_filename(str(lp), content_type=ct)

    # Determine URL strategy
    # Default behavior: do NOT call make_public; rely on bucket-level policy.
    make_public = _bool_env("GCS_MAKE_PUBLIC", False) if make_public is None else make_public
    sign_url = _bool_env("GCS_SIGN_URL", False) if sign_url is None else sign_url

    if make_public:
        try:
            blob.make_public()
        except Exception as e:
            # Uniform bucket-level access disables object ACLs; proceed but warn.
            print(f"Warning: make_public failed for {blob_name}: {e}")
        # Prefer a custom domain if provided, else fall back to GCS URL base
        public_base = os.getenv("PUBLIC_URL_BASE") or os.getenv("GCS_URL_BASE")
        if public_base:
            return f"{public_base.rstrip('/')}/{blob_name}"
        base = "https://storage.googleapis.com"
        return f"{base.rstrip('/')}/{bucket}/{blob_name}"

    if sign_url:
        from datetime import timedelta

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=signed_url_expiration_seconds),
            method="GET",
        )
        return url

    # Default: return deterministic public URL assuming bucket policy grants public access.
    # Prefer custom/public base if provided even without object ACLs.
    public_base = os.getenv("PUBLIC_URL_BASE") or os.getenv("GCS_URL_BASE")
    if public_base:
        base = public_base.rstrip('/')
        if "storage.googleapis.com" in base:
            return f"{base}/{bucket}/{blob_name}"
        return f"{base}/{blob_name}"
    return f"https://storage.googleapis.com/{bucket}/{blob_name}"
