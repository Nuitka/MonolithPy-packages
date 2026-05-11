import __mp__
from typing import *

import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    build_dir = os.path.join(src_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake", "-G", "Ninja",
                              "-DALSOFT_BACKEND_SNDIO=OFF",
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DLIBTYPE=STATIC", src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_openal", "1.21.1"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-openal", "1.21.1")
        __mp__.add_wheel_dep_libs(w, "openal", os.path.join(build_dir, "libopenal.a"))
        __mp__.add_wheel_dep_include(w, "openal", os.path.join(src_dir, "include", "*"),
                                     base_dir=os.path.join(src_dir, "include"))

    return result_wheel
