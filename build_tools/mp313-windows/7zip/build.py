import __mp__
import glob
from typing import *

import os


def run(temp_dir: str):
    downloaded_file = __mp__.download_file(
        "https://7-zip.org/a/7z2409.msi", temp_dir)

    os.chdir(temp_dir)
    __mp__.run_build_tool_exe("lessmsi", "lessmsi.exe", "x", downloaded_file)
    __mp__.install_build_tool("7zip", os.path.join(temp_dir, "7z2409", "SourceDir", "Files", "7-Zip", "*"))
