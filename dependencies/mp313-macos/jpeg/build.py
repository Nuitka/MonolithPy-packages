import __mp__
from typing import *

import os
import shutil
import glob

import sysconfig


def run(temp_dir: str):
    __mp__.download_extract("https://ijg.org/files/jpegsr9d.zip", temp_dir)

    src_dir = glob.glob(os.path.join(temp_dir, "jpeg*"))[0]
    os.chdir(src_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"]
    os.environ["CFLAGS"] = sysconfig.get_config_var("CFLAGS")
    shutil.copy(os.path.join(temp_dir, "libjpeg.cmake"), os.path.join(src_dir, "CMakeLists.txt"))
    shutil.copy(os.path.join(temp_dir, "libjpeg-jconfig.h.cmake"), os.path.join(src_dir, "jconfig.h.cmake"))

    __mp__.auto_patch_build(src_dir)
    __mp__.patch_all_source(src_dir)

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    __mp__.run_build_tool_exe("cmake", "cmake", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release", src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja")

    __mp__.install_dep_libs("jpeg", os.path.join(build_dir, "*.a"))
    __mp__.install_dep_include("jpeg", os.path.join(src_dir, "*.h"))
    __mp__.install_dep_include("jpeg", os.path.join(build_dir, "*.h"))
