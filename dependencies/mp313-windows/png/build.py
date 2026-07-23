import __mp__
from typing import *

import os
import shutil
import glob
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    __mp__.setup_compiler_env()

    __mp__.auto_patch_build(src_dir)

    build_dir = os.path.join(src_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DPNG_SHARED=OFF", "-DPNG_TESTS=OFF",
                              "-DZLIB_LIBRARY=" + os.path.join(__mp__.find_dep_libs("zlib"), "zlib.lib"),
                              "-DZLIB_INCLUDE_DIR=" + __mp__.find_dep_include("zlib"),
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja.exe")

    shutil.copy(os.path.join(build_dir, "libpng16_static.lib"), os.path.join(build_dir, "libpng16.lib"))

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_png", "1.6.50"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-png", "1.6.50")
        __mp__.add_wheel_dep_libs(w, "png", os.path.join(build_dir, "*.lib"))
        __mp__.add_wheel_dep_include(w, "png", os.path.join(src_dir, "*.h"),
                                     base_dir=os.path.join(src_dir, "include"))
        __mp__.add_wheel_dep_include(w, "png", os.path.join(build_dir, "*.h"))

    return result_wheel
