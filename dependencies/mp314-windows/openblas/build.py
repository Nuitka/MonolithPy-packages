import __mp__
from typing import *

import os
import shutil
import glob
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    __mp__.setup_compiler_env()

    __mp__.auto_patch_build_file(os.path.join(src_dir, "CMakeLists.txt"))

    os.chdir(src_dir)
    __mp__.run_build_tool_exe("patch", "patch.exe", "-p1", "-ui",
                              os.path.join(os.path.dirname(__file__), "openblas-intel.patch"))

    install_dir = os.path.join(src_dir, "install")
    os.mkdir(install_dir)
    build_dir = os.path.join(src_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep +
                          os.path.dirname(__mp__.find_build_tool_exe("flang", "flang-new.exe")) + os.pathsep + os.environ["PATH"])
    __mp__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir, "-DBUILD_STATIC_LIBS=ON", "-DBUILD_SHARED_LIBS=OFF",
                              "-DBUILD_TESTING=OFF", "-DCMAKE_Fortran_COMPILER=flang-new.exe",
                              "-DCMAKE_CXX_COMPILER=clang-cl.exe", "-DCMAKE_C_COMPILER=clang-cl.exe",
                              "-DCMAKE_C_FLAGS=-w", "-DCMAKE_CXX_FLAGS=-w",
                              "-DCMAKE_ASM_COMPILE_OPTIONS_MSVC_RUNTIME_LIBRARY_MultiThreaded=", src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja.exe", "install")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_openblas", "0.3.28"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-openblas", "0.3.28")
        __mp__.add_wheel_dep_libs(w, "openblas", os.path.join(install_dir, "lib", "*"),
                                  base_dir=os.path.join(install_dir, "lib"))
        __mp__.add_wheel_dep_include(w, "openblas", os.path.join(install_dir, "include", "*"),
                                     base_dir=os.path.join(install_dir, "include"))

    return result_wheel
