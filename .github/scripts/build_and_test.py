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
    parts = re.split(r'[.\-]', version_str)
    result = []
    for part in parts:
        try:
            result.append((0, int(part)))
        except ValueError:
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
            os.chmod(path, 0o777)
            func(path)
        except Exception:
            import uuid
            trash_dir = Path.cwd() / ".trash"
            trash_dir.mkdir(exist_ok=True)
            shutil.move(path, trash_dir / f"{uuid.uuid4().hex}")

    shutil.rmtree(path, onexc=on_error)


def run_rebuild(monolithpy: Path):
    """Run rebuildpython, ignoring errors."""
    try:
        subprocess.run([str(monolithpy), "-m", "rebuildpython"],
                       capture_output=True, check=False)
    except Exception:
        pass


def collect_built_wheels(pip_cache_dir: Path, output_dir: Path):
    """Copy wheels from pip's wheel cache to output_dir."""
    wheels_subdir = pip_cache_dir / "wheels"
    if not wheels_subdir.exists():
        return
    copied = 0
    for whl in wheels_subdir.rglob("*.whl"):
        dest = output_dir / whl.name
        if not dest.exists():
            shutil.copy2(whl, dest)
            copied += 1
    if copied:
        print(f"Captured {copied} wheel(s) from pip cache")


def normalize_pkg_name(name: str) -> str:
    """PEP 503 normalization for package name comparison."""
    return re.sub(r'[-_.]+', '-', name).lower()


def _iter_subdirs(path: Path):
    """Yield immediate subdirectories of path, if path exists."""
    if path.exists():
        yield from (d for d in path.iterdir() if d.is_dir())


def build_catalog(
    packages_dir: Path,
    dependencies_dir: Path,
    build_tools_dir: Path,
) -> dict[str, Path]:
    """Return {pip_install_name: package_dir} across all three source trees.

    - packages/      → pip name is the directory name        (e.g. "numpy")
    - dependencies/  → pip name is "mpy-dep-{dirname}"       (e.g. "mpy-dep-openblas")
    - build_tools/   → pip name is "mpy-tool-{dirname}"      (e.g. "mpy-tool-clang")
    """
    catalog: dict[str, Path] = {}
    for d in _iter_subdirs(packages_dir):
        catalog[d.name] = d
    for d in _iter_subdirs(dependencies_dir):
        catalog[f"mpy-dep-{d.name}"] = d
    for d in _iter_subdirs(build_tools_dir):
        catalog[f"mpy-tool-{d.name}"] = d
    return catalog


