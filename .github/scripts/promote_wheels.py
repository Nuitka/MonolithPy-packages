#!/usr/bin/env python3
"""Promote a staged CI run from `builds/<run>/` to `main/`.

Refuses to run unless `builds/<full>/MANIFEST.json` is present — this guards
against promoting a partial upload.  Uses server-side CopyObject, so no wheel
bytes transit the runner.  Overwrites any existing keys in `main/` (by design:
`main/` is a latest-known-good snapshot, not an archive).
"""

import argparse
import datetime
import json
import os
import sys

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


def make_s3_client():
    endpoint = os.environ["S3_ENDPOINT"]
    region = os.environ["S3_REGION"]
    access_key = os.environ["S3_ACCESS_KEY_ID"]
    secret_key = os.environ["S3_SECRET_ACCESS_KEY"]
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(retries={"max_attempts": 10, "mode": "adaptive"}),
    )


def resolve_source_prefix(s3, bucket: str, source_run: str) -> str:
    if "-" in source_run and len(source_run.split("-", 1)[1]) >= 4:
        candidate = f"builds/{source_run}/"
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=candidate, MaxKeys=1)
        if resp.get("KeyCount", 0) > 0:
            return candidate.rstrip("/")

    paginator = s3.get_paginator("list_objects_v2")
    matches = set()
    for page in paginator.paginate(
        Bucket=bucket, Prefix="builds/", Delimiter="/"
    ):
        for cp in page.get("CommonPrefixes", []) or []:
            p = cp["Prefix"].rstrip("/")
            folder = p.rsplit("/", 1)[-1]
            if folder == source_run or folder.startswith(f"{source_run}-"):
                matches.add(p)

    if not matches:
        raise SystemExit(
            f"::error::No builds/ folder matches source_run={source_run!r}"
        )
    if len(matches) > 1:
        raise SystemExit(
            f"::error::Ambiguous source_run={source_run!r}, matches: "
            f"{sorted(matches)}"
        )
    return matches.pop()


def load_manifest(s3, bucket: str, prefix: str) -> dict:
    key = f"{prefix}/MANIFEST.json"
    try:
        resp = s3.get_object(Bucket=bucket, Key=key)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("NoSuchKey", "404"):
            raise SystemExit(
                f"::error::MANIFEST.json missing at {key} — upload was partial "
                f"or the run folder does not exist"
            )
        raise
    return json.loads(resp["Body"].read())


def list_keys(s3, bucket: str, prefix: str) -> list[str]:
    paginator = s3.get_paginator("list_objects_v2")
    keys: list[str] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=f"{prefix}/"):
        for obj in page.get("Contents", []) or []:
            keys.append(obj["Key"])
    return keys


def copy_object(s3, bucket: str, src_key: str, dst_key: str) -> None:
    s3.copy_object(
        Bucket=bucket,
        CopySource={"Bucket": bucket, "Key": src_key},
        Key=dst_key,
        MetadataDirective="COPY",
    )


def append_promotion_log(
    s3, bucket: str, entry: dict, *, max_attempts: int = 5
) -> None:
    key = "main/PROMOTIONS.jsonl"
    new_line = json.dumps(entry, sort_keys=True) + "\n"
    for attempt in range(max_attempts):
        try:
            resp = s3.get_object(Bucket=bucket, Key=key)
            existing = resp["Body"].read()
            etag = resp["ETag"]
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("NoSuchKey", "404"):
                existing = b""
                etag = None
            else:
                raise

        body = existing + new_line.encode("utf-8")
        extra = {
            "Bucket": bucket,
            "Key": key,
            "Body": body,
            "ContentType": "application/x-ndjson",
        }
        if etag:
            extra["IfMatch"] = etag
        try:
            s3.put_object(**extra)
            return
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("PreconditionFailed", "412") and attempt < max_attempts - 1:
                continue
            raise
    raise SystemExit("::error::Failed to append PROMOTIONS.jsonl after retries")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-run", required=True,
                        help="builds/<source-run>/ prefix; may be <id>-<sha> or just <id>")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--promoter", default=os.environ.get("GITHUB_ACTOR", "unknown"))
    args = parser.parse_args()

    bucket = os.environ["S3_BUCKET"]
    s3 = make_s3_client()

    src_prefix = resolve_source_prefix(s3, bucket, args.source_run)
    print(f"Resolved source: {src_prefix}/")

    manifest = load_manifest(s3, bucket, src_prefix)
    print(
        f"MANIFEST: run_id={manifest.get('run_id')} "
        f"sha={manifest.get('commit_sha')} "
        f"ref={manifest.get('ref')} "
        f"uploaded_at={manifest.get('uploaded_at')}"
    )

    all_keys = list_keys(s3, bucket, src_prefix)
    copies: list[tuple[str, str]] = []
    for src in all_keys:
        rel = src[len(src_prefix) + 1:]
        if rel == "MANIFEST.json":
            continue
        dst = f"main/{rel}"
        copies.append((src, dst))

    print(f"\nPlanned copies: {len(copies)}")
    for src, dst in copies:
        print(f"  {src}  ->  {dst}")

    if args.dry_run:
        print("\n::notice::Dry run — no changes made.")
        return 0

    print(f"\nExecuting {len(copies)} copies...")
    for i, (src, dst) in enumerate(copies, 1):
        copy_object(s3, bucket, src, dst)
        if i % 20 == 0 or i == len(copies):
            print(f"  {i}/{len(copies)} done")

    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "source_run": src_prefix.removeprefix("builds/"),
        "commit_sha": manifest.get("commit_sha"),
        "ref": manifest.get("ref"),
        "promoter": args.promoter,
        "files_promoted": len(copies),
    }
    append_promotion_log(s3, bucket, entry)
    print(f"\n::notice::Promoted {len(copies)} file(s) from {src_prefix}/ to main/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
