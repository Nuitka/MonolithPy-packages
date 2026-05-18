import __mp__
from typing import *

import os
import platform
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    install_dir = os.path.join(src_dir, "install")
    os.mkdir(install_dir)
    build_dir = os.path.join(src_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    __mp__.auto_patch_build_file(os.path.join(src_dir, "CMakeLists.txt"))

    if platform.machine() == "x86_64":
        __mp__.run("patch", "-p1", "-i",
                   os.path.join(os.path.dirname(__file__), "openblas-intel.patch"), cwd=src_dir)

    env = os.environ.copy()
    env["MACOSX_DEPLOYMENT_TARGET"] = "10.13"
    env["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("cmake", "cmake")) + os.pathsep + os.environ["PATH"])
    env["FFLAGS"] = "-static-libgcc"
    if platform.machine() == "arm64":
        platform_args = ["-DCMAKE_OSX_ARCHITECTURES=arm64", "-DCMAKE_OSX_DEPLOYMENT_TARGET=11", "-DCMAKE_BUILD_TYPE=Debug"]
    else:
        platform_args = ["-DCMAKE_OSX_ARCHITECTURES=x86_64", "-DCMAKE_OSX_DEPLOYMENT_TARGET=10.13", "-DCMAKE_BUILD_TYPE=Debug"]  # Must build in Debug to workaround bug.
    __mp__.run_build_tool_exe("cmake", "cmake",
                              "-DCMAKE_Fortran_COMPILER=" + __mp__.find_build_tool_exe("gcc", "gfortran-nuitka"),
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir, "-DBUILD_STATIC_LIBS=ON", "-DBUILD_SHARED_LIBS=OFF",
                              "-DBUILD_TESTING=OFF", *platform_args, src_dir, env=env)
    __mp__.run_with_output("make", "-j4", "install", env=env)

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_openblas", "0.3.28"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-openblas", "0.3.28")
        __mp__.add_wheel_dep_libs(w, "openblas", os.path.join(install_dir, "lib", "*"),
                                  base_dir=os.path.join(install_dir, "lib"))
        __mp__.add_wheel_dep_include(w, "openblas", os.path.join(install_dir, "include", "*"),
                                     base_dir=os.path.join(install_dir, "include"))

    return result_wheel
