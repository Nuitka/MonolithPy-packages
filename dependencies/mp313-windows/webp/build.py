import __np__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __np__.download_extract("https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.5.0.tar.gz", temp_dir)

    __np__.setup_compiler_env()

    src_dir = glob.glob(os.path.join(temp_dir, "libwebp*"))[0]

    __np__.auto_patch_build(src_dir)

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    install_dir = os.path.join(temp_dir, "install")
    os.mkdir(install_dir)

    os.environ["PATH"] = os.path.dirname(__np__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"]
    __np__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja", "-DBUILD_SHARED_LIBS=OFF",
                              "-DCMAKE_BUILD_TYPE=Release", "-DWEBP_BUILD_CWEBP=OFF", "-DWEBP_BUILD_DWEBP=OFF",
                              "-DWEBP_BUILD_GIF2WEBP=OFF", "-DWEBP_BUILD_IMG2WEBP=OFF", "-DWEBP_BUILD_VWEBP=OFF",
                              "-DWEBP_BUILD_WEBPINFO=OFF", "-DWEBP_BUILD_WEBPMUX=OFF",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir, src_dir)
    __np__.run_build_tool_exe("ninja", "ninja.exe", "install")

    __np__.install_dep_libs("webp", os.path.join(install_dir, "lib", "*"))
    __np__.install_dep_include("webp", os.path.join(install_dir, "include", "**", "*.h"),
                               base_dir=os.path.join(install_dir, "include"))
