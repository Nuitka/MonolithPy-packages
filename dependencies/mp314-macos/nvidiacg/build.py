import __mp__
from typing import *

import os
import tempfile
import platform
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy_dep_nvidiacg", "3.1.0013-1"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-nvidiacg", "3.1.0013-1")

        if platform.processor() != "arm":
            temp_dir = tempfile.mkdtemp()
            __mp__.download_extract("https://www.panda3d.org/download/panda3d-1.10.11/panda3d-1.10.11-tools-mac.tar.gz", temp_dir)
            nvidiacg_dir = os.path.join(temp_dir, "panda3d-1.10.11/thirdparty/darwin-libs-a/nvidiacg")
            __mp__.add_wheel_dep_libs(w, "nvidiacg", os.path.join(nvidiacg_dir, "lib", "*.dylib"))
            __mp__.add_wheel_dep_include(w, "nvidiacg", os.path.join(nvidiacg_dir, "include", "*"),
                                         base_dir=os.path.join(nvidiacg_dir, "include"))
            # We must also install the proprietary DLLs. :(
            __mp__.add_wheel_files(w, "dependency_libs/nvidiacg/bin", os.path.join(nvidiacg_dir, "lib", "*.dylib"))

    return result_wheel
