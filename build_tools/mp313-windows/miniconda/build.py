import __np__
import glob
from typing import *

import os


def run(temp_dir: str):
    __np__.download_extract(
        "https://github.com/Nuitka/Nuitka-Python-packages/releases/download/dummy_miniconda_25.1.1/Miniconda3-py311_25.1.1-2-Windows-x86_64.zip",
        temp_dir)
    __np__.install_build_tool("miniconda", os.path.join(temp_dir, "miniconda3", "*"), ignore_errors=True)
