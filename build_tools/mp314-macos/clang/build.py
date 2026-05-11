import __mp__
from typing import *

import os
import tempfile
import platform
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    temp_dir = tempfile.mkdtemp()
    extract_dir = os.path.join(temp_dir, "extract")
    os.mkdir(extract_dir)
    if platform.machine() == "arm64":
        __mp__.download_extract("https://github.com/Nuitka/Nuitka-Python-packages/releases/download/dummy_llvm-19.1.7_macos/llvm-19.1.7-arm64.tar.xz",
                                extract_dir)
    else:
        __mp__.download_extract("https://github.com/Nuitka/Nuitka-Python-packages/releases/download/dummy_llvm-19.1.7_macos/llvm-19.1.7-x64.tar.xz",
                                extract_dir)

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-tool-clang", "19.1.7"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-tool-clang", "19.1.7")
        __mp__.add_wheel_build_tool(w, "clang", os.path.join(extract_dir, "*"))
        w.writestr("mpy_tool_clang-19.1.7.data/data/build_tools/clang/link.json",
                   '{"libraries": ["lib/libFortranEvaluate.a", "lib/libFortranRuntime.a", "lib/libFortranDecimal.a"]}')

    return result_wheel
