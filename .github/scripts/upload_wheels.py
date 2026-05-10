#!/usr/bin/env python3
"""Upload built MonolithPy wheels + constraints to the staging bucket.

Layout written under `builds/<run-id>-<sha>/`:

    <norm-pkg-name>/<wheel>.whl
    <norm-pkg-name>/<wheel>.whl.metadata   # PEP 658 sidecar (dist-info METADATA)
    constraints/<pkg>-constraint.txt
    MANIFEST.json                          # written last; presence = upload complete
"""

import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path

import boto3
from botocore.config import Config


_WHEEL_NAME_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*?)-(?P<version>\d[^-]*)"
    r"(?:-\d[^-]*)?-[^-]+-[^-]+-[^.]+\.whl$"
)


def pep503_normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_wheel_filename(filename: str) -> tuple[str, str]:
    m = _WHEEL_NAME_RE.match(filename)
    if not m:
        raise ValueError(f"Cannot parse wheel filename: {filename}")
    return m.group("name"), m.group("version")


def extract_metadata_from_wheel(wheel_path: Path) -> bytes:
    with zipfile.ZipFile(wheel_path, "r") as zf:
        for member in zf.namelist():
            if member.endswith(".dist-info/METADATA"):
                return zf.read(member)
    raise RuntimeError(f"No METADATA found in {wheel_path}")


def collect_wheels(source_dir: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for whl in source_dir.rglob("*.whl"):
        if whl.name in found:
            continue
        found[whl.name] = whl
    return found


def collect_constraints(constraints_dir: Path) -> list[Path]:
    if not constraints_dir.exists():
        return []
    return sorted(p for p in constraints_dir.rglob("*") if p.is_file())


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


def upload_wheel(s3, bucket: str, key: str, path: Path) -> None:
    s3.upload_file(
        str(path),
        bucket,
        key,
        ExtraArgs={"ContentType": "application/octet-stream"},
    )
    print(f"  uploaded {key} ({path.stat().st_size} bytes)")


def upload_metadata(s3, bucket: str, key: str, data: bytes) -> str:
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=data,
        ContentType="text/plain; charset=utf-8",
    )
    digest = hashlib.sha256(data).hexdigest()
    print(f"  uploaded {key} ({len(data)} bytes, sha256={digest[:12]}...)")
    return digest


def upload_constraint(s3, bucket: str, key: str, path: Path) -> None:
    s3.upload_file(
        str(path),
        bucket,
        key,
        ExtraArgs={"ContentType": "text/plain; charset=utf-8"},
    )
    print(f"  uploaded {key}")


def upload_manifest(s3, bucket: str, key: str, manifest: dict) -> None:
    body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/json",
    )
    print(f"  uploaded {key} ({len(body)} bytes)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--constraints", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--ref", default="")
    parser.add_argument("--workflow-url", default="")
    args = parser.parse_args()

    run_folder = f"{args.run_id}-{args.sha}"
    prefix = f"builds/{run_folder}"

    wheels = collect_wheels(args.source)
    if not wheels:
        print(f"::error::No wheels found in {args.source}", file=sys.stderr)
        return 1

    constraints = collect_constraints(args.constraints)

    print(f"Found {len(wheels)} wheel(s), {len(constraints)} constraint file(s)")
    print(f"Target prefix: {prefix}/")

    bucket = os.environ["S3_BUCKET"]
    s3 = make_s3_client()

    per_package: dict[str, list[dict]] = {}

    def upload_one_wheel(item):
        filename, path = item
        dist_name, version = parse_wheel_filename(filename)
        norm = pep503_normalize(dist_name)
        wheel_key = f"{prefix}/{norm}/{filename}"
        meta_key = f"{wheel_key}.metadata"

        metadata_bytes = extract_metadata_from_wheel(path)
        upload_wheel(s3, bucket, wheel_key, path)
        meta_digest = upload_metadata(s3, bucket, meta_key, metadata_bytes)

        return norm, {
            "filename": filename,
            "version": version,
            "size": path.stat().st_size,
            "wheel_key": wheel_key,
            "metadata_key": meta_key,
            "metadata_sha256": meta_digest,
        }

    print("\nUploading wheels + PEP 658 metadata sidecars...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for norm, info in executor.map(upload_one_wheel, wheels.items()):
            per_package.setdefault(norm, []).append(info)

    print("\nUploading constraint files...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for cpath in constraints:
            key = f"{prefix}/constraints/{cpath.name}"
            futures.append(executor.submit(upload_constraint, s3, bucket, key, cpath))
        for f in concurrent.futures.as_completed(futures):
            f.result()

    manifest = {
        "schema_version": 1,
        "run_id": args.run_id,
        "commit_sha": args.sha,
        "ref": args.ref,
        "workflow_url": args.workflow_url,
        "uploaded_at": datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "packages": {
            name: sorted(infos, key=lambda x: x["filename"])
            for name, infos in sorted(per_package.items())
        },
        "constraints": sorted(c.name for c in constraints),
    }

    print("\nUploading MANIFEST.json...")
    upload_manifest(s3, bucket, f"{prefix}/MANIFEST.json", manifest)

    print(f"\n::notice::Upload complete: {prefix}/ ({len(wheels)} wheels)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
