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
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DOGG_ROOT=" + __mp__.find_dep_root("ogg"),
                              "-DOGG_INCLUDE_DIRS=" + __mp__.find_dep_include("ogg"),
                              "-DOGG_LIBRARY=" + os.path.join(__mp__.find_dep_libs("ogg"), "libogg.a"),
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_vorbis", "1.3.7"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-vorbis", "1.3.7")
        __mp__.add_wheel_dep_libs(w, "vorbis", os.path.join(build_dir, "lib", "*.a"))
        __mp__.add_wheel_dep_include(w, "vorbis", os.path.join(src_dir, "include", "vorbis"),
                                     base_dir=os.path.join(src_dir, "include"))

    return result_wheel
