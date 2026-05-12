import __mp__
import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    install_dir = os.path.join(src_dir, "install")
    os.mkdir(install_dir)
    build_dir = os.path.join(src_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.13"
    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"]

    __mp__.run_build_tool_exe("cmake", "cmake", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF",
                              "-DCMAKE_INSTALL_PREFIX=" + install_dir,
                              "-DLIBXML2_WITH_PROGRAMS=OFF", "-DLIBXML2_WITH_TESTS=OFF",
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja")
    __mp__.run_build_tool_exe("ninja", "ninja", "install")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_libxml2", "2.15.2"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-libxml2", "2.15.2")
        __mp__.add_wheel_dep_libs(w, "libxml2", os.path.join(install_dir, "lib", "*.a"),
                                  base_dir=os.path.join(install_dir, "lib"))
        __mp__.add_wheel_dep_include(w, "libxml2", os.path.join(install_dir, "include", "libxml2", "*"))

    return result_wheel
