import __mp__
from typing import *

import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()
    os.chdir(src_dir)

    __mp__.run_with_output("patch", "--binary", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "glpk.patch"))

    install_dir = os.path.join(src_dir, "install")
    os.mkdir(install_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake", "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir, "-DBUILD_SHARED_LIBS=OFF", src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja")
    __mp__.run_build_tool_exe("ninja", "ninja", "install")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_glpk", "5.0"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-glpk", "5.0")
        __mp__.add_wheel_dep_libs(w, "glpk", os.path.join(install_dir, "lib", "*.a"))
        __mp__.add_wheel_dep_include(w, "glpk", os.path.join(install_dir, "include", "glpk.h"))

    return result_wheel
