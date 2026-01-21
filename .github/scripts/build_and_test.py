#!/usr/bin/env python3
"""Build and test mp313 packages using MonolithPy."""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Unbuffered output for CI environments
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)


def get_monolithpy_executable(monolithpy_dir: Path) -> Path:
    """Get the MonolithPy executable path."""
    if platform.system() == "Windows":
        return monolithpy_dir / "python.exe"
    else:
        return monolithpy_dir / "bin" / "python3.13"


def get_tests_from_index(index_path: Path) -> list[str]:
    """Read test files from index.json."""
    if not index_path.exists():
        return []
    try:
        with open(index_path) as f:
            data = json.load(f)
        return data.get("tests", [])
    except (json.JSONDecodeError, KeyError):
        return []


def clear_pip_cache(monolithpy: Path):
    """Clear pip cache, ignoring errors."""
    try:
        subprocess.run([str(monolithpy), "-m", "pip", "cache", "purge"],
                       capture_output=True, check=False)
    except Exception:
        pass


def rmtree_force(path: Path):
    """Remove directory tree, handling Windows permission issues."""
    def on_error(func, path, exc_info):
        try:
            # Handle read-only files on Windows
            os.chmod(path, 0o777)
            func(path)
        except Exception:
            # If we still can't delete, move the file out of the way
            import uuid
            trash_dir = Path.cwd() / ".trash"
            trash_dir.mkdir(exist_ok=True)
            shutil.move(path, trash_dir / f"{uuid.uuid4().hex}")

    shutil.rmtree(path, onexc=on_error)


def run_rebuild(monolithpy: Path):
    """Clear pip cache, ignoring errors."""
    try:
        subprocess.run([str(monolithpy), "-m", "rebuildpython"],
                       capture_output=True, check=False)
    except Exception:
        pass


def run_build(monolithpy: Path, package_name: str) -> bool:
    """Attempt to build a package. Returns True on success."""
    try:
        result = subprocess.run(
            [str(monolithpy), "-m", "pip", "install", "--verbose", package_name],
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Build error: {e}", file=sys.stderr)
        return False


def run_test(monolithpy: Path, test_path: Path) -> bool:
    """Run a test file. Returns True on success."""
    try:
        result = subprocess.run(
            [str(monolithpy), str(test_path)],
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Test error: {e}", file=sys.stderr)
        return False


def main():
    root_dir = Path.cwd()
    monolithpy_dir = root_dir / "monolithpy"
    
    # Determine platform-specific package directory
    if platform.system() == "Windows":
        packages_dir = root_dir / "packages" / "mp313-windows"
    elif platform.system() == "Darwin":
        packages_dir = root_dir / "packages" / "mp313-macos"
    else:
        print(f"Unsupported platform: {platform.system()}", file=sys.stderr)
        sys.exit(1)
    
    # Get MonolithPy executable
    monolithpy = get_monolithpy_executable(monolithpy_dir)
    print(f"MonolithPy location: {monolithpy}")
    if not monolithpy.exists():
        print(f"::error::MonolithPy executable not found at {monolithpy}", file=sys.stderr)
        sys.exit(1)
    
    # Keep a pristine copy of MonolithPy
    pristine_dir = root_dir / "monolithpy_pristine"
    shutil.copytree(monolithpy_dir, pristine_dir, dirs_exist_ok=True)

    work_monolithpy = root_dir / "monolithpy_work"

    for pkg_dir in sorted(packages_dir.iterdir()):
        if not pkg_dir.is_dir():
            continue

        pkg_name = pkg_dir.name
        print(f"::group::Building {pkg_name}")

        # Create a fresh copy of MonolithPy for this package
        if work_monolithpy.exists():
            rmtree_force(work_monolithpy)
        shutil.copytree(pristine_dir, work_monolithpy)

        # Update monolithpy to point to working copy
        monolithpy = get_monolithpy_executable(work_monolithpy)

        run_rebuild(monolithpy)

        clear_pip_cache(monolithpy)
        
        print(f"Building {pkg_name}...")
        if not run_build(monolithpy, pkg_name):
            print(f"::error::Build failed for {pkg_name}")
            print("::endgroup::")
            sys.exit(1)

        print(f"Build successful for {pkg_name}")

        # Check for and run tests
        tests = get_tests_from_index(pkg_dir / "index.json")
        for test_file in tests:
            test_path = pkg_dir / test_file
            if test_path.exists():
                print(f"Running test: {test_file}")
                if not run_test(monolithpy, test_path):
                    print(f"::error::Test failed for {pkg_name}/{test_file}")
                    print("::endgroup::")
                    sys.exit(1)
                print(f"Test passed for {pkg_name}/{test_file}")

        print("::endgroup::")


if __name__ == "__main__":
    main()

