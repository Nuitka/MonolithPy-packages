#!/usr/bin/env python3
"""Build and test mp313 packages using MonolithPy."""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


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


def clear_pip_cache():
    """Clear pip cache, ignoring errors."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "cache", "purge"],
                       capture_output=True, check=False)
    except Exception:
        pass


def run_build(monolithpy: Path, package_name: str) -> bool:
    """Attempt to build a package. Returns True on success."""
    try:
        result = subprocess.run(
            [str(monolithpy), "-m", "pip", "install", "--verbose", package_name],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Build error: {e}", file=sys.stderr)
        return False


def run_test(monolithpy: Path, test_path: Path) -> bool:
    """Run a test file. Returns True on success."""
    try:
        result = subprocess.run(
            [str(monolithpy), str(test_path)],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
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
    
    work_dir = root_dir / "work"
    
    for pkg_dir in sorted(packages_dir.iterdir()):
        if not pkg_dir.is_dir():
            continue
        
        pkg_name = pkg_dir.name
        print(f"::group::Building {pkg_name}")
        
        # Make a fresh copy of MonolithPy
        pkg_work_dir = work_dir / pkg_name
        pkg_work_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(monolithpy_dir, pkg_work_dir / "monolithpy", dirs_exist_ok=True)
        
        clear_pip_cache()
        
        build_script = pkg_dir / "build.py"
        if not build_script.exists():
            print(f"No build.py found for {pkg_name}, skipping")
            print("::endgroup::")
            continue
        
        print(f"Building {pkg_name}...")
        if run_build(monolithpy, pkg_name):
            print(f"Build successful for {pkg_name}")
            
            # Check for and run tests
            tests = get_tests_from_index(pkg_dir / "index.json")
            for test_file in tests:
                test_path = pkg_dir / test_file
                if test_path.exists():
                    print(f"Running test: {test_file}")
                    if run_test(monolithpy, test_path):
                        print(f"Test passed for {pkg_name}/{test_file}")
                    else:
                        print(f"::warning::Test failed for {pkg_name}/{test_file}")
        else:
            print(f"::warning::Build failed for {pkg_name}")
        
        print("::endgroup::")


if __name__ == "__main__":
    main()

