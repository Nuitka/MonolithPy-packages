import __mp__
from typing import *

import os
import glob
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-tool-cmake", "3.30.5"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-tool-cmake", "3.30.5")
        __mp__.add_wheel_build_tool(w, "cmake", os.path.join(os.getcwd(), "*"))

    return result_wheel
