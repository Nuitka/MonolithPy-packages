import __np__
import glob
from typing import *

import os


def run(temp_dir: str):
    __np__.run_build_tool_exe("miniconda", "conda.exe", "config", "--add", "channels", "conda-forge")

    # It seems that miniconda is the only way to get prebuilt binaries for flang on windows :(
    # Revisit this when LLVM finally decides to publish windows binaries for flang.
    __np__.run_build_tool_exe("miniconda", "conda.exe", "create", "--prefix=" + temp_dir, "-y",
                              "flang", "perl", "libflang", "flang-rt_win-64")

    __np__.install_build_tool("flang", os.path.join(temp_dir, "Library", "*"))

    with open(os.path.join(__np__.getToolsInstallDir(), "flang", "link.json"), 'w') as f:
        f.write('{"library_dirs": ["lib", "lib/clang/21/lib/x86_64-pc-windows-msvc"], "libraries": ["lib/clang/21/lib/x86_64-pc-windows-msvc/flang_rt.runtime.static.lib", "lib/FortranEvaluate.lib"]}')
