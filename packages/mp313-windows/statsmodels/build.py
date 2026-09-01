import __mp__
import glob
import shutil
import sys
import os
from tempfile import TemporaryDirectory

import setuptools.build_meta
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    # statsmodels 0.15.0 switched from a setuptools build to the meson-python
    # backend, so the recipe now needs the same meson-on-MonolithPy plumbing
    # scipy uses: a clang-cl compiler env, numpy's headers for the `cimport
    # numpy` extensions, and -- critically -- a meson wrapper that injects
    # /FORCE:UNRESOLVED into cython's compiler sanity-check link. Without that,
    # meson's "can cython compile programs?" probe links MonolithPy's
    # python3xx.lib (whose extension objects reference mp_* VFS shims and system
    # DLLs not present in the throwaway probe link) and fails with
    # "Compiler cython cannot compile programs" / unresolved mp_fprintf.
    # statsmodels has no Fortran and links no BLAS at build time (its meson.build
    # only does a `cy.compiles` probe of scipy.linalg.cython_blas), so the
    # Fortran/openblas parts of scipy's recipe are intentionally omitted.
    __mp__.setup_compiler_env()

    __mp__.run_build_tool_exe("patch", "patch.exe", "-t", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "statsmodels-static-patch.patch"))

    os.environ["CC"] = __mp__.find_build_tool_exe("clang", "clang-cl.exe")
    os.environ["CC_LD"] = "lld-link"
    os.environ["CXX"] = __mp__.find_build_tool_exe("clang", "clang-cl.exe")
    os.environ["CXX_LD"] = "lld-link"
    os.environ["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep +
                          os.path.dirname(__mp__.find_build_tool_exe("clang", "lld-link.exe")) + os.pathsep +
                          os.environ["PATH"])
    # statsmodels' Cython extensions `cimport numpy`; meson resolves numpy via
    # its dependency, but add the include explicitly so the compiler probes and
    # extension compiles find numpy/arrayobject.h regardless.
    import numpy as _numpy
    os.environ["INCLUDE"] = os.environ["INCLUDE"] + os.pathsep + _numpy.get_include()
    os.environ["GITHUB_ACTIONS"] = "true"

    pip_base_path = __mp__.get_pip_base_path()
    # Wrap meson via the MESON env var so we can guarantee PYTHONPATH is set
    # for all subprocesses (including cython) that meson spawns, and patch
    # cython's sanity-check link to tolerate unresolved symbols (see above).
    # On Windows, subprocess.Popen does not run .bat/.cmd wrappers, so a
    # PATH-based cython.bat approach does not work. mesonpy supports a MESON
    # env var: if it ends with ".py", mesonpy calls it as
    # `sys.executable wrapper.py <args>`, making it reliably executable.
    import tempfile as _tmpfile
    _meson_wrap_dir = _tmpfile.mkdtemp(prefix="meson_wrap_")
    if pip_base_path:
        _real_meson = os.path.join(pip_base_path, "Scripts", "meson.exe")
        _overlay_site = os.path.join(pip_base_path, "Lib", "site-packages")
        _meson_wrapper_py = os.path.join(_meson_wrap_dir, "meson_wrapper.py")
        with open(_meson_wrapper_py, "w") as _f:
            _f.write(f"""
import subprocess, sys, os, glob, shutil

# Patch mesonbuild's CythonCompiler in the overlay to inject /FORCE:UNRESOLVED
# into the sanity-check DLL link. MonolithPy's python3xx.lib is a full static
# lib containing all extension modules; those modules reference Windows system
# DLLs (advapi32, kernel32, etc.) and mp_* VFS shims that aren't provided in the
# test DLL link. Since _run_sanity_check() returns immediately (DLL is never
# executed), forcing the link to succeed with unresolved symbols is safe.
import glob as _glob
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

# Ensure PYTHONPATH includes the overlay site-packages so cython.exe can
# import Cython.  When meson calls cython as a subprocess, it inherits this.
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
    # Copy meson log to a stable location for diagnosis
    try:
        build_dir = sys.argv[sys.argv.index("setup") + 2] if "setup" in sys.argv else "."
        for log in glob.glob(os.path.join(build_dir, "meson-logs", "meson-log.txt")):
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
        job_args += ["-Ccompile-args=-j" + os.environ["MP_JOBS"]]
    try:
        __mp__.run(sys.executable, "-m", "build", "-w", "--no-isolation",
                   "-Csetup-args=-Db_vscrt=mt", *job_args)
    finally:
        _meson_log = os.path.join(_meson_wrap_dir, "meson-log.txt")
        if os.path.exists(_meson_log):
            with open(_meson_log) as _f:
                sys.stderr.write(f"[meson-log.txt]:\n{_f.read()}\n")
        import shutil as _shutil
        _shutil.rmtree(_meson_wrap_dir, ignore_errors=True)

    wheel_location = glob.glob(os.path.join("dist", "statsmodels-*.whl"))[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        __mp__.analyze_and_rename_library_symbols(tmpdir, "statsmodels")
        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
