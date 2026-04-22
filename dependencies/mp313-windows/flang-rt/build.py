import __mp__
import glob
from typing import *

import os
import tempfile
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    temp_dir = tempfile.mkdtemp()
    __mp__.run_build_tool_exe("miniconda", "conda.exe", "config", "--add", "channels", "conda-forge")

    # It seems that miniconda is the only way to get prebuilt binaries for flang on windows :(
    # Revisit this when LLVM finally decides to publish windows binaries for flang.
    __mp__.run_build_tool_exe("miniconda", "conda.exe", "create", "--prefix=" + temp_dir,
                              "-y", "--no-deps", "libflang=20.1.8", "flang-rt_win-64=22.1.0", "flang=22.1.0")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-dep-flang-rt", "22.1.0"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-flang-rt", "22.1.0")
        __mp__.add_wheel_dep_libs(w, "flang-rt",
                                  os.path.join(temp_dir, "Library", "lib", "FortranDecimal.lib"),
                                  os.path.join(temp_dir, "Library", "lib", "FortranEvaluate.lib"),
                                  os.path.join(temp_dir, "Library", "lib", "clang", "22", "lib", "x86_64-pc-windows-msvc", "flang_rt.runtime.static.lib"))
        w.writestr("mpy_dep_flang_rt-22.1.0.data/data/dependency_libs/flang-rt/link.json",
                   '{"library_dirs": ["lib"], "libraries": ["flang_rt.runtime.static.lib", "FortranDecimal.lib", "FortranEvaluate.lib"]}')

    return result_wheel
