import __mp__
from typing import *

import os
import shutil
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    __mp__.setup_compiler_env()

    __mp__.auto_patch_build(os.path.join(src_dir, "win32"))

    os.chdir(src_dir)

    __mp__.nmake("/f", "win32/Makefile.msc")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_zlib", "1.2.12"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-zlib", "1.2.12")
        __mp__.add_wheel_dep_libs(w, "zlib", os.path.join(src_dir, "zlib.lib"))
        __mp__.add_wheel_dep_include(w, "zlib", os.path.join(src_dir, "*.h"))

    return result_wheel
