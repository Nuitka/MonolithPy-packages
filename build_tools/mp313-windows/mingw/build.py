import __np__
import glob
from typing import *

import os


def run(temp_dir: str):
    result = __np__.download_file("https://github.com/niXman/mingw-builds-binaries/releases/download/14.2.0-rt_v12-rev0/x86_64-14.2.0-release-win32-seh-msvcrt-rt_v12-rev0.7z",
                            temp_dir)

    os.chdir(temp_dir)
    __np__.run_build_tool_exe("7zip", "7z.exe", "x", result)

    __np__.install_build_tool("mingw", os.path.join(temp_dir, "mingw64", "*"))