def build_dep_graph(catalog: dict[str, Path]) -> dict[str, set[str]]:
    """Return {pip_name -> set[pip_name]} covering all direct local dependencies.

    Reads four fields from each index.json:
      build_requires / dist_requires  – regular pip requirement specifiers
      dependencies                    – MonolithPy mpy-dep-* packages
      build_tools                     – MonolithPy mpy-tool-* packages
    """
    # Normalized-name → actual pip install name (for fuzzy requirement matching)
    norm_map: dict[str, str] = {normalize_pkg_name(name): name for name in catalog}

    graph: dict[str, set[str]] = {name: set() for name in catalog}

    for pip_name, pkg_dir in catalog.items():
        index_path = pkg_dir / "index.json"
        if not index_path.exists():
            continue
        try:
            with open(index_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        scripts = data.get("scripts", [{}])
        script = scripts[0] if scripts else {}

        def add_edge(norm_target: str) -> None:
            if norm_target in norm_map and norm_map[norm_target] != pip_name:
                graph[pip_name].add(norm_map[norm_target])

        # Regular pip requirements (build_requires / dist_requires)
        for req in script.get("build_requires", []) + script.get("dist_requires", []):
            bare = re.split(r'[>=<!;\[\s,]', req.strip())[0]
            add_edge(normalize_pkg_name(bare))

        # MonolithPy dependency packages  →  "mpy-dep-{name}"
        for dep in script.get("dependencies", []):
            add_edge(normalize_pkg_name(f"mpy-dep-{dep}"))

        # MonolithPy build tool packages  →  "mpy-tool-{name}"
        for tool in script.get("build_tools", []):
            add_edge(normalize_pkg_name(f"mpy-tool-{tool}"))

    return graph


def find_prebuild_candidates(dep_graph: dict[str, set[str]], threshold: int = 2) -> list[str]:
    """Return packages that appear as a dep of at least `threshold` other packages."""
    ref_count: dict[str, int] = {}
    for deps in dep_graph.values():
        for dep in deps:
            ref_count[dep] = ref_count.get(dep, 0) + 1
    return [pkg for pkg, count in sorted(ref_count.items()) if count >= threshold]


def topo_sort(packages: list[str], dep_graph: dict[str, set[str]]) -> list[str]:
    """Return packages in topological order (deps before dependents). Kahn's algorithm."""
    pkg_set = set(packages)
    in_degree = {p: 0 for p in packages}
    dependents: dict[str, list[str]] = {p: [] for p in packages}
    for pkg in packages:
        for dep in dep_graph.get(pkg, set()):
            if dep in pkg_set:
                in_degree[pkg] += 1
                dependents[dep].append(pkg)

    queue = sorted(p for p, d in in_degree.items() if d == 0)
    result: list[str] = []
    while queue:
        node = queue.pop(0)
        result.append(node)
        for neighbor in sorted(dependents[node]):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
                queue.sort()

    seen = set(result)
    result.extend(p for p in packages if p not in seen)
    return result


def run_build(
    monolithpy: Path,
    package_name: str,
    pip_cache_dir: Path | None = None,
    find_links_dir: Path | None = None,
) -> tuple[bool, dict[str, str]]:
    """Attempt to build a package. Returns (success, packages_dict)."""
    packages = defaultdict(list)

    cmd = [str(monolithpy), "-m", "pip", "install", "--verbose"]
    if pip_cache_dir is not None:
        pip_cache_dir.mkdir(parents=True, exist_ok=True)
        cmd += ["--cache-dir", str(pip_cache_dir)]
    if find_links_dir is not None and find_links_dir.is_dir():
        cmd += ["--find-links", str(find_links_dir)]
    cmd += [package_name]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
        )

        for line in process.stdout:
            print(line, end='', flush=True)

            wheel_match = re.search(r'(?:Downloading|Using cached)\s+(\S+\.whl)', line)
            if wheel_match:
                wheel_name = wheel_match.group(1)
                parts_match = re.match(r'([A-Za-z0-9_][A-Za-z0-9._-]*)-(\d+[A-Za-z0-9._]*)-', wheel_name)
                if parts_match:
                    pkg_name = parts_match.group(1).lower().replace('_', '-')
                    version = parts_match.group(2)
                    packages[pkg_name].append(version)
                continue

            tarball_match = re.search(r'(?:Downloading|Using cached)\s+([A-Za-z0-9_][A-Za-z0-9._-]*)-(\d+[A-Za-z0-9._]*)\.(?:tar\.gz|zip)', line)
            if tarball_match:
                pkg_name = tarball_match.group(1).lower().replace('_', '-')
                version = tarball_match.group(2)
                packages[pkg_name].append(version)
                continue

            if 'Successfully installed' in line:
                for match in re.finditer(r'([A-Za-z0-9_][A-Za-z0-9._-]*)-(\d+[A-Za-z0-9._]*)', line):
                    pkg_name = match.group(1).lower().replace('_', '-')
                    version = match.group(2)
                    packages[pkg_name].append(version)

        process.wait()

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

    if platform.system() == "Windows":
        platform_suffix = "mp313-windows"
    elif platform.system() == "Darwin":
        platform_suffix = "mp313-macos"
    else:
        print(f"Unsupported platform: {platform.system()}", file=sys.stderr)
        sys.exit(1)

    packages_dir    = root_dir / "packages"     / platform_suffix
    dependencies_dir = root_dir / "dependencies" / platform_suffix
    build_tools_dir  = root_dir / "build_tools"  / platform_suffix

    constraints_dir = root_dir / "constraints"
    constraints_dir.mkdir(exist_ok=True)
    built_wheels_dir = root_dir / "built_wheels"
    built_wheels_dir.mkdir(exist_ok=True)
    pip_cache_base = root_dir / ".pip-wheel-cache"

    monolithpy = get_monolithpy_executable(monolithpy_dir)
    print(f"MonolithPy location: {monolithpy}")
    if not monolithpy.exists():
        print(f"::error::MonolithPy executable not found at {monolithpy}", file=sys.stderr)
        sys.exit(1)

    pristine_dir = root_dir / "monolithpy_pristine"
    shutil.copytree(monolithpy_dir, pristine_dir, dirs_exist_ok=True)

    ensurepip_packages = get_ensurepip_package_names(monolithpy)
    print(f"Excluding ensurepip packages: {ensurepip_packages}")

    work_monolithpy = root_dir / "monolithpy_work"

    # Full catalog across packages/, dependencies/, build_tools/
    catalog = build_catalog(packages_dir, dependencies_dir, build_tools_dir)
    dep_graph = build_dep_graph(catalog)

    prebuild_mode = os.environ.get("PREBUILD_MODE", "").lower() == "true"
    round1_wheels_dir_env = os.environ.get("ROUND1_WHEELS_DIR", "")
    round1_wheels_dir = Path(round1_wheels_dir_env) if round1_wheels_dir_env else None

    if prebuild_mode:
        # Round 1: build packages that are deps of 2+ others, in topo order.
        # The dep graph spans packages/, dependencies/, and build_tools/ so
        # mpy-tool-clang, mpy-dep-openblas, numpy, scipy, etc. are all candidates.
        candidates = find_prebuild_candidates(dep_graph, threshold=2)
        all_packages = topo_sort(candidates, dep_graph)
        print(f"Round 1 (pre-build): {len(all_packages)} shared deps in order: {all_packages}")
    else:
        # Round 2: build only the top-level packages/; deps and tools come from
        # the Round 1 --find-links dir or are built on-demand by pip.
        all_packages = sorted(d.name for d in _iter_subdirs(packages_dir))
        split_total = int(os.environ.get("SPLIT_TOTAL", "1"))
        split_index = int(os.environ.get("SPLIT_INDEX", "0"))
        if split_total > 1:
            all_packages = [p for i, p in enumerate(all_packages) if i % split_total == split_index]
            print(f"Round 2, split {split_index+1}/{split_total}: {len(all_packages)} packages: {all_packages}")
        if round1_wheels_dir:
            print(f"Using Round 1 pre-built wheels from: {round1_wheels_dir}")

    for pkg_name in all_packages:
        pkg_dir = catalog[pkg_name]
        print(f"::group::Building {pkg_name}")

        if work_monolithpy.exists():
            rmtree_force(work_monolithpy)
        shutil.copytree(pristine_dir, work_monolithpy)

        monolithpy = get_monolithpy_executable(work_monolithpy)
        run_rebuild(monolithpy)

        pip_cache_dir = pip_cache_base / pkg_name

        # Round 1: --find-links points at built_wheels/ so each candidate can
        # reuse wheels produced by earlier packages in the same topo-ordered run
        # (e.g. scipy finds numpy and mpy-dep-openblas already there).
        # Round 2: --find-links points at the downloaded Round 1 artifact dir.
        find_links_dir = built_wheels_dir if prebuild_mode else round1_wheels_dir

        print(f"Building {pkg_name}...")
        success, installed_packages = run_build(
            monolithpy, pkg_name,
            pip_cache_dir=pip_cache_dir,
            find_links_dir=find_links_dir,
        )
        if not success:
            print(f"::error::Build failed for {pkg_name}")
            print("::endgroup::")
            sys.exit(1)

        print(f"Build successful for {pkg_name}")
        collect_built_wheels(pip_cache_dir, built_wheels_dir)

        write_constraint_file(pkg_name, installed_packages, constraints_dir, ensurepip_packages)

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
