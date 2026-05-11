import __mp__
from typing import *

import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"]

    build_dir = os.path.join(src_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    install_dir = os.path.join(src_dir, "install")
    os.mkdir(install_dir)

    __mp__.run_build_tool_exe("cmake", "cmake", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SHARED=FALSE",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir, src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja", "install")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_jpeg", "3.1.0"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-jpeg", "3.1.0")
        __mp__.add_wheel_dep_libs(w, "jpeg", os.path.join(install_dir, "lib", "*.a"))
        __mp__.add_wheel_dep_libs(w, "jpeg", os.path.join(install_dir, "lib", "cmake"),
                                  base_dir=os.path.join(install_dir, "lib"))
        __mp__.add_wheel_dep_include(w, "jpeg", os.path.join(install_dir, "include", "*"))

    return result_wheel
