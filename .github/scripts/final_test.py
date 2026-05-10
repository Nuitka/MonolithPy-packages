#!/usr/bin/env python3
"""Install every package together into a single MonolithPy interpreter, run
every package's test suite, then print the dynamic libraries linked to the
final rebuilt interpreter.

Build tools (mpy-tool-*) and dependency wheels (mpy-dep-*) are pulled in
transitively as dependencies of the top-level packages, so we only install
the top-level `packages/` entries directly.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_monolithpy_executable(monolithpy_dir: Path) -> Path:
    if platform.system() == "Windows":
        return monolithpy_dir / "python.exe"
    return monolithpy_dir / "bin" / "python3.13"


def list_top_level_packages(packages_dir: Path) -> list[str]:
    return sorted(d.name for d in packages_dir.iterdir() if d.is_dir())


def list_tests(pkg_dir: Path) -> list[Path]:
    idx = pkg_dir / "index.json"
    if not idx.exists():
        return []
    try:
        data = json.loads(idx.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    return [pkg_dir / t for t in data.get("tests", []) if (pkg_dir / t).exists()]


def run_pip_install(monolithpy: Path, wheel_dir: Path, packages: list[str]) -> bool:
    cmd = [
        str(monolithpy), "-m", "pip", "install", "--verbose",
        "--find-links", str(wheel_dir),
        *packages,
    ]
    print(f"\n::group::pip install {' '.join(packages)}")
    rc = subprocess.call(cmd)
    print("::endgroup::")
    return rc == 0


def run_tests(monolithpy: Path, packages_dir: Path, packages: list[str]) -> list[str]:
    failed: list[str] = []
    for pkg in packages:
        tests = list_tests(packages_dir / pkg)
        if not tests:
            print(f"::notice::{pkg}: no tests declared, skipping")
            continue
        for test_path in tests:
            label = f"{pkg}/{test_path.name}"
            print(f"\n::group::Running test: {label}")
            rc = subprocess.call([str(monolithpy), str(test_path)])
            print("::endgroup::")
            if rc != 0:
                print(f"::error::Test failed: {label} (exit {rc})")
                failed.append(label)
            else:
                print(f"::notice::Test passed: {label}")
    return failed


def dump_loaded_libraries(monolithpy: Path) -> None:
    """Start the interpreter, import every top-level package we know about, then
    dump the list of dynamic libraries the process has mapped in."""
    print("\n::group::Loaded dynamic libraries of the final interpreter")
    sys_name = platform.system()
    if sys_name == "Windows":
        script = (
            "import os, sys, ctypes, ctypes.wintypes as wt\n"
            "pid = os.getpid()\n"
            "psapi = ctypes.WinDLL('psapi')\n"
            "k32 = ctypes.WinDLL('kernel32')\n"
            "h = k32.OpenProcess(0x0410, False, pid)\n"
            "arr = (ctypes.c_void_p * 4096)()\n"
            "needed = wt.DWORD(0)\n"
            "psapi.EnumProcessModules(h, arr, ctypes.sizeof(arr), ctypes.byref(needed))\n"
            "count = needed.value // ctypes.sizeof(ctypes.c_void_p)\n"
            "buf = ctypes.create_unicode_buffer(1024)\n"
            "seen = []\n"
            "for i in range(count):\n"
            "    psapi.GetModuleFileNameExW(h, arr[i], buf, len(buf))\n"
            "    seen.append(buf.value)\n"
            "print(f'### {len(seen)} loaded modules ###')\n"
            "for m in sorted(seen, key=str.lower):\n"
            "    print(m)\n"
        )
        rc = subprocess.call([str(monolithpy), "-c", script])
    else:
        # macOS/Linux: use /proc/self/maps (Linux) or vmmap (macOS).
        # Easiest cross-platform: use the dl APIs via ctypes to iterate
        # loaded images. macOS: _dyld_image_count / _dyld_get_image_name.
        if sys_name == "Darwin":
            script = (
                "import ctypes, ctypes.util\n"
                "libc = ctypes.CDLL(ctypes.util.find_library('c'))\n"
                "libc._dyld_image_count.restype = ctypes.c_uint32\n"
                "libc._dyld_get_image_name.restype = ctypes.c_char_p\n"
                "libc._dyld_get_image_name.argtypes = [ctypes.c_uint32]\n"
                "names = [libc._dyld_get_image_name(i).decode() "
                "for i in range(libc._dyld_image_count())]\n"
                "print(f'### {len(names)} loaded images ###')\n"
                "for n in sorted(names, key=str.lower):\n"
                "    print(n)\n"
            )
        else:
            script = (
                "import pathlib\n"
                "seen = set()\n"
                "for line in pathlib.Path('/proc/self/maps').read_text().splitlines():\n"
                "    parts = line.split(maxsplit=5)\n"
                "    if len(parts) == 6 and parts[5].startswith('/'):\n"
                "        seen.add(parts[5])\n"
                "print(f'### {len(seen)} mapped files ###')\n"
                "for n in sorted(seen, key=str.lower):\n"
                "    print(n)\n"
            )
        rc = subprocess.call([str(monolithpy), "-c", script])
    print("::endgroup::")
    if rc != 0:
        print(f"::warning::Loaded-library dump exited with code {rc}")


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--monolithpy", required=True, type=Path)
    parser.add_argument("--wheels", required=True, type=Path)
    args = parser.parse_args()

    root = Path.cwd()
    if platform.system() == "Windows":
        packages_dir = root / "packages" / "mp313-windows"
    elif platform.system() == "Darwin":
        packages_dir = root / "packages" / "mp313-macos"
    else:
        print(f"::error::Unsupported platform: {platform.system()}", file=sys.stderr)
        return 1

    # Work on a clean copy of the monolithpy artifact so test side effects
    # don't leak between runs in the same job.
    work_dir = root / "monolithpy_final"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    shutil.copytree(args.monolithpy, work_dir)

    monolithpy = get_monolithpy_executable(work_dir)
    if not monolithpy.exists():
        print(f"::error::MonolithPy executable not found at {monolithpy}", file=sys.stderr)
        return 1

    # Rebuild the python binary so any prior state from the artifact is discarded.
    try:
        subprocess.run([str(monolithpy), "-m", "rebuildpython"],
                       capture_output=True, check=False)
    except Exception:
        pass

    packages = list_top_level_packages(packages_dir)
    if not packages:
        print(f"::error::No packages found in {packages_dir}", file=sys.stderr)
        return 1
    print(f"Installing {len(packages)} top-level package(s): {packages}")

    if not run_pip_install(monolithpy, args.wheels, packages):
        print("::error::pip install failed", file=sys.stderr)
        return 1

    # rebuild again after install so all native extensions are linked in.
    subprocess.run([str(monolithpy), "-m", "rebuildpython"],
                   capture_output=True, check=False)

    failed = run_tests(monolithpy, packages_dir, packages)

    dump_loaded_libraries(monolithpy)

    if failed:
        print(f"\n::error::{len(failed)} test(s) failed:")
        for f in failed:
            print(f"  - {f}")
        return 1

    print(f"\n::notice::All tests passed across {len(packages)} package(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
