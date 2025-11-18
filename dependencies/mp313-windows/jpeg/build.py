import __np__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __np__.download_extract("https://github.com/libjpeg-turbo/libjpeg-turbo/releases/download/3.1.0/libjpeg-turbo-3.1.0.tar.gz", temp_dir)

    __np__.setup_compiler_env()

    src_dir = glob.glob(os.path.join(temp_dir, "libjpeg*"))[0]
    os.chdir(src_dir)

    os.environ["PATH"] = os.path.dirname(__np__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"]

    __np__.auto_patch_build(src_dir)
    __np__.patch_all_source(src_dir)

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    install_dir = os.path.join(temp_dir, "install")
    os.mkdir(install_dir)

    __np__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SHARED=FALSE",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir, src_dir)
    __np__.run_build_tool_exe("ninja", "ninja.exe", "install")

    shutil.copy(os.path.join(install_dir, "lib", "jpeg-static.lib"), os.path.join(install_dir, "lib", "jpeg.lib"))
    shutil.copy(os.path.join(install_dir, "lib", "turbojpeg-static.lib"), os.path.join(install_dir, "lib", "turbojpeg.lib"))
    __np__.install_dep_libs("jpeg", os.path.join(install_dir, "lib", "*.lib"))
    __np__.install_dep_libs("jpeg", os.path.join(install_dir, "lib", "cmake"))
    __np__.install_dep_include("jpeg", os.path.join(install_dir, "include", "*"))
