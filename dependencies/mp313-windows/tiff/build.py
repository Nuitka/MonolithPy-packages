import __np__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __np__.download_extract("http://download.osgeo.org/libtiff/tiff-4.3.0.zip", temp_dir)

    __np__.setup_compiler_env()

    src_dir = glob.glob(os.path.join(temp_dir, "tiff*"))[0]

    __np__.auto_patch_build(src_dir)

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["PATH"] = os.path.dirname(__np__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"]
    __np__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF",
                              "-DZLIB_ROOT=" + __np__.find_dep_root("zlib"),
                              "-DJPEG_ROOT=" + __np__.find_dep_root("jpeg"),
                              src_dir)
    __np__.run_build_tool_exe("ninja", "ninja.exe")

    __np__.install_dep_libs("tiff", os.path.join(build_dir, "libtiff", "*.lib"))
    __np__.install_dep_include("tiff", os.path.join(src_dir, "libtiff", "*.h"))
    __np__.install_dep_include("tiff", os.path.join(build_dir, "libtiff", "*.h"))
