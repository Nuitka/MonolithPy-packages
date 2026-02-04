import __mp__
import glob
from typing import *

import os


def run(temp_dir: str):
    __mp__.download_extract("https://github.com/llvm/llvm-project/releases/download/llvmorg-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc.tar.xz",
                            temp_dir)
    __mp__.install_build_tool("clang", os.path.join(temp_dir, "clang+llvm-21.1.8-x86_64-pc-windows-msvc", "*"))
