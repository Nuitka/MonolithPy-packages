import __mp__
from typing import *

import os


def run(temp_dir: str):
    __mp__.download_extract("https://sourceforge.net/projects/gnuwin32/files/patch/2.5.9-7/patch-2.5.9-7-bin.zip/download", temp_dir)
    os.chdir(os.path.join(temp_dir, "bin"))
    __mp__.run_compiler_exe("mt.exe", "-manifest", os.path.join(temp_dir, "patch.exe.manifest"), "-outputresource:patch.exe;1")
    __mp__.install_build_tool("patch", os.path.join(temp_dir, "bin", "*"))
