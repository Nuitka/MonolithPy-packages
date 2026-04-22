import __mp__
from typing import *

import os
import shutil
import glob
import sysconfig
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    src_dir = os.getcwd()

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_nvidiacg", "3.1.0013"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-nvidiacg", "3.1.0013")
        __mp__.add_wheel_dep_libs(w, "nvidiacg", os.path.join(src_dir, "nvidiacg", "lib", "*.lib"))
        __mp__.add_wheel_dep_include(w, "nvidiacg", os.path.join(src_dir, "nvidiacg", "include", "*"),
                                     base_dir=os.path.join(src_dir, "nvidiacg", "include"))
        # We must also install the proprietary DLLs. :(
        __mp__.add_wheel_files(w, "dependency_libs/nvidiacg/bin", os.path.join(src_dir, "nvidiacg", "bin", "*.dll"))

    return result_wheel
