import __mp__
import glob
import shutil
import sys
import os
import setuptools.build_meta
from tempfile import TemporaryDirectory

from wheel.wheelfile import WheelFile


def run(wheel_directory):
    __mp__.setup_compiler_env()

    __mp__.run_build_tool_exe("patch", "patch.exe", "-p1", "-ui",
                              os.path.join(os.path.dirname(__file__), "scikit_learn-static-patch.patch"))

    with open("pyproject.toml", "r") as f:
        pyproject = f.read()

    pyproject = pyproject.replace("numpy>=2,<2.4.0", "numpy>=2")
    pyproject = pyproject.replace("scipy>=1.10.0,<1.17.0", "scipy>=1.10.0")
    pyproject = pyproject.replace("meson-python>=0.17.1,<0.19.0", "meson-python>=0.17.1")

    with open("pyproject.toml", "w") as f:
        f.write(pyproject)

    # clang-cl defines _MSC_VER, so MurmurHash3.h's pre-stdint typedef block
    # redefines uint32_t as 'unsigned long', clashing with stdint.h's
    # 'unsigned int' (typedef redefinition with different types). Gate the
    # manual typedefs on the MSVC era that actually lacked stdint.h (< 1600);
    # clang-cl and modern MSVC then fall through to '#include <stdint.h>'.
    _mmh = os.path.join("sklearn", "utils", "src", "MurmurHash3.h")
    with open(_mmh, "r") as f:
        _mmh_src = f.read()
    with open(_mmh, "w") as f:
        f.write(_mmh_src.replace("#if defined(_MSC_VER)",
                                 "#if defined(_MSC_VER) && (_MSC_VER < 1600)", 1))

    os.environ["CC"] = __mp__.find_build_tool_exe("clang", "clang-cl.exe")
    os.environ["CC_LD"] = "lld-link"
    os.environ["CXX"] = __mp__.find_build_tool_exe("clang", "clang-cl.exe")
    os.environ["CXX_LD"] = "lld-link"
    os.environ["PATH"] = (
        os.path.dirname(__mp__.find_build_tool_exe("clang", "lld-link.exe")) + os.pathsep +
        os.environ["PATH"]
    )
    import numpy as _numpy
    os.environ["INCLUDE"] = os.environ.get("INCLUDE", "") + os.pathsep + _numpy.get_include()

    pip_base_path = __mp__.get_pip_base_path()
    if pip_base_path:
        overlay_site = os.path.join(pip_base_path, "Lib", "site-packages")
        existing_pythonpath = os.environ.get("PYTHONPATH", "")
        os.environ["PYTHONPATH"] = overlay_site + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
        overlay_scripts = os.path.join(pip_base_path, "Scripts")
        if os.path.isdir(overlay_scripts):
            os.environ["PATH"] = overlay_scripts + os.pathsep + os.environ["PATH"]

    import tempfile as _tmpfile
    _meson_wrap_dir = _tmpfile.mkdtemp(prefix="meson_wrap_")
    if pip_base_path:
        _real_meson = os.path.join(pip_base_path, "Scripts", "meson.exe")
        _overlay_site = os.path.join(pip_base_path, "Lib", "site-packages")
        _meson_wrapper_py = os.path.join(_meson_wrap_dir, "meson_wrapper.py")
        with open(_meson_wrapper_py, "w") as _f:
            _f.write(f"""
import subprocess, sys, os, glob, shutil

import glob as _glob
_overlay_root = r"{_overlay_site}"
_cython_candidates = _glob.glob(os.path.join(_overlay_root, "**", "compilers", "cython.py"), recursive=True)
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
    else:
        _cython_backup = None

existing = os.environ.get("PYTHONPATH", "")
os.environ["PYTHONPATH"] = r"{_overlay_site}" + (os.pathsep + existing if existing else "")
try:
    result = subprocess.run([r"{_real_meson}"] + sys.argv[1:])
finally:
    if _cython_backup is not None:
        with open(_cython_py, "w") as _f:
            _f.write(_cython_backup)
if result.returncode != 0:
    try:
        build_dir = sys.argv[sys.argv.index("setup") + 2] if "setup" in sys.argv else "."
        for log in glob.glob(os.path.join(build_dir, "meson-logs", "meson-log.txt")):
            dest = r"{_meson_wrap_dir}\\meson-log.txt"
            shutil.copy(log, dest)
    except Exception:
        pass
sys.exit(result.returncode)
""")
        os.environ["MESON"] = _meson_wrapper_py

    import subprocess as _subprocess
    _short_src = "C:\\T\\sklearn_src"
    os.makedirs("C:\\T", exist_ok=True)
    if os.path.exists(_short_src):
        _subprocess.run(["cmd", "/c", "rmdir", _short_src], check=False)
    _src_dir = os.getcwd()
    _subprocess.run(["cmd", "/c", "mklink", "/J", _short_src, _src_dir], check=True)
    os.chdir(_short_src)

    job_args = []
    if "MP_JOBS" in os.environ:
        job_args += ["-Ccompile-args=-j" + os.environ["MP_JOBS"]]
    try:
        __mp__.run(sys.executable, "-m", "build", "-w", "--no-isolation",
                   "-Csetup-args=-Db_vscrt=mt", *job_args)
    finally:
        os.chdir(_src_dir)
        _subprocess.run(["cmd", "/c", "rmdir", _short_src], check=False)
        import shutil as _shutil
        _shutil.rmtree(_meson_wrap_dir, ignore_errors=True)

    wheel_location = glob.glob(os.path.join(_src_dir, "dist", "scikit_learn-*.whl"))[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        __mp__.analyze_and_rename_library_symbols(tmpdir, "scikit_learn")
        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
