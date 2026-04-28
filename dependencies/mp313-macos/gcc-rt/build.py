import __mp__
from typing import *

import glob
import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    gcc_lib_dir = os.path.dirname(__mp__.find_build_tool_exe("gcc", "gfortran-nuitka"))
    gcc_root = os.path.dirname(gcc_lib_dir)
    lib_dir = os.path.join(gcc_root, "lib")

    libs = []
    for name in ["libgfortran.a", "libgcc.a", "libquadmath.a"]:
        path = os.path.join(lib_dir, name)
        if os.path.isfile(path):
            libs.append(path)
        else:
            found = glob.glob(os.path.join(gcc_root, "**", name), recursive=True)
            if found:
                libs.append(found[0])
            else:
                raise FileNotFoundError(f"Could not find {name} in gcc tool at {gcc_root}")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-dep-gcc-rt", "14"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-gcc-rt", "14")
        __mp__.add_wheel_dep_libs(w, "gcc-rt", *libs)

    return result_wheel
