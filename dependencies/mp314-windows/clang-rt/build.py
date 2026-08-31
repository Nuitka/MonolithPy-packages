import __mp__
import glob
from typing import *

import os
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    # clang emits compiler-rt builtin calls that the MSVC CRT has no equivalent
    # for -- e.g. __divti3 (128-bit signed division), reached from sklearn's
    # _csr_polynomial_expansion. Those helpers live in clang_rt.builtins, which
    # ships INSIDE the clang toolchain (mpy-tool-clang). The monolithic relink
    # excludes build_tools, so the helpers go unresolved and /FORCE silently
    # ships them as calls to address 0 (a crash on first use). Split the builtins
    # archive out into a dependency lib -- exactly as flang-rt does for the
    # Fortran runtime -- so the relink links it. (Build tools cannot provide
    # libraries to the relink; a dependency package can.)
    clang_exe = __mp__.find_build_tool_exe("clang", "clang.exe")
    clang_root = os.path.dirname(os.path.dirname(clang_exe))
    matches = glob.glob(os.path.join(
        clang_root, "lib", "clang", "*", "lib", "windows",
        "clang_rt.builtins-x86_64.lib"))
    if not matches:
        raise RuntimeError(
            "clang_rt.builtins-x86_64.lib not found under %s" % clang_root)
    builtins = matches[0]

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-dep-clang-rt", "21.1.8"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-clang-rt", "21.1.8")
        __mp__.add_wheel_dep_libs(w, "clang-rt", builtins)
        w.writestr("mpy_dep_clang_rt-21.1.8.data/data/dependency_libs/clang-rt/link.json",
                   '{"library_dirs": ["lib"], "libraries": ["clang_rt.builtins-x86_64.lib"]}')

    return result_wheel
