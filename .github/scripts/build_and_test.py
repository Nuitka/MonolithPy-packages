#!/usr/bin/env python3
"""Build and test MonolithPy packages (any mp3XX)."""

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Unbuffered output for CI environments
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)


_TAG_RE = re.compile(r"^mp(?P<major>\d)(?P<minor>\d+)$")


def parse_python_version(tag: str) -> tuple[int, int]:
    """Derive (major, minor) from a tag like 'mp313' or 'mp314'."""
    m = _TAG_RE.match(tag)
    if not m:
        raise ValueError(f"Invalid MonolithPy tag {tag!r}; expected 'mp<major><minor>' (e.g. 'mp313')")
    return int(m.group("major")), int(m.group("minor"))


def get_monolithpy_executable(monolithpy_dir: Path, python_version: tuple[int, int]) -> Path:
    """Get the MonolithPy executable path."""
    if platform.system() == "Windows":
        return monolithpy_dir / "python.exe"
    else:
        return monolithpy_dir / "bin" / f"python{python_version[0]}.{python_version[1]}"


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


def purge_caches(pip_cache_dir: Path, work_dir: Path):
    """Reclaim disk between prebuild tiers."""
    import tempfile
    if pip_cache_dir.exists():
        rmtree_force(pip_cache_dir)
    mpy_cache = Path(os.environ.get("MPY_WHEEL_CACHE_DIR",
                     os.path.join(tempfile.gettempdir(), "mpy-wheel-cache")))
    if mpy_cache.exists():
        rmtree_force(mpy_cache)
    if work_dir.exists():
        rmtree_force(work_dir)


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
        # packages/ use scripts[0] format; dependencies/ and build_tools/ use top-level fields
        scripts = data.get("scripts", [])
        script = scripts[0] if scripts else {}

        def add_edge(norm_target: str) -> None:
            if norm_target in norm_map and norm_map[norm_target] != pip_name:
                graph[pip_name].add(norm_map[norm_target])

        # Regular pip requirements (build_requires / dist_requires)
        for req in (script.get("build_requires") or data.get("build_requires", [])) + \
                   (script.get("dist_requires") or data.get("dist_requires", [])):
            bare = re.split(r'[>=<!;\[\s,]', req.strip())[0]
            add_edge(normalize_pkg_name(bare))

        # MonolithPy dependency packages  →  "mpy-dep-{name}"
        for dep in (script.get("dependencies") or data.get("dependencies", [])):
            add_edge(normalize_pkg_name(f"mpy-dep-{dep}"))

        # MonolithPy build tool packages  →  "mpy-tool-{name}"
        for tool in (script.get("build_tools") or data.get("build_tools", [])):
            add_edge(normalize_pkg_name(f"mpy-tool-{tool}"))

    return graph


def get_build_files(pkg_dir: Path) -> list[Path]:
    """Return sorted build files in pkg_dir, excluding test files."""
    excluded = set()
    index_path = pkg_dir / "index.json"
    if index_path.exists():
        try:
            with open(index_path) as f:
                excluded.update(json.load(f).get("tests", []))
        except (json.JSONDecodeError, OSError):
            pass

    return sorted(
        f for f in pkg_dir.rglob("*")
        if f.is_file() and f.name not in excluded
    )


def compute_cache_keys(
    catalog: dict[str, Path],
    dep_graph: dict[str, set[str]],
    platform_suffix: str,
) -> dict[str, str]:
    """Compute a deterministic cache key per package.

    Each key incorporates the SHA-256 of all build files in the package
    directory (excluding tests) plus, recursively, the keys of all
    transitive dependencies.
    """
    import hashlib

    own_hashes: dict[str, str] = {}
    for pip_name, pkg_dir in catalog.items():
        h = hashlib.sha256()
        for f in get_build_files(pkg_dir):
            h.update(str(f.relative_to(pkg_dir)).encode())
            h.update(f.read_bytes())
        own_hashes[pip_name] = h.hexdigest()

    all_sorted = topo_sort(list(catalog.keys()), dep_graph)
    full_hashes: dict[str, str] = {}
    for pip_name in all_sorted:
        h = hashlib.sha256()
        h.update(own_hashes[pip_name].encode())
        for dep in sorted(dep_graph.get(pip_name, set())):
            if dep in full_hashes:
                h.update(full_hashes[dep].encode())
        full_hashes[pip_name] = h.hexdigest()

    return {
        pip_name: f"{platform_suffix}-{pip_name}-{full_hashes[pip_name][:16]}"
        for pip_name in catalog
    }


