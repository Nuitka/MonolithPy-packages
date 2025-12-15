import __mp__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __mp__.download_extract("http://download.osgeo.org/libtiff/tiff-4.3.0.zip", temp_dir)

    __mp__.setup_compiler_env()

    src_dir = glob.glob(os.path.join(temp_dir, "tiff*"))[0]

    __mp__.auto_patch_build(src_dir)

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF",
                              "-DZLIB_ROOT=" + __mp__.find_dep_root("zlib"),
                              "-DJPEG_ROOT=" + __mp__.find_dep_root("jpeg"),
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja.exe")

    __mp__.install_dep_libs("tiff", os.path.join(build_dir, "libtiff", "*.lib"))
    __mp__.install_dep_include("tiff", os.path.join(src_dir, "libtiff", "*.h"))
    __mp__.install_dep_include("tiff", os.path.join(build_dir, "libtiff", "*.h"))
