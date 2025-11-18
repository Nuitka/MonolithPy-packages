import __np__
import glob
import shutil
import sys
import os
from tempfile import TemporaryDirectory

import setuptools.build_meta
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    __np__.setup_compiler_env()

    __np__.run_build_tool_exe("patch", "patch.exe", "-t", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "pillow-static-patch.patch"))

    env = os.environ.copy()
    env["JPEG_ROOT"] = __np__.find_dep_root("jpeg")
    env["TIFF_ROOT"] = __np__.find_dep_root("tiff")
    env["ZLIB_ROOT"] = __np__.find_dep_root("zlib")
    env["FREETYPE_ROOT"] = __np__.find_dep_root("freetype")
    env["HARFBUZZ_ROOT"] = __np__.find_dep_root("harfbuzz")

    env["PEP517_BACKEND_PATH"] = os.pathsep.join([x for x in sys.path if not x.endswith(os.path.sep + "site")])
    __np__.run_with_output(sys.executable, "-m", "build", "-w", "--no-isolation", "-C", "jpeg=enable",
                           "-C", "tiff=disable", "-C", "zlib=enable", "-C", "freetype=enable", "-C", "harfbuzz=enable",
                           "-C", "raqm=vendor", "-C", "fribidi=vendor", env=env)

    wheel_location = glob.glob(os.path.join("dist", "pillow-*.whl"))[0]
    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