def try_restore_from_cache(
    pkg_name: str,
    cache_key: str,
    wheel_cache_dir: Path,
    built_wheels_dir: Path,
) -> bool:
    """If a cached build exists for this exact cache key, copy wheels out
    and return True.  Otherwise return False."""
    marker = wheel_cache_dir / f"{cache_key}.marker"
    if not marker.exists():
        return False
    try:
        whl_names = json.loads(marker.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    if not all((wheel_cache_dir / w).exists() for w in whl_names):
        return False
    for w in whl_names:
        dest = built_wheels_dir / w
        if not dest.exists():
            shutil.copy2(wheel_cache_dir / w, dest)
    return True


def save_to_cache(
    cache_key: str,
    new_wheels: set[str],
    wheel_cache_dir: Path,
    built_wheels_dir: Path,
):
    """Persist newly-built wheels and write a marker so future runs can
    restore them."""
    wheel_cache_dir.mkdir(parents=True, exist_ok=True)
    whl_list = sorted(new_wheels)
    for w in whl_list:
        src = built_wheels_dir / w
        if src.exists():
            shutil.copy2(src, wheel_cache_dir / w)
    (wheel_cache_dir / f"{cache_key}.marker").write_text(json.dumps(whl_list))


def find_prebuild_candidates(dep_graph: dict[str, set[str]], threshold: int = 2) -> list[str]:
    """Return packages that appear as a dep of at least `threshold` others, plus all their transitive deps."""
    ref_count: dict[str, int] = {}
    for deps in dep_graph.values():
        for dep in deps:
            ref_count[dep] = ref_count.get(dep, 0) + 1
    candidates = {p for p, c in ref_count.items() if c >= threshold}
    # Expand transitively so deps-of-deps (e.g. flang→miniconda) are also pre-built
    queue = list(candidates)
    while queue:
        pkg = queue.pop()
        for dep in dep_graph.get(pkg, set()):
            if dep not in candidates:
                candidates.add(dep)
                queue.append(dep)
    return sorted(candidates)


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
) -> bool:
    """Attempt to build a package. Returns True on success."""
    cmd = [str(monolithpy), "-m", "pip", "install", "--verbose"]
    if pip_cache_dir is not None:
        pip_cache_dir.mkdir(parents=True, exist_ok=True)
        cmd += ["--cache-dir", str(pip_cache_dir)]
    if find_links_dir is not None and find_links_dir.is_dir():
        cmd += ["--find-links", str(find_links_dir)]
    cmd += [package_name]

    env = os.environ.copy()
    if find_links_dir is not None and find_links_dir.is_dir():
        env["PIP_FIND_LINKS"] = str(find_links_dir)

    try:
        result = subprocess.run(cmd, env=env)
        return result.returncode == 0
    except Exception as e:
        print(f"Build error: {e}", file=sys.stderr)
        return False


