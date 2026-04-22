import __mp__
from typing import *

import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-tool-ninja", "1.12.1"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-tool-ninja", "1.12.1")
        __mp__.add_wheel_build_tool(w, "ninja", os.path.join(os.getcwd(), "*"))

    return result_wheel
