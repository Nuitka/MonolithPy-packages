import __np__
from typing import *

import os
import shutil
import glob
import sysconfig


def run(temp_dir: str):
    __np__.download_extract("https://master.dl.sourceforge.net/project/freetype/freetype2/2.7.1/freetype-2.7.1.tar.gz", temp_dir)

    src_dir = glob.glob(os.path.join(temp_dir, "freetype*"))[0]

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    install_dir = os.path.join(temp_dir, "install")
    os.mkdir(install_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    os.environ["PATH"] = os.path.dirname(__np__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"]
    os.environ["CFLAGS"] = sysconfig.get_config_var("CFLAGS")
    __np__.run_build_tool_exe("cmake", "cmake", "-G", "Ninja",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir,
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DZLIB_ROOT=" + __np__.find_dep_root("zlib"),
                              "-DWITH_HarfBuzz=ON", "-DWITH_BZip2=OFF",
                              "-DWITH_PNG=OFF",
                              "-DHARFBUZZ_INCLUDE_DIRS=" + __np__.find_dep_include("harfbuzz"),
                              "-DPC_HARFBUZZ_INCLUDEDIR=" + __np__.find_dep_include("harfbuzz"),
                              "-DPC_HARFBUZZ_LIBDIR=" + __np__.find_dep_libs("harfbuzz"),
                              src_dir)
    __np__.run_build_tool_exe("ninja", "ninja")
    __np__.run_build_tool_exe("ninja", "ninja", "install")

    __np__.install_dep_libs("freetype", os.path.join(install_dir, "lib", "libfreetype.a"))
    __np__.install_dep_include("freetype", os.path.join(install_dir, "include", "freetype2", "*"))
