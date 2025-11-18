import __np__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __np__.download_extract("https://github.com/xiph/vorbis/releases/download/v1.3.7/libvorbis-1.3.7.zip", temp_dir)

    __np__.setup_compiler_env()

    src_dir = glob.glob(os.path.join(temp_dir, "libvorbis*"))[0]

    __np__.auto_patch_build(src_dir)

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["PATH"] = os.path.dirname(__np__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"]
    __np__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DOGG_ROOT=" + __np__.find_dep_root("ogg"),
                              "-DOGG_INCLUDE_DIRS=" + __np__.find_dep_include("ogg"),
                              "-DOGG_LIBRARY=" + os.path.join(__np__.find_dep_libs("ogg"), "ogg.lib"),
                              src_dir)
    __np__.run_build_tool_exe("ninja", "ninja.exe")

    __np__.install_dep_libs("vorbis", os.path.join(build_dir, "lib", "*.lib"))
    __np__.install_dep_include("vorbis", os.path.join(src_dir, "include", "vorbis"))
