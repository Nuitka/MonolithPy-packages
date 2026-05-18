import __mp__
from typing import *

import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    # We have to use the git download instead of the official archive since it is missing
    # the file "opus_buildtype.cmake" at time of writing. :(
    src_dir = os.getcwd()

    # We have to write this file manually since it is not included in git.
    with open(os.path.join(src_dir, "package_version"), 'w') as f:
        f.write('PACKAGE_VERSION="1.3.1"\n')

    build_dir = os.path.join(src_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.13"
    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release", src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_opus", "1.3.1"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-opus", "1.3.1")
        __mp__.add_wheel_dep_libs(w, "opus", os.path.join(build_dir, "libopus.a"))
        __mp__.add_wheel_dep_include(w, "opus", os.path.join(src_dir, "include", "*.h"))

    return result_wheel
