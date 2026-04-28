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
        __mp__.download_extract("https://github.com/Nuitka/Nuitka-Python-packages/releases/download/dummy_gcc-14_macos/gcc-14-arm64.tar.xz",
                                extract_dir)
    else:
        __mp__.download_extract("https://github.com/Nuitka/Nuitka-Python-packages/releases/download/dummy_gcc-14_macos/gcc-14-x64.tar.xz",
                                extract_dir)

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-tool-gcc", "14"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-tool-gcc", "14")
        __mp__.add_wheel_build_tool(w, "gcc", os.path.join(extract_dir, "*"))

    return result_wheel
