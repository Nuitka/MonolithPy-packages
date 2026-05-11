import __mp__
import glob
from typing import *

import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    os.rename(os.path.join(os.getcwd(), "_conda.exe"), os.path.join(os.getcwd(), "conda.exe"))
    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-tool-miniconda", "26.1.1"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-tool-miniconda", "26.1.1")
        __mp__.add_wheel_build_tool(w, "miniconda", os.path.join(os.getcwd(), "*"))

    return result_wheel
