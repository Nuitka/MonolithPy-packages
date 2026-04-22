import __mp__
from typing import *

import os
import glob
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-tool-lessmsi", "2.2.0"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-tool-lessmsi", "2.2.0")
        __mp__.add_wheel_build_tool(w, "lessmsi", os.path.join(os.getcwd(), "*"))

    return result_wheel
