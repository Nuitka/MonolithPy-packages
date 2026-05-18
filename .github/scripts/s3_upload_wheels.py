#!/usr/bin/env python3
"""Upload built_wheels/ to S3 as a single tar.zst snapshot.

Used by each build job to push its wheel directory to a well-known
run-scoped prefix so final-test can download from S3 instead of relying
on GitHub's artifact system (which occasionally truncates large files).
"""

import argparse
import io
import os
import sys
import tarfile
import zstandard
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
        config=Config(retries={"max_attempts": 5, "mode": "standard"}),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path,
                        help="Directory containing .whl files")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--arch", required=True)
    parser.add_argument("--name", required=True,
                        help="Snapshot name, e.g. 'tools', 'deps', 'r2-3'")
    args = parser.parse_args()

    whls = sorted(args.source.glob("*.whl"))
    if not whls:
        print(f"No .whl files in {args.source}, skipping upload.")
        return 0

    # Build tar in memory, then compress in one shot.
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as tf:
        for whl in whls:
            tf.add(whl, arcname=whl.name)
    cctx = zstandard.ZstdCompressor()
    body = cctx.compress(raw.getvalue())

    bucket = os.environ["S3_CACHE_BUCKET"]
    key = f"wheel-snapshots/{args.run_id}/{args.arch}/{args.name}.tar.zst"
    s3 = s3_client()
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
    )
    print(f"Uploaded {len(whls)} wheel(s) to s3://{bucket}/{key} "
          f"({len(body)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
