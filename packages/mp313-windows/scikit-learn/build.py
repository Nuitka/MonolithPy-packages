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

    # Loosen some requirement constraints to make things easier for us.
    pyproject = pyproject.replace("numpy>=2,<2.4.0", "numpy>=2")
    pyproject = pyproject.replace("scipy>=1.10.0,<1.17.0", "scipy>=1.10.0")

    with open("pyproject.toml", "w") as f:
        f.write(pyproject)

    env = os.environ.copy()
    env["CC"] = os.path.dirname(__mp__.find_build_tool_exe("clang", "clang-cl.exe"))
    env["CC_LD"] = os.path.dirname(__mp__.find_build_tool_exe("clang", "lld-link.exe"))
    env["CXX"] = os.path.dirname(__mp__.find_build_tool_exe("clang", "lld-link.exe"))
    env["CXX_LD"] = os.path.dirname(__mp__.find_build_tool_exe("clang", "clang-cl.exe"))
    env["PATH"] = (
                os.path.dirname(__mp__.find_build_tool_exe("clang", "lld-link.exe")) + os.pathsep + os.environ["PATH"])
    with TemporaryDirectory() as temp_dir:
        __mp__.run(sys.executable, "-m", "pip", "wheel", ".", "-v",
                   "--config-settings=compile-args=-j3", "--config-settings=build-dir=" + temp_dir, env=env)

    wheel_location = glob.glob("scikit_learn-*.whl")[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        __mp__.analyze_and_rename_library_symbols(tmpdir,
                                                  "scikit_learn")
        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
