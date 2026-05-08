import __mp__
import glob
import shutil
import sys
import os
from tempfile import TemporaryDirectory

import setuptools.build_meta
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    __mp__.setup_compiler_env()

    __mp__.run_build_tool_exe("patch", "patch.exe", "-t", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "pillow-static-patch.patch"))

    env = os.environ.copy()
    env["JPEG_ROOT"] = __mp__.find_dep_root("jpeg")
    env["TIFF_ROOT"] = __mp__.find_dep_root("tiff")
    env["ZLIB_ROOT"] = __mp__.find_dep_root("zlib")
    env["FREETYPE_ROOT"] = __mp__.find_dep_root("freetype")
    env["HARFBUZZ_ROOT"] = __mp__.find_dep_root("harfbuzz")

    __mp__.run_with_output(sys.executable, "-m", "build", "-w", "--no-isolation", "-o", ".",
                           "-Cjpeg=enable",
                           "-Ctiff=disable", "-Czlib=enable",
                           "-Cfreetype=enable", "-Charfbuzz=enable",
                           "-Craqm=vendor", "-Cfribidi=vendor", env=env)

    wheel_location = glob.glob("pillow-*.whl")[0]
    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
