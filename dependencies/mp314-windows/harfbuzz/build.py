import __mp__
from typing import *

import os
import shutil
import glob
import tempfile
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    # Harfbuzz depends on freetype and freetype depends on harfbuzz. :(
    # We will build freetype first here and then base off that, but we will also have a separate freetype package.
    ft_dir = tempfile.mkdtemp()

    __mp__.download_extract("http://download-mirror.savannah.gnu.org/releases/freetype/freetype-2.14.3.tar.gz", ft_dir)

    __mp__.setup_compiler_env()

    ft_src_dir = glob.glob(os.path.join(ft_dir, "freetype*"))[0]

    __mp__.auto_patch_build(ft_src_dir)
    __mp__.patch_all_source(ft_src_dir)

    ft_build_dir = os.path.join(ft_dir, "build")
    os.mkdir(ft_build_dir)
    os.chdir(ft_build_dir)

    ft_install_dir = os.path.join(ft_dir, "install")
    os.mkdir(ft_install_dir)

    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ[
        "PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DCMAKE_INSTALL_PREFIX=" + ft_install_dir,
                              "-DZLIB_ROOT=" + __mp__.find_dep_root("zlib"),
                              "-DWITH_HarfBuzz=OFF", "-DWITH_BZip2=OFF",
                              "-DWITH_PNG=OFF", ft_src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja.exe")

    __mp__.run_build_tool_exe("ninja", "ninja.exe", "install")

    os.chdir(src_dir)

    __mp__.auto_patch_build(src_dir)
    __mp__.patch_all_source(src_dir)

    build_dir = os.path.join(src_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    install_dir = os.path.join(src_dir, "install")
    os.mkdir(install_dir)

    # Build WITH graphite2 so this harfbuzz matches the depLibs harfbuzz
    # configuration (XeTeX needs Graphite; the two must be interchangeable
    # against the same static Qt). graphite2 is a build dependency, installed
    # under its dependency_libs root; add it to CMAKE_PREFIX_PATH so harfbuzz's
    # find_path/find_library locate graphite2/Font.h + graphite2.lib.
    # GRAPHITE2_STATIC: graphite2's headers mark gr_* as __declspec(dllimport)
    # unless this is defined, so hb-graphite2.cc would otherwise emit __imp_gr_*
    # refs that do not resolve against the static graphite2.lib.
    graphite2_root = __mp__.find_dep_root("graphite2")
    __mp__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir,
                              "-DCMAKE_PREFIX_PATH=" + ft_install_dir + ";" + graphite2_root,
                              "-DHB_HAVE_FREETYPE=ON", "-DHB_BUILD_TESTS=OFF",
                              "-DHB_BUILD_UTILS=OFF", "-DHB_BUILD_SUBSET=OFF",
                              "-DHB_HAVE_GRAPHITE2=ON",
                              "-DCMAKE_C_FLAGS=-DGRAPHITE2_STATIC",
                              "-DCMAKE_CXX_FLAGS=-DGRAPHITE2_STATIC",
                              "-DHB_HAVE_INTROSPECTION=OFF", "-DHB_HAVE_CORETEXT=OFF",
                              f"-DFREETYPE_INCLUDE_DIR_freetype2={ft_install_dir}/include/freetype2",
                              f"-DFREETYPE_INCLUDE_DIR_ft2build={ft_install_dir}/include/freetype2",
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja.exe")

    __mp__.run_build_tool_exe("ninja", "ninja.exe", "install")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_harfbuzz", "14.2.1"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-harfbuzz", "14.2.1")
        __mp__.add_wheel_dep_libs(w, "harfbuzz", os.path.join(install_dir, "lib", "*.lib"))
        __mp__.add_wheel_dep_include(w, "harfbuzz", os.path.join(install_dir, "include", "harfbuzz", "*.h"))

    return result_wheel
