import __mp__
from typing import *

import os
import shutil
import glob
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()
    install_dir = os.path.join(os.getcwd(), "install_prefix")

    __mp__.run_build_tool_exe("patch", "patch.exe", "--binary", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "glpk.patch"))

    __mp__.auto_patch_build_file(os.path.join(src_dir, "CMakeLists.txt"))

    os.mkdir(install_dir)

    os.environ["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"])
    __mp__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir, "-DBUILD_SHARED_LIBS=OFF", src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja.exe")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_glpk", "5.0"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-glpk", "5.0")
        __mp__.add_wheel_dep_libs(w, "glpk", os.path.join(src_dir, "bin", "*.lib"))
        __mp__.add_wheel_dep_include(w, "glpk", os.path.join(src_dir, "src", "glpk.h"))

    return result_wheel
