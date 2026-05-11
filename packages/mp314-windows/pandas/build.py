import __mp__
import glob
import shutil
import sys
import os
import tempfile
from tempfile import TemporaryDirectory

from wheel.wheelfile import WheelFile


def run(wheel_directory):
    __mp__.setup_compiler_env()

    __mp__.run_build_tool_exe("patch", "patch.exe", "-p1", "-ui",
                              os.path.join(os.path.dirname(__file__), "pandas-static-patch.patch"))

    os.environ["GITHUB_ACTIONS"] = "true"

    pip_base_path = __mp__.get_pip_base_path()

    # Wrap meson via the MESON env var so we can guarantee PYTHONPATH is set
    # for all subprocesses (including cython) that meson spawns.
    # Also patches CythonCompiler to add /FORCE:UNRESOLVED for the sanity-check
    # DLL link: python313.lib is a full static lib whose Windows system DLL
    # dependencies are not provided in the test link. The DLL is never executed
    # (_run_sanity_check returns immediately), so forcing is safe.
    _meson_wrap_dir = tempfile.mkdtemp(prefix="meson_wrap_")
    if pip_base_path:
        _real_meson = os.path.join(pip_base_path, "Scripts", "meson.exe")
        _overlay_site = os.path.join(pip_base_path, "Lib", "site-packages")
        _meson_wrapper_py = os.path.join(_meson_wrap_dir, "meson_wrapper.py")
        with open(_meson_wrapper_py, "w") as _f:
            _f.write(f"""
import subprocess, sys, os, glob as _glob, shutil

_overlay_root = r"{_overlay_site}"
_cython_candidates = _glob.glob(os.path.join(_overlay_root, "**", "compilers", "cython.py"), recursive=True)
sys.stderr.write(f"[meson_wrapper] cython.py search in {{_overlay_root!r}}: {{_cython_candidates}}\\n")
_cython_py = _cython_candidates[0] if _cython_candidates else None
_cython_backup = None
_OLD = "        largs.extend(compiler.get_allow_undefined_link_args())\\n        return args, largs"
_NEW = ("        largs.extend(compiler.get_allow_undefined_link_args())\\n"
        "        if self.environment.machines[self.for_machine].is_windows():\\n"
        "            largs.append('/FORCE:UNRESOLVED')\\n"
        "        return args, largs")
if _cython_py:
    with open(_cython_py, "r") as _f:
        _cython_backup = _f.read()
    if _OLD in _cython_backup:
        with open(_cython_py, "w") as _f:
            _f.write(_cython_backup.replace(_OLD, _NEW))
        sys.stderr.write(f"[meson_wrapper] patched {{_cython_py}} with /FORCE:UNRESOLVED\\n")
    else:
        sys.stderr.write(f"[meson_wrapper] WARNING: cython.py patch target not found in {{_cython_py}}\\n")
        _cython_backup = None
else:
    sys.stderr.write("[meson_wrapper] WARNING: cython.py not found in overlay\\n")

existing = os.environ.get("PYTHONPATH", "")
os.environ["PYTHONPATH"] = r"{_overlay_site}" + (os.pathsep + existing if existing else "")
try:
    result = subprocess.run([r"{_real_meson}"] + sys.argv[1:])
finally:
    if _cython_backup is not None:
        with open(_cython_py, "w") as _f:
            _f.write(_cython_backup)
        sys.stderr.write("[meson_wrapper] restored cython.py\\n")
if result.returncode != 0:
    try:
        build_dir = sys.argv[sys.argv.index("setup") + 2] if "setup" in sys.argv else "."
        for log in _glob.glob(os.path.join(build_dir, "meson-logs", "meson-log.txt")):
            dest = r"{_meson_wrap_dir}\\meson-log.txt"
            shutil.copy(log, dest)
            sys.stderr.write(f"[meson_wrapper] copied meson log to {{dest}}\\n")
    except Exception as e:
        sys.stderr.write(f"[meson_wrapper] could not copy log: {{e}}\\n")
sys.exit(result.returncode)
""")
        os.environ["MESON"] = _meson_wrapper_py
        sys.stderr.write(f"[build.py] meson wrapper at {_meson_wrapper_py}, real meson={_real_meson!r}\n")

    job_args = []
    if "MP_JOBS" in os.environ:
        job_args += [f"-Ccompile-args=-j{os.environ['MP_JOBS']}"]

    try:
        __mp__.run(sys.executable, "-m", "build", "-w", "--no-isolation", *job_args)
    finally:
        _meson_log = os.path.join(_meson_wrap_dir, "meson-log.txt")
        if os.path.exists(_meson_log):
            with open(_meson_log) as _f:
                sys.stderr.write(f"[meson-log.txt]:\n{_f.read()}\n")
        import shutil as _shutil
        _shutil.rmtree(_meson_wrap_dir, ignore_errors=True)

    wheel_location = glob.glob(os.path.join("dist", "pandas-*.whl"))[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        __mp__.analyze_and_rename_library_symbols(tmpdir, "pandas")
        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
