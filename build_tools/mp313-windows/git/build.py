import __mp__
from typing import *

import os
import tempfile
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    temp_dir = tempfile.mkdtemp()
    downloaded_file = __mp__.download_file(
        "https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.1/PortableGit-2.47.1-32-bit.7z.exe", temp_dir)
    git_dir = os.path.join(temp_dir, "git")
    os.mkdir(git_dir)
    os.chdir(git_dir)
    __mp__.run_build_tool_exe("7zip", "7z.exe", "x", downloaded_file)

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-tool-git", "2.47.1"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-tool-git", "2.47.1")
        __mp__.add_wheel_build_tool(w, "git", os.path.join(git_dir, "*"))

    return result_wheel
