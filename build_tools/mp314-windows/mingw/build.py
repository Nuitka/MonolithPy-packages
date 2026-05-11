import __mp__
import glob
from typing import *

import os
import tempfile
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    temp_dir = tempfile.mkdtemp()
    result = __mp__.download_file("https://github.com/niXman/mingw-builds-binaries/releases/download/14.2.0-rt_v12-rev0/x86_64-14.2.0-release-win32-seh-msvcrt-rt_v12-rev0.7z",
                            temp_dir)

    os.chdir(temp_dir)
    __mp__.run_build_tool_exe("7zip", "7z.exe", "x", result)

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-tool-mingw", "14.2.0"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-tool-mingw", "14.2.0")
        __mp__.add_wheel_build_tool(w, "mingw", os.path.join(temp_dir, "mingw64", "*"))

    return result_wheel
