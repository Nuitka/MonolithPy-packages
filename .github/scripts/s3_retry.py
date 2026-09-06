#!/usr/bin/env python3
"""Retry + verification layer for the CI's S3-compatible object store (Backblaze B2).

B2 is expected to be flaky: it periodically answers 500 "InternalError: internal
incident" / 503 SlowDown for minutes at a time, and a multipart upload that hits
that on a single UploadPart surfaces from boto3 as S3UploadFailedError once
botocore's own (short, ~1-2 min) retry budget is exhausted. Every transfer the CI
does against B2 therefore goes through here:

  * botocore-level retries stay on (adaptive, 10 attempts) for sub-second blips;
  * on top of that, `retry()` re-runs the WHOLE operation with exponential
    backoff + jitter (default 12 attempts, 5s -> 300s cap, ~35 min worst case)
    for anything that looks transient -- 5xx / throttling responses, connection
    resets, timeouts, truncated bodies, and boto3 transfer failures wrapping
    those. Definite client errors (AccessDenied, NoSuchBucket, bad credentials,
    missing local file, ...) fail immediately;
  * uploads and downloads are verified against the object's ContentLength, so a
    silently truncated transfer is retried instead of being reported as success;
  * multipart transfers use 64 MB parts and 4 concurrent connections per file:
    fewer requests that can fail, and no connection-pool thrash when several
    files upload in parallel.

Tunables (env): S3_RETRY_ATTEMPTS (12), S3_RETRY_BASE_DELAY (5 s),
S3_RETRY_MAX_DELAY (300 s).
"""

import http.client
import os
import random
import socket
import sys
import time
from pathlib import Path

__all__ = [
    "VerificationError",
    "client_config",
    "download_file",
    "get_bytes",
    "is_transient",
    "put_bytes",
    "retry",
    "retry_count",
    "transfer_config",
    "upload_file",
]

_MB = 1024 * 1024

# S3 error codes we treat as "the service is having a moment".
_TRANSIENT_CODES = {
    "InternalError", "InternalServerError", "ServiceUnavailable", "SlowDown",
    "Throttling", "ThrottlingException", "RequestLimitExceeded", "TooManyRequests",
    "RequestTimeout", "RequestTimeoutException", "OperationAborted",
    "408", "429", "500", "502", "503", "504",
}
# ... and those that will never succeed however long we wait.
_FATAL_CODES = {
    "AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch", "ExpiredToken",
    "InvalidToken", "NoSuchBucket", "NoSuchKey", "NoSuchUpload", "InvalidRequest",
    "InvalidArgument", "MalformedXML", "EntityTooLarge", "EntityTooSmall",
    "MethodNotAllowed", "301", "400", "403", "404", "405",
}

_retries_performed = 0


class VerificationError(Exception):
    """A transfer completed but the object on the server does not match."""


def retry_count() -> int:
    """Number of retries performed so far in this process (for summaries)."""
    return _retries_performed


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        print(f"[s3-retry] ignoring invalid {name}={raw!r}", file=sys.stderr, flush=True)
        return default


def _unwrap(exc: BaseException):
    """Return the exception boto3's transfer layer wrapped, if any."""
    inner = getattr(exc, "last_exception", None)
    if isinstance(inner, BaseException) and inner is not exc:
        return inner
    for attr in ("__cause__", "__context__"):
        inner = getattr(exc, attr, None)
        if isinstance(inner, BaseException) and inner is not exc:
            return inner
    return None


def is_transient(exc: BaseException) -> bool:
    """Decide whether `exc` is worth retrying against a flaky object store."""
    import botocore.exceptions as be
    import boto3.exceptions as b3e

    if isinstance(exc, VerificationError):
        return True

    if isinstance(exc, be.ClientError):
        error = exc.response.get("Error", {}) if isinstance(exc.response, dict) else {}
        code = str(error.get("Code", ""))
        status = (exc.response.get("ResponseMetadata", {}) or {}).get("HTTPStatusCode")
        if code in _FATAL_CODES:
            return False
        if code in _TRANSIENT_CODES:
            return True
        if isinstance(status, int):
            return status >= 500 or status in (408, 429)
        return False

    # boto3's high-level transfer API wraps the real error: look through it.
    wrapper_types = tuple(
        t for t in (
            getattr(b3e, "S3UploadFailedError", None),
            getattr(b3e, "S3TransferFailedError", None),
            getattr(b3e, "RetriesExceededError", None),
        ) if t is not None
    )
    if wrapper_types and isinstance(exc, wrapper_types):
        inner = _unwrap(exc)
        if inner is not None:
            return is_transient(inner)
        msg = str(exc)
        return not any(code in msg for code in _FATAL_CODES if code.isalpha())

    # Things that are wrong with us, not with the service.
    fatal_types = tuple(
        t for t in (
            getattr(be, "NoCredentialsError", None),
            getattr(be, "PartialCredentialsError", None),
            getattr(be, "ParamValidationError", None),
            getattr(be, "UnknownServiceError", None),
        ) if t is not None
    )
    if fatal_types and isinstance(exc, fatal_types):
        return False
    if isinstance(exc, (FileNotFoundError, PermissionError, IsADirectoryError)):
        return False

    # Network-level trouble.
    network_types = tuple(
        t for t in (
            getattr(be, "ConnectionError", None),        # Endpoint/SSL/ConnectionClosed/Proxy/ConnectTimeout
            getattr(be, "HTTPClientError", None),        # ReadTimeout, ResponseStreamingError
            getattr(be, "IncompleteReadError", None),
            getattr(be, "ReadTimeoutError", None),
            getattr(be, "ConnectTimeoutError", None),
        ) if t is not None
    )
    if network_types and isinstance(exc, network_types):
        return True
    if isinstance(exc, (ConnectionError, TimeoutError, socket.timeout, http.client.IncompleteRead)):
        return True
    try:
        import urllib3.exceptions as u3e
        if isinstance(exc, (u3e.ProtocolError, u3e.TimeoutError, u3e.IncompleteRead)):
            return True
    except Exception:  # pragma: no cover - urllib3 always ships with botocore
        pass

    return False


