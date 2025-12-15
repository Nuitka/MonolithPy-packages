import __mp__
import glob
from typing import *

import os


def run(temp_dir: str):
    __mp__.download_extract("https://github.com/Kitware/CMake/releases/download/v3.31.4/cmake-3.31.4-macos-universal.tar.gz",
                            temp_dir)
    __mp__.install_build_tool("cmake", os.path.join(temp_dir, "cmake-3.31.4-macos-universal", "CMake.app", "Contents", "*"))
