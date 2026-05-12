import __mp__
from typing import *

import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    build_dir = os.path.join(src_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.13"
    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release", src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_ogg", "1.3.5"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-ogg", "1.3.5")
        __mp__.add_wheel_dep_libs(w, "ogg", os.path.join(build_dir, "libogg.a"))
        __mp__.add_wheel_dep_include(w, "ogg", os.path.join(src_dir, "include", "**", "*.h"),
                                     base_dir=os.path.join(src_dir, "include"))
        __mp__.add_wheel_dep_include(w, "ogg", os.path.join(build_dir, "include", "*"),
                                     base_dir=os.path.join(build_dir, "include"))

    return result_wheel
