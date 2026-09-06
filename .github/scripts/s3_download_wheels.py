#!/usr/bin/env python3
"""Download all built wheels for a run from S3 into a local directory.

Each build job uploads its built_wheels/ to:
    s3://<bucket>/run-wheels/<run_id>/<arch>/<tier-or-split>.tar.zst

This script lists all objects under that prefix, downloads each archive,
and extracts every .whl into the output directory.  Duplicate wheel
filenames (same package built in different tiers) are harmless — the
last one extracted wins.
"""

import argparse
import io
import os
import sys
import tarfile
import zstandard
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s3_retry  # noqa: E402


def s3_client():
    import boto3
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
        config=s3_retry.client_config(),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--arch", required=True,
                        help="e.g. 'arm64' or 'x86_64'")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    bucket = os.environ["S3_CACHE_BUCKET"]
    prefix = f"wheel-snapshots/{args.run_id}/{args.arch}/"
    s3 = s3_client()

    print(f"Listing s3://{bucket}/{prefix} ...")
    def list_keys():
        paginator = s3.get_paginator("list_objects_v2")
        found = []
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                found.append(obj["Key"])
        return found

    keys = s3_retry.retry(list_keys, what=f"list {prefix}")

    if not keys:
        print(f"::error::No wheel snapshots found under s3://{bucket}/{prefix}",
              file=sys.stderr)
        return 1

    print(f"Found {len(keys)} snapshot(s)")
    args.output.mkdir(parents=True, exist_ok=True)

    for key in keys:
        name = key.rsplit("/", 1)[-1]
        print(f"  downloading {name} ...")
        body = s3_retry.get_bytes(s3, bucket, key)  # retried + length-verified
        print(f"    {len(body)} bytes")

        dctx = zstandard.ZstdDecompressor()
        with dctx.stream_reader(io.BytesIO(body)) as reader:
            with tarfile.open(fileobj=reader, mode="r|") as tf:
                for member in tf:
                    if member.name.endswith(".whl"):
                        dest = args.output / Path(member.name).name
                        fobj = tf.extractfile(member)
                        if fobj is None:
                            continue
                        with open(dest, "wb") as out:
                            out.write(fobj.read())
                        print(f"    extracted {dest.name} ({member.size} bytes)")

    whl_count = len(list(args.output.glob("*.whl")))
    print(f"\nTotal: {whl_count} wheel(s) in {args.output}")
    if s3_retry.retry_count():
        print(f"::warning::S3 was flaky: {s3_retry.retry_count()} operation(s) had to be retried")
    return 0


if __name__ == "__main__":
    sys.exit(main())
