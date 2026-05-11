import __mp__
import shutil
import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    os.chdir(os.path.join(src_dir, "win32"))

    install_dir = os.path.join(src_dir, "install_tmp")

    __mp__.setup_compiler_env()
    __mp__.auto_patch_build(src_dir)
    __mp__.patch_all_source(src_dir)

    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"]
    __mp__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir,
                              "-DIconv_INCLUDE_DIR=" + __mp__.find_dep_include("iconv"),
                              "-DIconv_LIBRARY=" + os.path.join(__mp__.find_dep_libs("iconv"), "iconv.lib"),
                              "-DLIBXML2_WITH_PROGRAMS=OFF", "-DLIBXML2_WITH_TESTS=OFF",
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja.exe")
    __mp__.run_build_tool_exe("ninja", "ninja.exe", "install")

    __mp__.prepend_to_file(os.path.join(install_dir, "include", "libxml2", "libxml", "xmlexports.h"), "#define LIBXML_STATIC\n")

    # lxml's setup.py in --static mode looks for libxml2_a.lib, but CMake's
    # RELEASE_POSTFIX='s' gives us libxml2s.lib. Rename.
    lib_dir = os.path.join(install_dir, "lib")
    src = os.path.join(lib_dir, "libxml2s.lib")
    if os.path.isfile(src):
        shutil.copy(src, os.path.join(lib_dir, "libxml2_a.lib"))

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_libxml2", "2.15.2"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-libxml2", "2.15.2")
        __mp__.add_wheel_dep_libs(w, "libxml2", os.path.join(install_dir, "lib", "*.lib"), os.path.join(install_dir, "lib", "cmake"))
        __mp__.add_wheel_dep_include(w, "libxml2", os.path.join(install_dir, "include", "libxml2"))

    return result_wheel
