import __mp__
from typing import *

import os
import shutil
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    # Choose the correct project based on VS version
    if __mp__.get_vs_version() > 17:
        build_dir = os.path.join(src_dir, "build-VS2026-MT")
    else:
        build_dir = os.path.join(src_dir, "build-VS2022-MT")

    # /GL produces LTCG IR tied to the exact cl micro-version, which
    # breaks linking when extension wheels are compiled with a different
    # MSVC patch level than this bin-dep. Disable WPO so iconv.lib stays
    # portable plain COFF.
    __mp__.msbuild(os.path.join(build_dir, "libiconv.sln"),
                    "/property:Configuration=Release",
                    "/property:Platform=x64",
                    "/property:WholeProgramOptimization=false")

    # Rename the output file to the standard name.
    shutil.copy(os.path.join(build_dir, "x64", "Release", "libiconv-static.lib"), os.path.join(src_dir, "iconv.lib"))
    shutil.copy(os.path.join(src_dir, "iconv.lib"), os.path.join(src_dir, "iconv_a.lib"))

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_iconv", "1.16"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-iconv", "1.16")
        __mp__.add_wheel_dep_libs(w, "iconv", os.path.join(src_dir, "iconv.lib"))
        __mp__.add_wheel_dep_libs(w, "iconv", os.path.join(src_dir, "iconv_a.lib"))
        __mp__.add_wheel_dep_include(w, "iconv", os.path.join(src_dir, "include", "*"))

    return result_wheel
