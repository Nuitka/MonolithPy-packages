import __mp__
from typing import *

import os
import shutil
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
                              "-DBUILD_SHARED_LIBS=OFF",
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja.exe", "zlibstatic")

    # Normalize output name: zlib's CMake build produces zlibstatic.lib;
    # downstream packages expect zlib.lib.
    shutil.copy(os.path.join(build_dir, "zlibstatic.lib"), os.path.join(build_dir, "zlib.lib"))

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_zlib", "1.2.12"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-zlib", "1.2.12")
        __mp__.add_wheel_dep_libs(w, "zlib", os.path.join(build_dir, "zlib.lib"))
        __mp__.add_wheel_dep_include(w, "zlib", os.path.join(src_dir, "*.h"))
        __mp__.add_wheel_dep_include(w, "zlib", os.path.join(build_dir, "*.h"))

    return result_wheel
