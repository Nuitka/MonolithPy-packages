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
    # The whole MonolithPy embed is static /MT. We must ship only /MT (static-CRT) libs or a
    # consumer that links the embed pulls in the dynamic CRT (vcruntime/msvcp*), which the
    # buildMonolithPyEmbed /MT gate rejects. conda-forge's flang packaging makes this fiddly:
    #   * flang_rt.runtime.static.lib -> from flang-rt_win-64 22.1.0 (already /MT, matches the
    #     flang 22.1.0 compiler in build_tools). It imports 12 Fortran::decimal symbols and zero
    #     Fortran::evaluate symbols, so it needs FortranDecimal but NOT FortranEvaluate.
    #   * FortranDecimal.static.lib   -> from flang 20.1.8, the last release to ship a /MT (.static)
    #     variant (flang 21+ ships only a /MD FortranDecimal.lib). Its exported decimal symbols are
    #     an exact superset of the 12 the v22 runtime imports, so it is an ABI-clean drop-in.
    #   * FortranEvaluate.lib         -> dropped. It is a huge compile-time frontend library, /MD-only
    #     in every flang version, and the runtime never references it.
    # flang-rt_win-64 22.1.0 requires flang ==22.1.0, so it cannot share a prefix with flang 20.1.8
    # even under --no-deps (the solver still enforces the constraint); use two separate prefixes.
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
