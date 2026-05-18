import __mp__
from typing import *

import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-tool-cmake", "3.31.4"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-tool-cmake", "3.31.4")
        __mp__.add_wheel_build_tool(w, "cmake", os.path.join(os.getcwd(), "CMake.app", "Contents", "*"))

    return result_wheel
