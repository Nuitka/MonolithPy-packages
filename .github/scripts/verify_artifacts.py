#!/usr/bin/env python3
"""Gate the built MonolithPy wheels for static-linkage hygiene.

MonolithPy is a static monolith: every package and dependency ships as
relocatable objects / static libraries (.obj/.lib on Windows, .o/.a on macOS)
that are linked into a single interpreter at install time. Two invariants must
hold for the *shipped* wheels (build-tool wheels, mpy-tool-*, are excluded --
clang/cmake/gcc/ninja run on the build host and are never linked in):

  1. No dynamic modules. A shipped wheel must contain no .dll/.pyd (Windows) and
     no .dylib/.so/.bundle (macOS). A dynamic module means something built a
     shared object instead of static input for the monolith.

  2. Full /MT (Windows) and low macOS minimum. Every .obj/.lib must use the
     static CRT (LIBCMT, not MSVCRT); every Mach-O .o/.a slice must target a
     macOS minimum below the threshold (default 13) rather than inheriting the
     build runner's OS.

The /MT and min-macOS content checks are delegated to the proven dumpbin/otool
scripts in ci/; this script owns wheel selection, the no-dynamic-modules check,
and orchestration. It exits non-zero on any violation so it can gate uploads.

Usage: verify_artifacts.py --wheels DIR [--max-macos-major 13]
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


# Wheels that are build tools, not shipped/linked artifacts.
TOOL_PREFIXES = ("mpy_tool_", "mpy-tool-")

# Dynamic modules that must never appear in a shipped wheel.
DYNAMIC_EXTS = (".dll", ".pyd", ".dylib", ".so", ".bundle")

# Object / static-lib members to extract for the native content scanners.
CONTENT_EXTS_WINDOWS = (".lib", ".obj")
CONTENT_EXTS_MACOS = (".o", ".a")


def is_scannable(whl: Path) -> bool:
    name = whl.name.lower()
    if name.startswith(TOOL_PREFIXES):
        return False
    # Pure-Python wheels carry no compiled artifacts.
    if name.endswith("-none-any.whl"):
        return False
    return True


def find_powershell() -> str | None:
    for exe in ("pwsh", "powershell"):
        if shutil.which(exe):
            return exe
    return None


def main() -> int:
    # Keep our prints ordered with the delegated dumpbin/otool subprocess output
    # (CI captures a pipe, so stdout is block-buffered by default).
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--wheels", required=True, type=Path)
    ap.add_argument("--max-macos-major", default=13, type=int)
    args = ap.parse_args()

    if not args.wheels.is_dir():
        print(f"::error::--wheels dir not found: {args.wheels}", file=sys.stderr)
        return 1

    wheels = sorted(args.wheels.rglob("*.whl"))
    scannable = [w for w in wheels if is_scannable(w)]
    skipped = [w for w in wheels if w not in scannable]

    print(f"::group::Artifact verification: {len(scannable)} shipped wheel(s) "
          f"({len(skipped)} tool/pure-python wheel(s) skipped)")
    for w in scannable:
        print(f"  scan  {w.name}")
    for w in skipped:
        print(f"  skip  {w.name}")
    print("::endgroup::")

    if not scannable:
        print("::notice::No shipped wheels to verify.")
        return 0

    host = platform.system()
    content_exts = CONTENT_EXTS_WINDOWS if host == "Windows" else CONTENT_EXTS_MACOS

    extract_root = Path(tempfile.mkdtemp(prefix="verify-artifacts-"))
    dynamic_hits: list[str] = []
    try:
        # Pass 1: inspect zip listings for dynamic modules (no extraction needed),
        # and extract only the object/lib members the content scanner needs.
        for whl in scannable:
            try:
                with zipfile.ZipFile(whl, "r") as zf:
                    names = zf.namelist()
                    for n in names:
                        if n.endswith("/"):
                            continue
                        ext = os.path.splitext(n)[1].lower()
                        if ext in DYNAMIC_EXTS:
                            dynamic_hits.append(f"{whl.name} :: {n}")
                    members = [n for n in names
                               if os.path.splitext(n)[1].lower() in content_exts]
                    if members:
                        dest = extract_root / whl.stem
                        for n in members:
                            zf.extract(n, dest)
            except zipfile.BadZipFile as e:
                print(f"::error::{whl.name}: not a valid wheel ({e})", file=sys.stderr)
                return 1

        failed = False

        # Check 1: no dynamic modules in shipped wheels.
        print("::group::Check: no dynamic modules (.dll/.pyd/.dylib/.so/.bundle) in shipped wheels")
        if dynamic_hits:
            failed = True
            print("::error::dynamic module(s) found in shipped wheel(s) "
                  "(MonolithPy artifacts must be fully static):")
            for h in sorted(set(dynamic_hits)):
                print(f"    {h}")
        else:
            print("OK -- no dynamic modules in any shipped wheel")
        print("::endgroup::")

        # Check 2: native content scan (/MT on Windows, min-macOS on macOS).
        script_dir = Path(__file__).resolve().parent / "ci"
        if host == "Windows":
            ps = find_powershell()
            if ps is None:
                print("::error::PowerShell (pwsh/powershell) not found for /MT check",
                      file=sys.stderr)
                return 1
            script = script_dir / "verify-static-windows.ps1"
            cmd = [ps, "-NoProfile", "-ExecutionPolicy", "Bypass",
                   "-File", str(script), "-Paths", str(extract_root)]
        elif host == "Darwin":
            script = script_dir / "verify-min-macos.sh"
            cmd = ["sh", str(script), str(args.max_macos_major), str(extract_root)]
        else:
            print(f"::notice::Host {host} has no native content scan; "
                  "dynamic-module check only.")
            return 1 if failed else 0

        label = "/MT static CRT" if host == "Windows" else f"min macOS < {args.max_macos_major}"
        print(f"::group::Check: {label}")
        sys.stdout.flush()
        rc = subprocess.call(cmd)
        print("::endgroup::")
        if rc != 0:
            failed = True

        if failed:
            print("::error::Artifact verification FAILED", file=sys.stderr)
            return 1
        print("::notice::Artifact verification passed "
              f"({len(scannable)} shipped wheel(s))")
        return 0
    finally:
        shutil.rmtree(extract_root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
