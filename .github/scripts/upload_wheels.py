#!/usr/bin/env python3
"""Upload built MonolithPy wheels to the staging bucket.

Layout written under `builds/<run-id>-<sha>/`:

    <norm-pkg-name>/<wheel>.whl
    <norm-pkg-name>/<wheel>.whl.metadata   # PEP 658 sidecar (dist-info METADATA)
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
    r"(?:-\d[^-]*)?"
    r"-(?P<python>[^-]+)-(?P<abi>[^-]+)-(?P<platform>[^.]+)\.whl$"
)


def pep503_normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_wheel_filename(filename: str) -> tuple[str, str]:
    m = _WHEEL_NAME_RE.match(filename)
    if not m:
        raise ValueError(f"Cannot parse wheel filename: {filename}")
    return m.group("name"), m.group("version")


def is_universal_wheel(filename: str) -> bool:
    """A wheel with abi=none and platform=any is pure Python."""
    m = _WHEEL_NAME_RE.match(filename)
    if not m:
        return False
    return m.group("abi") == "none" and m.group("platform") == "any"


def has_build_recipe(norm_name: str, repo_root: Path) -> bool:
    """True if the repo contains an explicit build.py recipe for this package.
    Recipes live at packages/<platform>/<name>/build.py (or under a version
    subdir) or the equivalent under dependencies/ or build_tools/."""
    for root_name in ("packages", "dependencies", "build_tools"):
        root = repo_root / root_name
        if not root.is_dir():
            continue
        for platform_dir in root.iterdir():
            pkg_dir = platform_dir / norm_name
            if not pkg_dir.is_dir():
                continue
            if (pkg_dir / "build.py").is_file():
                return True
            for sub in pkg_dir.iterdir():
                if sub.is_dir() and (sub / "build.py").is_file():
                    return True
    return False


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

    # Skip pure-Python wheels (abi=none, plat=any) UNLESS the repo has an
    # explicit build.py recipe for that package — those are wheels we built
    # ourselves (e.g. meson, meson-python) and must ship from our bucket so
    # downstream installs pick our patched version instead of pristine PyPI.
    repo_root = Path(__file__).resolve().parent.parent.parent
    skipped_universal = []
    for name in list(wheels):
        if not is_universal_wheel(name):
            continue
        dist_name, _ = parse_wheel_filename(name)
        if has_build_recipe(pep503_normalize(dist_name), repo_root):
            continue
        skipped_universal.append(name)
        del wheels[name]
    skipped_universal.sort()
    if skipped_universal:
        print(f"Skipping {len(skipped_universal)} pure-Python wheel(s) already on PyPI:")
        for name in skipped_universal:
            print(f"  - {name}")

    print(f"Found {len(wheels)} wheel(s) to upload")
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
    }

    print("\nUploading MANIFEST.json...")
    upload_manifest(s3, bucket, f"{prefix}/MANIFEST.json", manifest)

    print(f"\n::notice::Upload complete: {prefix}/ ({len(wheels)} wheels)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
