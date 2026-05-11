import __mp__
from typing import *

import os
import shutil
import glob
import re
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
                              "-DMI_BUILD_SHARED=OFF",
                              "-DMI_BUILD_OBJECT=OFF",
                              "-DMI_BUILD_TESTS=OFF",
                              "-DMI_BUILD_STATIC=ON",
                              "-DMI_INSTALL_TOPLEVEL=ON",
                              "-DMI_OVERRIDE=OFF",
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja.exe")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_mimalloc", "2.0.7"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-mimalloc", "2.0.7")
        __mp__.add_wheel_dep_libs(w, "mimalloc", os.path.join(build_dir, "*.lib"))
        __mp__.add_wheel_dep_include(w, "mimalloc", os.path.join(src_dir, "mimalloc.h"))

    return result_wheel
