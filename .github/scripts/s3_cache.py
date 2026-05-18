#!/usr/bin/env python3
"""S3-backed wheel cache — replacement for actions/cache for this project.

Two operations mirroring actions/cache/{restore,save}:

    restore --path DIR --key KEY [--restore-keys KEY1 KEY2 ...]
    save    --path DIR --key KEY

Cache objects live at the root of the bucket, keyed as `<key>.tar.gz`.
Restore tries the exact key first, then each restore-key as a prefix
match (picking the most recently modified object when multiple match).
Misses are silent — the path simply isn't populated.
"""

import argparse
import os
import sys
import tarfile
import tempfile
from pathlib import Path


def s3_client():
    import boto3
    from botocore.config import Config
    endpoint = os.environ["S3_CACHE_ENDPOINT"]
    region = os.environ["S3_CACHE_REGION"]
    access_key = os.environ["S3_CACHE_ACCESS_KEY_ID"]
    secret_key = os.environ["S3_CACHE_SECRET_ACCESS_KEY"]
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(retries={"max_attempts": 10, "mode": "adaptive"}),
    )


def object_key(key: str) -> str:
    return f"{key}.tar.gz"


def head_exists(s3, bucket: str, key: str) -> bool:
    from botocore.exceptions import ClientError
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response.get("Error", {}).get("Code", "") in ("404", "NoSuchKey", "NotFound"):
            return False
        raise


def find_best_match(s3, bucket: str, prefix: str) -> str | None:
    """Return the most-recently-modified object whose key starts with prefix."""
    paginator = s3.get_paginator("list_objects_v2")
    best_key = None
    best_modified = None
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []) or []:
            if best_modified is None or obj["LastModified"] > best_modified:
                best_modified = obj["LastModified"]
                best_key = obj["Key"]
    return best_key


def download_and_extract(s3, bucket: str, key: str, path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        s3.download_file(bucket, key, tmp_path)
        size = os.path.getsize(tmp_path)
        print(f"Downloaded {key} ({size:,} bytes)")
        with tarfile.open(tmp_path, "r:gz") as tf:
            tf.extractall(str(path))
        print(f"Extracted into {path}")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def compress_and_upload(s3, bucket: str, key: str, path: Path) -> None:
    if not path.exists():
        print(f"::warning::cache path {path} does not exist, nothing to save")
        return
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        with tarfile.open(tmp_path, "w:gz", compresslevel=3) as tf:
            tf.add(str(path), arcname=".")
        size = os.path.getsize(tmp_path)
        print(f"Packed {path} -> {tmp_path} ({size:,} bytes)")
        s3.upload_file(
            tmp_path,
            bucket,
            key,
            ExtraArgs={"ContentType": "application/gzip"},
        )
        print(f"Uploaded {key}")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def cmd_restore(args) -> int:
    bucket = os.environ["S3_CACHE_BUCKET"]
    s3 = s3_client()

    exact_key = object_key(args.key)
    if head_exists(s3, bucket, exact_key):
        print(f"Cache HIT (exact): {exact_key}")
        download_and_extract(s3, bucket, exact_key, Path(args.path))
        _set_output("cache-hit", "true")
        _set_output("matched-key", args.key)
        return 0

    print(f"Cache MISS (exact): {exact_key}")
    suffix = ".tar.gz"
    for rk in args.restore_keys or []:
        # restore-key is itself a prefix of valid keys; find any object whose
        # key starts with `<rk>` and ends with the archive suffix.
        matched = find_best_match(s3, bucket, rk)
        if matched and matched.endswith(suffix):
            print(f"Cache HIT (restore-key '{rk}' -> '{matched}')")
            download_and_extract(s3, bucket, matched, Path(args.path))
            _set_output("cache-hit", "false")
            _set_output("matched-key", matched.removesuffix(suffix))
            return 0
        print(f"Cache MISS (restore-key '{rk}')")

    _set_output("cache-hit", "false")
    _set_output("matched-key", "")
    return 0


def cmd_save(args) -> int:
    bucket = os.environ["S3_CACHE_BUCKET"]
    s3 = s3_client()

    exact_key = object_key(args.key)
    if head_exists(s3, bucket, exact_key):
        print(f"Cache already present, skipping save: {exact_key}")
        return 0

    compress_and_upload(s3, bucket, exact_key, Path(args.path))
    return 0


def _set_output(name: str, value: str) -> None:
    out = os.environ.get("GITHUB_OUTPUT")
    if not out:
        return
    with open(out, "a", encoding="utf-8") as f:
        f.write(f"{name}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("restore")
    r.add_argument("--path", required=True)
    r.add_argument("--key", required=True)
    r.add_argument("--restore-keys", nargs="*", default=[])

    s = sub.add_parser("save")
    s.add_argument("--path", required=True)
    s.add_argument("--key", required=True)

    args = parser.parse_args()
    if args.cmd == "restore":
        return cmd_restore(args)
    if args.cmd == "save":
        return cmd_save(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
