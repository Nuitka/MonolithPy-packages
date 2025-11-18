import __np__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __np__.download_extract("http://download-mirror.savannah.gnu.org/releases/freetype/freetype-2.13.3.tar.gz", temp_dir)

    __np__.setup_compiler_env()

    src_dir = glob.glob(os.path.join(temp_dir, "freetype*"))[0]

    __np__.auto_patch_build(src_dir)
    __np__.patch_all_source(src_dir)

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    install_dir = os.path.join(temp_dir, "install")
    os.mkdir(install_dir)

    os.environ["PATH"] = os.path.dirname(__np__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"]
    __np__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir,
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DZLIB_ROOT=" + __np__.find_dep_root("zlib"),
                              "-DWITH_HarfBuzz=ON", "-DWITH_BZip2=OFF",
                              "-DWITH_PNG=OFF",
                              "-DHARFBUZZ_INCLUDE_DIRS=" + __np__.find_dep_include("harfbuzz"),
                              "-DPC_HARFBUZZ_INCLUDEDIR=" + __np__.find_dep_include("harfbuzz"),
                              "-DPC_HARFBUZZ_LIBDIR=" + __np__.find_dep_libs("harfbuzz"),
                              src_dir)
    __np__.run_build_tool_exe("ninja", "ninja.exe")
    __np__.run_build_tool_exe("ninja", "ninja.exe", "install")

    __np__.install_dep_libs("freetype", os.path.join(install_dir, "lib", "freetype.lib"))
    __np__.install_dep_libs("freetype", os.path.join(install_dir, "lib", "cmake"))
    __np__.install_dep_include("freetype", os.path.join(install_dir, "include", "freetype2", "*"))
