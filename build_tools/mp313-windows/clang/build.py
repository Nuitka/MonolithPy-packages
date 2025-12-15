import __mp__
import glob
from typing import *

import os


def run(temp_dir: str):
    __mp__.download_extract("https://github.com/llvm/llvm-project/releases/download/llvmorg-19.1.6/clang+llvm-19.1.6-x86_64-pc-windows-msvc.tar.xz",
                            temp_dir)
    __mp__.install_build_tool("clang", os.path.join(temp_dir, "clang+llvm-19.1.6-x86_64-pc-windows-msvc", "*"))
