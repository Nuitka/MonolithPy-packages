import __mp__
from typing import *

import os
import glob
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    os.chdir(os.path.join(os.getcwd(), "bin"))
    __mp__.run_compiler_exe("mt.exe", "-manifest", os.path.join(os.path.dirname(__file__), "patch.exe.manifest"), "-outputresource:patch.exe;1")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-tool-patch", "2.5.9.post7"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-tool-patch", "2.5.9.post7")
        __mp__.add_wheel_build_tool(w, "patch", os.path.join(os.getcwd(), "*"))

    return result_wheel
