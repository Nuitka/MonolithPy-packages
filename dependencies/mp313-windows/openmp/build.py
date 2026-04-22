import __mp__
from typing import *

import os
import shutil
import glob
import sys
import tempfile
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    # Download LLVM CMake modules required for standalone build
    cmake_tmp = tempfile.mkdtemp()
    __mp__.download_extract("https://github.com/llvm/llvm-project/releases/download/llvmorg-21.1.8/cmake-21.1.8.src.tar.xz", cmake_tmp)

    __mp__.setup_compiler_env()

    cmake_dir = glob.glob(os.path.join(cmake_tmp, "cmake*"))[0]

    __mp__.auto_patch_build(src_dir)

    # Patch out the check that prevents static library builds on Windows
    runtime_cmake = os.path.join(src_dir, "runtime", "CMakeLists.txt")
    with open(runtime_cmake, "r") as f:
        content = f.read()
    content = content.replace(
        'if(WIN32 AND NOT LIBOMP_ENABLE_SHARED)\n  libomp_error_say("Static libraries requested but not available on Windows")\nendif()',
        '# Patched: Allow static library builds on Windows\n# if(WIN32 AND NOT LIBOMP_ENABLE_SHARED)\n#   libomp_error_say("Static libraries requested but not available on Windows")\n# endif()'
    )
    with open(runtime_cmake, "w") as f:
        f.write(content)

    build_dir = os.path.join(src_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + os.environ["PATH"]
    # Use forward slashes for CMake paths to avoid escape character issues
    cmake_module_path = os.path.join(cmake_dir, "Modules").replace("\\", "/")
    # Use the current Python executable to avoid environment conflicts
    python_exe = sys.executable.replace("\\", "/")
    __mp__.run_build_tool_exe("cmake", "cmake.exe", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DLIBOMP_ENABLE_SHARED=OFF",
                              "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded",
                              "-DCMAKE_MODULE_PATH=" + cmake_module_path,
                              "-DPython3_EXECUTABLE=" + python_exe,
                              src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja.exe")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_openmp", "21.1.8"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-openmp", "21.1.8")
        __mp__.add_wheel_dep_libs(w, "openmp", os.path.join(build_dir, "runtime", "src", "*.lib"))
        __mp__.add_wheel_dep_include(w, "openmp", os.path.join(build_dir, "runtime", "src", "omp.h"))

    return result_wheel