def run_test(monolithpy: Path, test_path: Path) -> bool:
    """Run a test file. Returns True on success."""
    try:
        result = subprocess.run([str(monolithpy), str(test_path)])
    except Exception as e:
        print(f"Test error: {e}", file=sys.stderr)
        return False
    rc = result.returncode
    if rc == 0:
        return True
    if rc < 0:
        print(f"Test killed by signal {-rc}", file=sys.stderr)
    else:
        print(f"Test exited with code {rc}", file=sys.stderr)
    return False


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--prebuild", metavar="TIER",
                        help="Run a pre-build tier: tools, deps, heavy, or 'all' for every tier.")
    parser.add_argument("--round2", nargs=2, metavar=("INDEX", "TOTAL"),
                        help="Run round 2 with the given split INDEX out of TOTAL.")
    parser.add_argument("--round1-wheels", metavar="DIR",
                        help="Directory containing Round 1 pre-built wheels.")
    parser.add_argument("--wheel-cache-dir", metavar="DIR",
                        help="Directory for wheel cache (persisted via actions/cache).")
    parser.add_argument("--monolithpy-tag", metavar="TAG",
                        default=os.environ.get("MONOLITHPY_TAG"),
                        help="MonolithPy Python version tag (e.g. 'mp313', 'mp314'). "
                             "Defaults to $MONOLITHPY_TAG.")
    args = parser.parse_args()

    if not args.monolithpy_tag:
        print("Error: --monolithpy-tag or MONOLITHPY_TAG env var is required "
              "(e.g. 'mp313', 'mp314').", file=sys.stderr)
        sys.exit(1)
    python_version = parse_python_version(args.monolithpy_tag)

    root_dir = Path.cwd()
    monolithpy_dir = root_dir / "monolithpy"

    if platform.system() == "Windows":
        platform_suffix = f"{args.monolithpy_tag}-windows"
    elif platform.system() == "Darwin":
        platform_suffix = f"{args.monolithpy_tag}-macos"
    else:
        print(f"Unsupported platform: {platform.system()}", file=sys.stderr)
        sys.exit(1)

    packages_dir    = root_dir / "packages"     / platform_suffix
    dependencies_dir = root_dir / "dependencies" / platform_suffix
    build_tools_dir  = root_dir / "build_tools"  / platform_suffix

    built_wheels_dir = root_dir / "built_wheels"
    built_wheels_dir.mkdir(exist_ok=True)
    pip_cache_base = root_dir / ".pip-wheel-cache"

    monolithpy = get_monolithpy_executable(monolithpy_dir, python_version)
    print(f"MonolithPy location: {monolithpy}")
    if not monolithpy.exists():
        print(f"::error::MonolithPy executable not found at {monolithpy}", file=sys.stderr)
        sys.exit(1)

    pristine_dir = root_dir / "monolithpy_pristine"
    shutil.copytree(monolithpy_dir, pristine_dir, dirs_exist_ok=True)

    work_monolithpy = root_dir / "monolithpy_work"

    # Full catalog across packages/, dependencies/, build_tools/
    catalog = build_catalog(packages_dir, dependencies_dir, build_tools_dir)
    dep_graph = build_dep_graph(catalog)

    wheel_cache_dir = Path(args.wheel_cache_dir) if args.wheel_cache_dir else None
    cache_keys = compute_cache_keys(catalog, dep_graph, platform_suffix) if wheel_cache_dir else {}
    if cache_keys:
        print(f"Computed cache keys for {len(cache_keys)} packages")

    round1_wheels_dir = Path(args.round1_wheels) if args.round1_wheels else None

    if args.prebuild:
        candidates = find_prebuild_candidates(dep_graph, threshold=2)
        all_prebuild = topo_sort(candidates, dep_graph)

        heavy_set = {"numpy", "scipy"}
        tier1 = [p for p in all_prebuild if p.startswith("mpy-tool-")]
        tier1_set = set(tier1)
        tier2 = [p for p in all_prebuild if p not in tier1_set and p not in heavy_set]
        tier3 = [p for p in all_prebuild if p in heavy_set]
        all_tiers = [("tools", tier1), ("deps", tier2), ("heavy", tier3)]
        all_tiers = [(t, pkgs) for t, pkgs in all_tiers if pkgs]

        if args.prebuild == "all":
            tiers = all_tiers
        else:
            tiers = [(t, pkgs) for t, pkgs in all_tiers if t == args.prebuild]
            if not tiers:
                print(f"Unknown tier '{args.prebuild}'; available: {[t for t, _ in all_tiers]}")
                sys.exit(1)

        print(f"Pre-build: {sum(len(p) for _, p in tiers)} packages across {len(tiers)} tiers")
        for tier_label, tier_packages in tiers:
            print(f"  {tier_label}: {tier_packages}")
    else:
        all_packages = sorted(d.name for d in _iter_subdirs(packages_dir))
        if args.round2:
            split_index, split_total = int(args.round2[0]), int(args.round2[1])
            all_packages = [p for i, p in enumerate(all_packages) if i % split_total == split_index]
            print(f"Round 2, split {split_index+1}/{split_total}: {len(all_packages)} packages: {all_packages}")
        if round1_wheels_dir:
            print(f"Using Round 1 pre-built wheels from: {round1_wheels_dir}")
        tiers = [("all", all_packages)]

    for tier_label, tier_packages in tiers:
        if args.prebuild:
            print(f"::group::=== Tier: {tier_label} ({len(tier_packages)} packages) ===")

        # Reset once per tier, carry forward within so tools/deps accumulate.
        if work_monolithpy.exists():
            rmtree_force(work_monolithpy)
        shutil.copytree(pristine_dir, work_monolithpy)

        for pkg_name in tier_packages:
            pkg_dir = catalog[pkg_name]
            print(f"::group::Building {pkg_name}")

            cache_key = cache_keys.get(pkg_name)
            if cache_key and wheel_cache_dir:
                if try_restore_from_cache(pkg_name, cache_key, wheel_cache_dir, built_wheels_dir):
                    print(f"Cache HIT for {pkg_name} (key: {cache_key})")
                    print("::endgroup::")
                    continue
                print(f"Cache MISS for {pkg_name} (key: {cache_key})")

            monolithpy = get_monolithpy_executable(work_monolithpy, python_version)
            run_rebuild(monolithpy)

            pip_cache_dir = pip_cache_base
            find_links_dir = built_wheels_dir if args.prebuild else round1_wheels_dir

            pre_build_wheels = {w.name for w in built_wheels_dir.glob("*.whl")}

            print(f"Building {pkg_name}...")
            success = run_build(
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

            if cache_key and wheel_cache_dir:
                new_wheels = {w.name for w in built_wheels_dir.glob("*.whl")} - pre_build_wheels
                if new_wheels:
                    save_to_cache(cache_key, new_wheels, wheel_cache_dir, built_wheels_dir)
                    print(f"Cached {len(new_wheels)} wheel(s) for {pkg_name}")

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

        if args.prebuild:
            collect_built_wheels(pip_cache_base, built_wheels_dir)
            print(f"Tier {tier_label} complete.")
            print("::endgroup::")


if __name__ == "__main__":
    main()
