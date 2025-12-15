import __mp__
from typing import *

import os
import shutil
import glob
import platform


def run(temp_dir: str):
    __mp__.download_extract("https://github.com/OpenMathLib/OpenBLAS/archive/68ff451eccea3e7d7d2afb2588b63552bde7ea89.tar.gz", temp_dir)

    src_dir = glob.glob(os.path.join(temp_dir, "OpenBLAS*"))[0]

    install_dir = os.path.join(temp_dir, "install")
    os.mkdir(install_dir)
    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    __mp__.auto_patch_build_file(os.path.join(src_dir, "CMakeLists.txt"))

    if platform.machine() == "x86_64":
        __mp__.run("patch", "-p1", "-i",
                                os.path.join(os.path.dirname(__file__), "openblas-intel.patch"), cwd=src_dir)

    env = os.environ.copy()
    env["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    env["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("cmake", "cmake")) + os.pathsep + os.environ["PATH"])
    env["FFLAGS"] = "-static-libgcc"
    if platform.machine() == "arm64":
        platform_args = ["-DCMAKE_OSX_ARCHITECTURES=arm64", "-DCMAKE_OSX_DEPLOYMENT_TARGET=11", "-DCMAKE_BUILD_TYPE=Debug"]
    else:
        platform_args = ["-DCMAKE_OSX_ARCHITECTURES=x86_64", "-DCMAKE_OSX_DEPLOYMENT_TARGET=10.9", "-DCMAKE_BUILD_TYPE=Debug"]  # Must build in Debug to workaround bug.
    __mp__.run_build_tool_exe("cmake", "cmake",
                              "-DCMAKE_Fortran_COMPILER=" + __mp__.find_build_tool_exe("gcc", "gfortran-nuitka"),
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir, "-DBUILD_STATIC_LIBS=ON", "-DBUILD_SHARED_LIBS=OFF",
                              "-DBUILD_TESTING=OFF", *platform_args, src_dir, env=env)
    __mp__.run_with_output("make", "-j4", "install", env=env)

    __mp__.install_dep_libs("openblas", os.path.join(install_dir, "lib", "*"),
                            base_dir=os.path.join(install_dir, "lib"))
    __mp__.install_dep_include("openblas", os.path.join(install_dir, "include", "*"),
                               base_dir=os.path.join(install_dir, "include"))
