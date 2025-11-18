import __np__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __np__.download_extract("https://github.com/kcat/openal-soft/archive/refs/tags/1.21.1.tar.gz", temp_dir)

    __np__.setup_compiler_env()

    src_dir = glob.glob(os.path.join(temp_dir, "openal*"))[0]

    __np__.auto_patch_build(src_dir)

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["PATH"] = os.path.dirname(__np__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"]
    __np__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DFORCE_STATIC_VCRT=ON", "-DLIBTYPE=STATIC", src_dir)
    __np__.run_build_tool_exe("ninja", "ninja.exe")

    __np__.install_dep_libs("openal", os.path.join(build_dir, "OpenAL32.lib"))
    __np__.install_dep_include("openal", os.path.join(src_dir, "include", "*"))
