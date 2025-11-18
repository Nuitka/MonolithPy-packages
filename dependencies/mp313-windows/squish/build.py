import __np__
from typing import *

import os
import shutil
import glob
import re


def run(temp_dir: str):
    src_dir = os.path.join(temp_dir, "libsquish")

    __np__.download_extract("http://prdownloads.sourceforge.net/libsquish/libsquish-1.15.tgz?download", src_dir)

    __np__.setup_compiler_env()

    __np__.auto_patch_build(src_dir)

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["PATH"] = os.path.dirname(__np__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"]
    __np__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release",
                              src_dir)
    __np__.run_build_tool_exe("ninja", "ninja.exe")

    __np__.install_dep_libs("squish", os.path.join(build_dir, "*.lib"))
    __np__.install_dep_include("squish", os.path.join(src_dir, "squish.h"))
