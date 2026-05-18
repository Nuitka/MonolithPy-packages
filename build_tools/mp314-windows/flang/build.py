import __mp__
import glob
from typing import *

import os
import tempfile
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    temp_dir = tempfile.mkdtemp()
    __mp__.run_build_tool_exe("miniconda", "conda.exe", "config", "--add", "channels", "conda-forge")

    # It seems that miniconda is the only way to get prebuilt binaries for flang on windows :(
    # Revisit this when LLVM finally decides to publish windows binaries for flang.
    __mp__.run_build_tool_exe("miniconda", "conda.exe", "create", "--prefix=" + temp_dir, "-y",
                              "perl", "flang-rt_win-64=22.1.0", "libflang=20.1.8", "flang=22.1.0")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-tool-flang", "22.1.0"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-tool-flang", "22.1.0")
        __mp__.add_wheel_build_tool(w, "flang", os.path.join(temp_dir, "Library", "*"))

    return result_wheel
