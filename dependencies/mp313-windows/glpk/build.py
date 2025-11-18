import __np__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __np__.download_extract("https://github.com/Mizux/GLPK/archive/refs/tags/5.0.zip", temp_dir)

    __np__.setup_compiler_env()

    src_dir = glob.glob(os.path.join(temp_dir, "GLPK*"))[0]
    os.chdir(src_dir)

    __np__.run_build_tool_exe("patch", "patch.exe", "--binary", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "glpk.patch"))

    __np__.auto_patch_build_file(os.path.join(src_dir, "CMakeLists.txt"))

    install_dir = os.path.join(temp_dir, "install")
    os.mkdir(install_dir)

    os.environ["PATH"] = (os.path.dirname(__np__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"])
    __np__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir, "-DBUILD_SHARED_LIBS=OFF", src_dir)
    __np__.run_build_tool_exe("ninja", "ninja.exe")

    __np__.install_dep_libs("glpk", os.path.join(src_dir, "bin", "*.lib"))
    __np__.install_dep_include("glpk", os.path.join(src_dir, "src", "glpk.h"))
