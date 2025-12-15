import __mp__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __mp__.download_extract("https://github.com/kcat/openal-soft/archive/refs/tags/1.21.1.tar.gz", temp_dir)

    __mp__.setup_compiler_env()

    src_dir = glob.glob(os.path.join(temp_dir, "openal*"))[0]

    __mp__.auto_patch_build(src_dir)

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DFORCE_STATIC_VCRT=ON", "-DLIBTYPE=STATIC", src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja.exe")

    __mp__.install_dep_libs("openal", os.path.join(build_dir, "OpenAL32.lib"))
    __mp__.install_dep_include("openal", os.path.join(src_dir, "include", "*"))
