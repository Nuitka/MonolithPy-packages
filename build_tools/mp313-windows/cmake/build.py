import __mp__
from typing import *

import os


def run(temp_dir: str):
    __mp__.download_extract("https://github.com/Kitware/CMake/releases/download/v3.30.5/cmake-3.30.5-windows-i386.zip", temp_dir)
    __mp__.install_build_tool("cmake", os.path.join(temp_dir, "cmake-3.30.5-windows-i386", "*"))
