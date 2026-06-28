import __mp__
import glob
import shutil
import sys
import os
from tempfile import TemporaryDirectory

import setuptools.build_meta
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    __mp__.patch_all_source(os.getcwd())

    env = os.environ.copy()
    env["JPEG_ROOT"] = __mp__.find_dep_root("jpeg")
    env["TIFF_ROOT"] = __mp__.find_dep_root("tiff")
    env["ZLIB_ROOT"] = __mp__.find_dep_root("base")
    env["FREETYPE_ROOT"] = __mp__.find_dep_root("base")
    env["HARFBUZZ_ROOT"] = __mp__.find_dep_root("base")
    # Use the shared mpy-dep-raqm (SheenBidi-based) instead of pillow's
    # vendored raqm, so pillow and matplotlib build against one raqm source.
    env["RAQM_ROOT"] = __mp__.find_dep_root("raqm")

    __mp__.run_with_output(sys.executable, "-m", "build", "-w", "--no-isolation", "-o", ".",
                           "-Cjpeg=enable",
                           "-Ctiff=disable", "-Czlib=enable",
                           "-Cfreetype=enable", "-Charfbuzz=enable",
                           "-Craqm=enable",
                           "-Clcms=disable", "-Cwebp=disable",
                           "-Cjpeg2000=disable", "-Cimagequant=disable",
                           "-Cxcb=disable", env=env)

    wheel_location = glob.glob("pillow-*.whl")[0]
    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
