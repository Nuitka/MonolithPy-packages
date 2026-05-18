import __mp__
from typing import *

import os
import shutil
import glob
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    __mp__.setup_compiler_env()

    build_dir = os.path.join(src_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    install_dir = os.path.join(src_dir, "install")
    os.mkdir(install_dir)

    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_CPU_DEMOS=OFF",
                              "-DBUILD_OPENGL3_DEMOS=OFF", "-DBUILD_UNIT_TESTS=OFF",
                              "-DINSTALL_LIBS=ON",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir,
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja.exe")
    __mp__.run_build_tool_exe("ninja", "ninja.exe", "install")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_bullet", "2.83.7"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-bullet", "2.83.7")
        __mp__.add_wheel_dep_libs(w, "bullet", os.path.join(install_dir, "lib", "*.lib"))
        __mp__.add_wheel_dep_include(w, "bullet", os.path.join(install_dir, "include", "bullet", "*"),
                                     base_dir=os.path.join(install_dir, "include", "bullet"))

    return result_wheel
