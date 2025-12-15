import __mp__
import glob
from typing import *
import os
import platform


def run(temp_dir: str):
    extract_dir = os.path.join(temp_dir, "extract")
    os.mkdir(extract_dir)
    if platform.machine() == "arm64":
        __mp__.download_extract("https://github.com/Nuitka/Nuitka-Python-packages/releases/download/dummy_llvm-19.1.7_macos/llvm-19.1.7-arm64.tar.xz",
                                extract_dir)
        __mp__.install_build_tool("clang", os.path.join(extract_dir, "*"))
    else:
        __mp__.download_extract("https://github.com/Nuitka/Nuitka-Python-packages/releases/download/dummy_llvm-19.1.7_macos/llvm-19.1.7-x64.tar.xz",
                                extract_dir)
        __mp__.install_build_tool("clang", os.path.join(extract_dir, "*"))

    with open(os.path.join(__mp__.getToolsInstallDir(), "clang", "link.json"), 'w') as f:
        f.write('{"libraries": ["lib/libFortranEvaluate.a", "lib/libFortranRuntime.a", "lib/libFortranDecimal.a"]}')
    
