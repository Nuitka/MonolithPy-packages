import __mp__
import glob
from typing import *

import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-tool-clang", "21.1.8"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-tool-clang", "21.1.8")
        __mp__.add_wheel_build_tool(w, "clang", os.path.join(os.getcwd(), "*"))

    return result_wheel
