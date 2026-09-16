import __mp__
import glob
from typing import *

import os
import tempfile
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    __mp__.run_build_tool_exe("miniconda", "conda.exe", "config", "--add", "channels", "conda-forge")

    # It seems that miniconda is the only way to get prebuilt binaries for flang on windows :(
    # Revisit this when LLVM finally decides to publish windows binaries for flang.
    #
    # The embed is static /MT, so every shipped lib must be /MT. conda-forge's flang:
    #   * flang_rt.runtime.static.lib <- flang-rt_win-64 22.1.0 (/MT). Imports 12
    #     Fortran::decimal symbols, zero Fortran::evaluate.
    #   * FortranDecimal.static.lib   <- flang 20.1.8, the last /MT (.static) release
    #     (21+ ship only /MD); its decimal exports cover the 12 above.
    #   * FortranEvaluate.lib         -> dropped; the runtime never references it.
    # flang-rt_win-64 22.1.0 requires flang==22.1.0, so it can't share a prefix with
    # flang 20.1.8 (the solver enforces it even under --no-deps) -> two prefixes.
    runtime_dir = tempfile.mkdtemp()
    __mp__.run_build_tool_exe("miniconda", "conda.exe", "create", "--prefix=" + runtime_dir,
                              "-y", "--no-deps", "flang-rt_win-64=22.1.0")

    decimal_dir = tempfile.mkdtemp()
    __mp__.run_build_tool_exe("miniconda", "conda.exe", "create", "--prefix=" + decimal_dir,
                              "-y", "--no-deps", "flang=20.1.8")

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-dep-flang-rt", "22.1.0"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-flang-rt", "22.1.0")
        __mp__.add_wheel_dep_libs(w, "flang-rt",
                                  os.path.join(runtime_dir, "Library", "lib", "clang", "22", "lib", "x86_64-pc-windows-msvc", "flang_rt.runtime.static.lib"),
                                  os.path.join(decimal_dir, "Library", "lib", "FortranDecimal.static.lib"))
        w.writestr("mpy_dep_flang_rt-22.1.0.data/data/dependency_libs/flang-rt/link.json",
                   '{"library_dirs": ["lib"], "libraries": ["flang_rt.runtime.static.lib", "FortranDecimal.static.lib"]}')

    return result_wheel
