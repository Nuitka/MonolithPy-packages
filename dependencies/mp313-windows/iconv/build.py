import __np__
from typing import *

import os
import shutil


def run(temp_dir: str):
    __np__.download_extract("https://github.com/kiyolee/libiconv-win-build/archive/refs/tags/v1.16-p1.zip", temp_dir)

    # Choose the correct project based on VS version
    if __np__.get_vs_version() >= 16:
        build_dir = os.path.join(temp_dir, "libiconv-win-build-1.16-p1", "build-VS2019-MT")
    else:
        build_dir = os.path.join(temp_dir, "libiconv-win-build-1.16-p1", "build-VS2017-MT")

    is_amd64 = 'amd64' in __np__.get_platform()

    __np__.msbuild(os.path.join(build_dir, "libiconv.sln"),
                    "/property:Configuration=Release",
                    "/property:Platform=" + ("x64" if is_amd64 else "Win32"))

    # Rename the output file to the standard name.
    if is_amd64:
        shutil.copy(os.path.join(build_dir, "x64", "Release", "libiconv-static.lib"), os.path.join(temp_dir, "iconv.lib"))
    else:
        shutil.copy(os.path.join(build_dir, "Release", "libiconv-static.lib"), os.path.join(temp_dir, "iconv.lib"))

    shutil.copy(os.path.join(temp_dir, "iconv.lib"), os.path.join(temp_dir, "iconv_a.lib"))
    __np__.install_dep_libs("iconv", os.path.join(temp_dir, "iconv.lib"))
    __np__.install_dep_libs("iconv", os.path.join(temp_dir, "iconv_a.lib"))
    __np__.install_dep_include("iconv", os.path.join(temp_dir, "libiconv-win-build-1.16-p1", "include", "*"))
