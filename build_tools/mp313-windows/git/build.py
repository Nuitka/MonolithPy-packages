import __np__
from typing import *

import os


def run(temp_dir: str):
    downloaded_file = __np__.download_file(
        "https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.1/PortableGit-2.47.1-32-bit.7z.exe", temp_dir)
    git_dir = os.path.join(temp_dir, "git")
    os.mkdir(git_dir)
    os.chdir(git_dir)
    __np__.run_build_tool_exe("7zip", "7z.exe", "x", downloaded_file)
    __np__.install_build_tool("git", os.path.join(git_dir, "*"))
