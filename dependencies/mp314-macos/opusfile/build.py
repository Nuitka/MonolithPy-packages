import __mp__
from typing import *

import os
import shutil
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    shutil.copy(os.path.join(os.path.dirname(__file__), "libopusfile.cmake"), os.path.join(src_dir, "CMakeLists.txt"))

    build_dir = os.path.join(src_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.13"
    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DOGG_INCLUDE_DIRS=" + __mp__.find_dep_include("ogg"),
                              "-DOGG_LIBRARIES=" + os.path.join(__mp__.find_dep_libs("ogg"), "libogg.a"),
                              "-DOPUS_INCLUDE_DIRS=" + __mp__.find_dep_include("opus"),
                              "-DOPUS_LIBRARIES=" + os.path.join(__mp__.find_dep_libs("opus"), "libopus.a"),
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_opusfile", "0.12"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-opusfile", "0.12")
        __mp__.add_wheel_dep_libs(w, "opusfile", os.path.join(build_dir, "libopusfile.a"))
        __mp__.add_wheel_dep_include(w, "opusfile", os.path.join(src_dir, "include", "*.h"))

    return result_wheel
