import __mp__
from typing import *

import os
import sysconfig
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    prefix_dir = os.path.join(src_dir, "prefix")
    os.mkdir(prefix_dir)
    os.chdir(src_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    os.environ["CFLAGS"] = sysconfig.get_config_var("CFLAGS")
    print("bash", os.path.join(src_dir, "configure"), "--disable-shared", "--with-zlib-prefix=" + __mp__.find_dep_root("zlib"))
    __mp__.run_with_output("bash", os.path.join(src_dir, "configure"), "--disable-shared", "--with-zlib-prefix=" + __mp__.find_dep_root("zlib"), "--prefix=" + prefix_dir)
    __mp__.run_with_output("sed", "-i", '', 's/#if PNG_ZLIB_VERNUM != 0 && PNG_ZLIB_VERNUM != ZLIB_VERNUM/#if 0/g', os.path.join(src_dir, "pngpriv.h"))
    __mp__.run_with_output("make")
    __mp__.run_with_output("make", "install")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_png", "1.6.50"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-png", "1.6.50")
        __mp__.add_wheel_dep_libs(w, "png", os.path.join(prefix_dir, "lib", "*"))
        __mp__.add_wheel_dep_include(w, "png", os.path.join(prefix_dir, "include", "*.h"),
                                     base_dir=os.path.join(prefix_dir, "include"))

    return result_wheel
