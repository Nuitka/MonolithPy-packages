import __mp__
from typing import *

import os
import shutil


def run(temp_dir: str):
    __mp__.download_extract("https://github.com/kiyolee/libiconv-win-build/archive/refs/tags/v1.18-p1.zip", temp_dir)

    # Choose the correct project based on VS version
    if __mp__.get_vs_version() > 17:
        build_dir = os.path.join(temp_dir, "libiconv-win-build-1.18-p1", "build-VS2026-MT")
    else:
        build_dir = os.path.join(temp_dir, "libiconv-win-build-1.18-p1", "build-VS2022-MT")

    __mp__.msbuild(os.path.join(build_dir, "libiconv.sln"),
                    "/property:Configuration=Release",
                    "/property:Platform=x64")

    # Rename the output file to the standard name.
    shutil.copy(os.path.join(build_dir, "x64", "Release", "libiconv-static.lib"), os.path.join(temp_dir, "iconv.lib"))

    shutil.copy(os.path.join(temp_dir, "iconv.lib"), os.path.join(temp_dir, "iconv_a.lib"))
    __mp__.install_dep_libs("iconv", os.path.join(temp_dir, "iconv.lib"))
    __mp__.install_dep_libs("iconv", os.path.join(temp_dir, "iconv_a.lib"))
    __mp__.install_dep_include("iconv", os.path.join(temp_dir, "libiconv-win-build-1.18-p1", "include", "*"))
