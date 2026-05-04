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
                              "-DCMAKE_PREFIX_PATH=" + __mp__.find_dep_root("libxml2"),
                              "-DLIBXSLT_WITH_PROGRAMS=OFF", "-DLIBXSLT_WITH_PYTHON=OFF",
                              "-DLIBXSLT_WITH_TESTS=OFF",
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja.exe")
    __mp__.run_build_tool_exe("ninja", "ninja.exe", "install")

    # libxslt's exports.h uses __declspec(dllimport) unless LIBXSLT_STATIC is
    # defined. lxml doesn't define it, so inject it at the top of the headers.
    for header, guard in (
        ("libxslt/xsltexports.h", "LIBXSLT_STATIC"),
        ("libexslt/exsltexports.h", "LIBEXSLT_STATIC"),
    ):
        p = os.path.join(install_dir, "include", header)
        if os.path.isfile(p):
            __mp__.prepend_to_file(p, "#define %s\n" % guard)

    # lxml's setup.py in --static mode looks for libxslt_a.lib / libexslt_a.lib,
    # but CMake's RELEASE_POSTFIX='s' gives us libxslts.lib / libexslts.lib. Rename.
    lib_dir = os.path.join(install_dir, "lib")
    for base in ("libxslt", "libexslt"):
        src = os.path.join(lib_dir, base + "s.lib")
        if os.path.isfile(src):
            shutil.copy(src, os.path.join(lib_dir, base + "_a.lib"))

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_libxslt", "1.1.45"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-libxslt", "1.1.45")
        __mp__.add_wheel_dep_libs(w, "libxslt", os.path.join(install_dir, "lib", "*.lib"))
        __mp__.add_wheel_dep_libs(w, "libxslt", os.path.join(install_dir, "lib", "cmake"))
        __mp__.add_wheel_dep_include(w, "libxslt", os.path.join(install_dir, "include", "*"))

    return result_wheel