def retry(fn, *, what: str, attempts: int = None, base_delay: float = None,
          max_delay: float = None):
    """Run `fn()`; on a transient failure sleep (exp. backoff + jitter) and retry.

    Re-raises the last error once `attempts` are exhausted, and re-raises
    immediately for anything `is_transient()` rejects.
    """
    global _retries_performed
    attempts = int(attempts if attempts is not None else _env_float("S3_RETRY_ATTEMPTS", 12))
    base_delay = base_delay if base_delay is not None else _env_float("S3_RETRY_BASE_DELAY", 5.0)
    max_delay = max_delay if max_delay is not None else _env_float("S3_RETRY_MAX_DELAY", 300.0)
    attempts = max(1, attempts)

    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - classified below
            if attempt >= attempts or not is_transient(exc):
                if attempt > 1:
                    print(f"[s3-retry] {what}: giving up after {attempt} attempts "
                          f"({type(exc).__name__}: {str(exc)[:300]})", flush=True)
                raise
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay *= random.uniform(0.5, 1.0)
            _retries_performed += 1
            print(f"[s3-retry] {what}: attempt {attempt}/{attempts} failed with "
                  f"{type(exc).__name__}: {str(exc)[:300]} -- retrying in {delay:.0f}s",
                  flush=True)
            time.sleep(delay)
    raise AssertionError("unreachable")  # pragma: no cover


def client_config():
    """botocore Config shared by every CI S3 client."""
    from botocore.config import Config
    return Config(
        retries={"max_attempts": 10, "mode": "adaptive"},
        connect_timeout=30,
        read_timeout=120,
        max_pool_connections=64,
    )


def transfer_config():
    """TransferConfig for upload_file/download_file: big parts, modest fan-out."""
    from boto3.s3.transfer import TransferConfig
    return TransferConfig(
        multipart_threshold=64 * _MB,
        multipart_chunksize=64 * _MB,
        max_concurrency=4,
        use_threads=True,
    )


def _head(s3, bucket: str, key: str, what: str) -> dict:
    # A verification HEAD that fails transiently must NOT cost us a re-upload,
    # so it gets its own (short) retry budget inside the outer attempt.
    return retry(lambda: s3.head_object(Bucket=bucket, Key=key),
                 what=f"{what} (verify HEAD)", attempts=6)


def upload_file(s3, bucket: str, key: str, path, *, extra_args: dict = None,
                what: str = None) -> int:
    """Upload a local file (multipart when large) and verify its size on the server.

    Returns the byte count uploaded.
    """
    path = Path(path)
    size = path.stat().st_size  # missing file -> FileNotFoundError now, not mid-retry
    what = what or f"upload {key}"

    def attempt():
        s3.upload_file(str(path), bucket, key, ExtraArgs=extra_args or {},
                       Config=transfer_config())
        got = _head(s3, bucket, key, what).get("ContentLength")
        if got != size:
            raise VerificationError(f"{key}: server has {got} bytes, expected {size}")

    retry(attempt, what=what)
    return size


def put_bytes(s3, bucket: str, key: str, body: bytes, *, content_type: str = None,
              what: str = None) -> int:
    """put_object for small in-memory payloads, verified by size."""
    what = what or f"put {key}"
    kwargs = {"Bucket": bucket, "Key": key, "Body": body}
    if content_type:
        kwargs["ContentType"] = content_type

    def attempt():
        s3.put_object(**kwargs)
        got = _head(s3, bucket, key, what).get("ContentLength")
        if got != len(body):
            raise VerificationError(f"{key}: server has {got} bytes, expected {len(body)}")

    retry(attempt, what=what)
    return len(body)


def get_bytes(s3, bucket: str, key: str, *, what: str = None) -> bytes:
    """get_object fully into memory, verified against ContentLength."""
    what = what or f"get {key}"

    def attempt():
        resp = s3.get_object(Bucket=bucket, Key=key)
        expected = resp.get("ContentLength")
        body = resp["Body"].read()
        if expected is not None and len(body) != expected:
            raise VerificationError(f"{key}: read {len(body)} bytes, expected {expected}")
        return body

    return retry(attempt, what=what)


def download_file(s3, bucket: str, key: str, path, *, what: str = None) -> int:
    """download_file to `path` (written via a temp name), verified by size."""
    path = Path(path)
    what = what or f"download {key}"
    tmp = path.with_name(path.name + ".part")

    def attempt():
        expected = _head(s3, bucket, key, what).get("ContentLength")
        if tmp.exists():
            tmp.unlink()
        s3.download_file(bucket, key, str(tmp), Config=transfer_config())
        got = tmp.stat().st_size
        if expected is not None and got != expected:
            raise VerificationError(f"{key}: downloaded {got} bytes, expected {expected}")
        os.replace(tmp, path)
        return got

    try:
        return retry(attempt, what=what)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
