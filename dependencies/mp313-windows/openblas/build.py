import __np__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __np__.download_extract("https://github.com/OpenMathLib/OpenBLAS/releases/download/v0.3.28/OpenBLAS-0.3.28.zip", temp_dir)

    __np__.setup_compiler_env()

    src_dir = glob.glob(os.path.join(temp_dir, "OpenBLAS*"))[0]

    __np__.auto_patch_build_file(os.path.join(src_dir, "CMakeLists.txt"))

    os.chdir(src_dir)
    __np__.run_build_tool_exe("patch", "patch.exe", "-p1", "-ui",
                              os.path.join(os.path.dirname(__file__), "openblas-intel.patch"))

    install_dir = os.path.join(temp_dir, "install")
    os.mkdir(install_dir)
    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["PATH"] = (os.path.dirname(__np__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep +
                          os.path.dirname(__np__.find_build_tool_exe("flang", "flang-new.exe")) + os.pathsep + os.environ["PATH"])
    __np__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir, "-DBUILD_STATIC_LIBS=ON", "-DBUILD_SHARED_LIBS=OFF",
                              "-DBUILD_TESTING=OFF", "-DCMAKE_Fortran_COMPILER=flang-new.exe",
                              "-DCMAKE_CXX_COMPILER=clang-cl.exe", "-DCMAKE_C_COMPILER=clang-cl.exe",
                              "-DCMAKE_C_FLAGS=-w", "-DCMAKE_CXX_FLAGS=-w",
                              "-DCMAKE_ASM_COMPILE_OPTIONS_MSVC_RUNTIME_LIBRARY_MultiThreaded=", src_dir)
    __np__.run_build_tool_exe("ninja", "ninja.exe", "install")

    __np__.install_dep_libs("openblas", os.path.join(install_dir, "lib", "*"),
                            base_dir=os.path.join(install_dir, "lib"))
    __np__.install_dep_include("openblas", os.path.join(install_dir, "include", "*"),
                               base_dir=os.path.join(install_dir, "include"))
