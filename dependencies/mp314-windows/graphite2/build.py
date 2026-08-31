import __mp__
from typing import *

import os
import re
import glob
import sysconfig
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    # graphite2 is the SIL Graphite shaping engine. HarfBuzz is built against it
    # (HB_HAVE_GRAPHITE2=ON) so the MonolithPy harfbuzz matches the depLibs
    # harfbuzz byte-for-byte in configuration -- both reference gr_* and both are
    # satisfied by this one static graphite2 the bundle now ships. Mirrors the
    # depLibs graphite2 1.3.14 build (see TrySail .github/build_dep_libs_win.ps1).
    src_dir = os.getcwd()

    __mp__.setup_compiler_env()

    __mp__.auto_patch_build(src_dir)
    __mp__.patch_all_source(src_dir)

    # graphite2's default build also compiles tests/doc/gr2fonttest, whose
    # install rules reference binaries we do not build (and which would drag the
    # mp_embed link-injection into throwaway executables). Drop them; we only
    # want the static graphite2 library.
    cml = os.path.join(src_dir, "CMakeLists.txt")
    with open(cml) as f:
        lines = f.readlines()
    with open(cml, "w") as f:
        for line in lines:
            if re.search(r"add_subdirectory\((tests|doc|gr2fonttest)\)", line):
                continue
            f.write(line)

    build_dir = os.path.join(src_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    install_dir = os.path.join(src_dir, "install")
    os.mkdir(install_dir)

    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ[
        "PATH"]

    # graphite2's CMakeLists has no `cmake_minimum_required(VERSION x)` line
    # (it opens with project()), so __mp__.auto_patch_build's CMakeLists rewrite
    # never fires on it -- yet patch_all_source still prepends `#include
    # "mp_embed.h"` to every source. Supply what that rewrite normally would:
    #   * -I<INCLUDEPY> so the prepended mp_embed.h is found (else C1083), and
    #   * CMAKE_MSVC_RUNTIME_LIBRARY + CMP0091 NEW to pin the static CRT (/MT).
    inc = sysconfig.get_config_var("INCLUDEPY").replace("\\", "/")
    __mp__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir,
                              "-DBUILD_SHARED_LIBS=OFF",
                              "-DCMAKE_POLICY_DEFAULT_CMP0091=NEW",
                              "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded",
                              "-DCMAKE_C_FLAGS=-I" + inc,
                              "-DCMAKE_CXX_FLAGS=-I" + inc,
                              "-DGRAPHITE2_COMPARE_RENDERER=OFF",
                              "-DGRAPHITE2_NTRACING=ON",
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja.exe")

    __mp__.run_build_tool_exe("ninja", "ninja.exe", "install")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_graphite2", "1.3.14"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-graphite2", "1.3.14")
        __mp__.add_wheel_dep_libs(w, "graphite2", os.path.join(install_dir, "lib", "*.lib"))
        __mp__.add_wheel_dep_include(w, "graphite2", os.path.join(install_dir, "include", "graphite2", "*.h"))

    return result_wheel
