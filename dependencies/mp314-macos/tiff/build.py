import __mp__
from typing import *

import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    build_dir = os.path.join(src_dir, "builddir")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.13"
    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF",
                              "-Djbig=OFF", "-Dzstd=OFF",
                              "-DZLIB_ROOT=" + __mp__.find_dep_root("base"),
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_tiff", "4.3.0"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-tiff", "4.3.0")
        __mp__.add_wheel_dep_libs(w, "tiff", os.path.join(build_dir, "libtiff", "*.a"))
        __mp__.add_wheel_dep_include(w, "tiff", os.path.join(src_dir, "libtiff", "*.h"))
        __mp__.add_wheel_dep_include(w, "tiff", os.path.join(build_dir, "libtiff", "*.h"))

    return result_wheel
