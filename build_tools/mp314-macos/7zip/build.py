import __mp__
from typing import *

import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-tool-7zip", "24.09"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-tool-7zip", "24.09")
        __mp__.add_wheel_build_tool(w, "7zip", os.path.join(os.getcwd(), "*"))

    return result_wheel
