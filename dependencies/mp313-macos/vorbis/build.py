import __mp__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __mp__.download_extract("https://github.com/xiph/vorbis/releases/download/v1.3.7/libvorbis-1.3.7.zip", temp_dir)

    src_dir = glob.glob(os.path.join(temp_dir, "libvorbis*"))[0]

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DOGG_ROOT=" + __mp__.find_dep_root("ogg"),
                              "-DOGG_INCLUDE_DIRS=" + __mp__.find_dep_include("ogg"),
                              "-DOGG_LIBRARY=" + os.path.join(__mp__.find_dep_libs("ogg"), "libogg.a"),
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja")

    __mp__.install_dep_libs("vorbis", os.path.join(build_dir, "lib", "*.a"))
    __mp__.install_dep_include("vorbis", os.path.join(src_dir, "include", "vorbis"))
