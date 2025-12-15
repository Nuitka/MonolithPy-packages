import __mp__
from typing import *

import os
import shutil
import glob
import sysconfig


def run(temp_dir: str):
    __mp__.download_extract("https://github.com/bulletphysics/bullet3/archive/2fb92bc40c16e4da5a9018479d4a8e1899702ab8.zip", temp_dir)

    src_dir = glob.glob(os.path.join(temp_dir, "bullet*"))[0]
    os.chdir(src_dir)

    __mp__.run_with_output("patch", "--binary", "-p1", "-i",
                           os.path.join(os.path.dirname(__file__), "7638b7c5a659dceb4e580ae87d4d60b00847ef94.diff"))

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    install_dir = os.path.join(temp_dir, "install")
    os.mkdir(install_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    os.environ["CFLAGS"] = sysconfig.get_config_var("CFLAGS")
    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_CPU_DEMOS=OFF",
                              "-DBUILD_OPENGL3_DEMOS=OFF", "-DBUILD_UNIT_TESTS=OFF",
                              "-DINSTALL_LIBS=ON",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir,
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja")
    __mp__.run_build_tool_exe("ninja", "ninja", "install")

    __mp__.install_dep_libs("bullet", os.path.join(install_dir, "lib", "*.a"))
    __mp__.install_dep_include("bullet", os.path.join(install_dir, "include", "bullet", "*"))
