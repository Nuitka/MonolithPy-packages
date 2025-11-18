import __np__
from typing import *

import os
import shutil
import glob
import re


def run(temp_dir: str):
    __np__.download_extract("https://github.com/microsoft/mimalloc/archive/refs/tags/v2.0.7.zip", temp_dir)

    src_dir = glob.glob(os.path.join(temp_dir, "mimalloc*"))[0]

    __np__.setup_compiler_env()

    __np__.auto_patch_build(src_dir)

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["PATH"] = os.path.dirname(__np__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"]
    __np__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DMI_BUILD_SHARED=OFF",
                              "-DMI_BUILD_OBJECT=OFF",
                              "-DMI_BUILD_TESTS=OFF",
                              "-DMI_BUILD_STATIC=ON",
                              "-DMI_INSTALL_TOPLEVEL=ON",
                              "-DMI_OVERRIDE=OFF",
                              src_dir)
    __np__.run_build_tool_exe("ninja", "ninja.exe")

    __np__.install_dep_libs("mimalloc", os.path.join(build_dir, "*.lib"))
    __np__.install_dep_include("mimalloc", os.path.join(src_dir, "mimalloc.h"))
