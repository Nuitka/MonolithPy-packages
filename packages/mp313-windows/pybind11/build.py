import __mp__
import glob
import shutil
import sys
import os
import setuptools.build_meta


def run(wheel_directory):
    __mp__.setup_compiler_env()

    base_dir = os.getcwd()
    if not os.path.exists(os.path.join(base_dir, "include")) and os.path.exists(os.path.join(base_dir, "pybind11")):
        base_dir = os.path.join(base_dir, "pybind11")

    __mp__.run_build_tool_exe("patch", "patch.exe", "-t", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "pybind11-static-patch.patch"),
                              cwd=base_dir)

    __mp__.run_with_output(sys.executable, "-m", "pip", "wheel", ".", "-v")

    wheel_location = glob.glob(os.path.join("dist", "pybind11-*.whl"))[0]
    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
