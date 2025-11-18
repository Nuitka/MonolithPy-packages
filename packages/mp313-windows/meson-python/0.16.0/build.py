import __np__
import glob
import shutil
import sys
import os
import setuptools.build_meta


def run(wheel_directory):
    __np__.setup_compiler_env()

    __np__.run_build_tool_exe("patch", "patch.exe", "-t", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "meson_python-static-patch.patch"))

    __np__.run_with_output(sys.executable, "-m", "build", "-w", "--no-isolation")

    __np__.run_with_output(sys.executable, "-m", "build", "-w", "--no-isolation")

    wheel_location = glob.glob(os.path.join("dist", "meson_python-*.whl"))[0]
    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
