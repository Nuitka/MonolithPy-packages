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

    env["PEP517_BACKEND_PATH"] = os.pathsep.join([x for x in sys.path if not x.endswith(os.path.sep + "site")])
    __mp__.run_with_output(sys.executable, "-m", "pip", "wheel", ".", "-v",
                           "--config-settings=jpeg=enable",
                           "--config-settings=tiff=disable", "--config-settings=zlib=enable",
                           "--config-settings=freetype=enable", "--config-settings=harfbuzz=enable",
                           "--config-settings=raqm=vendor", "--config-settings=fribidi=vendor",
                           "--config-settings=lcms=disable", "--config-settings=webp=disable",
                           "--config-settings=jpeg2000=disable", "--config-settings=imagequant=disable",
                           "--config-settings=xcb=disable", env=env)

    wheel_location = glob.glob("pillow-*.whl")[0]
    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
