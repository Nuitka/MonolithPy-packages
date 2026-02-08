#!/usr/bin/env python3
"""Build and test mp313 packages using MonolithPy."""

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from collections import defaultdict
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


def parse_version(version_str: str) -> tuple:
    """Parse version string into comparable tuple."""
    # Handle versions like "1.2.3", "1.2.3a1", "1.2.3.post1", etc.
    parts = re.split(r'[.\-]', version_str)
    result = []
    for part in parts:
        # Try to convert to int, otherwise keep as string for comparison
        try:
            result.append((0, int(part)))
        except ValueError:
            # Handle alpha/beta/rc/post suffixes
            result.append((1, part))
    return tuple(result)


def get_ensurepip_package_names(monolithpy: Path) -> set[str]:
    """Get the package names bundled with ensurepip from MonolithPy."""
    try:
        result = subprocess.run(
            [str(monolithpy), "-c", "import ensurepip; print('\\n'.join(ensurepip._PACKAGE_NAMES))"],
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            return {name.lower() for name in result.stdout.strip().splitlines()}
    except Exception:
        pass
    return set()


def write_constraint_file(pkg_name: str, packages: dict[str, str], output_dir: Path, excluded: set[str]):
    """Write a constraint file for a package based on pip output."""
    if not packages:
        return

    constraint_file = output_dir / f"{pkg_name}-constraint.txt"
    with open(constraint_file, 'w') as f:
        for name, version in sorted(packages.items()):
            if name.lower() not in excluded:
                f.write(f"{name}<={version}\n")

    print(f"Created constraint file: {constraint_file}")


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


def run_build(monolithpy: Path, package_name: str) -> tuple[bool, dict[str, str]]:
    """Attempt to build a package. Returns (success, packages_dict)."""
    packages = defaultdict(list)

    try:
        process = subprocess.Popen(
            [str(monolithpy), "-m", "pip", "install", "--verbose", package_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
        )

        for line in process.stdout:
            # Stream output immediately
            print(line, end='', flush=True)

            # Parse for package info from various pip output patterns:
            # "Downloading package_name-1.2.3-py3-none-any.whl"
            # "Using cached package_name-1.2.3-py3-none-any.whl"
            wheel_match = re.search(r'(?:Downloading|Using cached)\s+(\S+\.whl)', line)
            if wheel_match:
                wheel_name = wheel_match.group(1)
                # Parse wheel filename: name-version-python-abi-platform.whl
                parts_match = re.match(r'([A-Za-z0-9_][A-Za-z0-9._-]*)-(\d+[A-Za-z0-9._]*)-', wheel_name)
                if parts_match:
                    pkg_name = parts_match.group(1).lower().replace('_', '-')
                    version = parts_match.group(2)
                    packages[pkg_name].append(version)
                continue

            # "Downloading package_name-1.2.3.tar.gz"
            # "Using cached package_name-1.2.3.tar.gz"
            tarball_match = re.search(r'(?:Downloading|Using cached)\s+([A-Za-z0-9_][A-Za-z0-9._-]*)-(\d+[A-Za-z0-9._]*)\.(?:tar\.gz|zip)', line)
            if tarball_match:
                pkg_name = tarball_match.group(1).lower().replace('_', '-')
                version = tarball_match.group(2)
                packages[pkg_name].append(version)
                continue

            # "Successfully installed pkg1-1.0.0 pkg2-2.0.0 ..."
            if 'Successfully installed' in line:
                for match in re.finditer(r'([A-Za-z0-9_][A-Za-z0-9._-]*)-(\d+[A-Za-z0-9._]*)', line):
                    pkg_name = match.group(1).lower().replace('_', '-')
                    version = match.group(2)
                    packages[pkg_name].append(version)

        process.wait()

        # Build result dict with max versions
        result_dict = {}
        for pkg_name, versions in packages.items():
            result_dict[pkg_name] = max(versions, key=parse_version)

        return process.returncode == 0, result_dict
    except Exception as e:
        print(f"Build error: {e}", file=sys.stderr)
        return False, {}


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

    # Create constraints output directory
    constraints_dir = root_dir / "constraints"
    constraints_dir.mkdir(exist_ok=True)

    # Get MonolithPy executable
    monolithpy = get_monolithpy_executable(monolithpy_dir)
    print(f"MonolithPy location: {monolithpy}")
    if not monolithpy.exists():
        print(f"::error::MonolithPy executable not found at {monolithpy}", file=sys.stderr)
        sys.exit(1)

    # Keep a pristine copy of MonolithPy
    pristine_dir = root_dir / "monolithpy_pristine"
    shutil.copytree(monolithpy_dir, pristine_dir, dirs_exist_ok=True)

    # Get ensurepip package names to exclude from constraints
    ensurepip_packages = get_ensurepip_package_names(monolithpy)
    print(f"Excluding ensurepip packages: {ensurepip_packages}")

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
        success, installed_packages = run_build(monolithpy, pkg_name)
        if not success:
            print(f"::error::Build failed for {pkg_name}")
            print("::endgroup::")
            sys.exit(1)

        print(f"Build successful for {pkg_name}")

        # Generate constraint file from parsed pip output
        write_constraint_file(pkg_name, installed_packages, constraints_dir, ensurepip_packages)

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

