import __mp__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __mp__.download_extract("https://github.com/Mizux/GLPK/archive/refs/tags/5.0.zip", temp_dir)

    src_dir = glob.glob(os.path.join(temp_dir, "GLPK*"))[0]
    os.chdir(src_dir)

    __mp__.run_with_output("patch", "--binary", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "glpk.patch"))

    install_dir = os.path.join(temp_dir, "install")
    os.mkdir(install_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake", "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir, "-DBUILD_SHARED_LIBS=OFF", src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja")
    __mp__.run_build_tool_exe("ninja", "ninja", "install")

    __mp__.install_dep_libs("glpk", os.path.join(install_dir, "lib", "*.a"))
    __mp__.install_dep_include("glpk", os.path.join(install_dir, "include", "glpk.h"))
