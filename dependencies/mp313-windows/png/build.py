import __np__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __np__.download_extract("http://prdownloads.sourceforge.net/libpng/lpng1637.zip?download", temp_dir)

    __np__.setup_compiler_env()

    src_dir = glob.glob(os.path.join(temp_dir, "lpng*"))[0]

    __np__.auto_patch_build(src_dir)

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["PATH"] = os.path.dirname(__np__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"]
    __np__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DPNG_SHARED=OFF", "-DPNG_TESTS=OFF",
                              "-DZLIB_LIBRARY=" + os.path.join(__np__.find_dep_libs("zlib"), "zlib.lib"),
                              "-DZLIB_INCLUDE_DIR=" + __np__.find_dep_include("zlib"),
                              src_dir)
    __np__.run_build_tool_exe("ninja", "ninja.exe")

    shutil.copy(os.path.join(build_dir, "libpng16_static.lib"), os.path.join(build_dir, "libpng16.lib"))
    __np__.install_dep_libs("png", os.path.join(build_dir, "*.lib"))
    __np__.install_dep_include("png", os.path.join(src_dir, "*.h"), base_dir=os.path.join(src_dir, "include"))
    __np__.install_dep_include("png", os.path.join(build_dir, "*.h"))
