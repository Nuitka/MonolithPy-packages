import __mp__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __mp__.download_extract("https://github.com/xiph/opusfile/releases/download/v0.12/opusfile-0.12.zip", temp_dir)

    src_dir = glob.glob(os.path.join(temp_dir, "opusfile*"))[0]

    shutil.copy(os.path.join(temp_dir, "libopusfile.cmake"), os.path.join(src_dir, "CMakeLists.txt"))

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DOGG_INCLUDE_DIRS=" + __mp__.find_dep_include("ogg"),
                              "-DOGG_LIBRARIES=" + os.path.join(__mp__.find_dep_libs("ogg"), "libogg.a"),
                              "-DOPUS_INCLUDE_DIRS=" + __mp__.find_dep_include("opus"),
                              "-DOPUS_LIBRARIES=" + os.path.join(__mp__.find_dep_libs("opus"), "libopus.a"),
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja")

    __mp__.install_dep_libs("opusfile", os.path.join(build_dir, "libopusfile.a"))
    __mp__.install_dep_include("opusfile", os.path.join(src_dir, "include", "*.h"))
