import __mp__
from typing import *

import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_eigen", "3.4.0"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-eigen", "3.4.0")
        __mp__.add_wheel_dep_include(w, "eigen", os.path.join(src_dir, "Eigen", "*"), base_dir=src_dir)

    return result_wheel
