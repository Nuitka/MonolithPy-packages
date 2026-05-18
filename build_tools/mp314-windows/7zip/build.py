import __mp__
import glob
from typing import *

import os
import tempfile
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    temp_dir = tempfile.mkdtemp()
    downloaded_file = __mp__.download_file(
        "https://7-zip.org/a/7z2409.msi", temp_dir)

    os.chdir(temp_dir)
    __mp__.run_build_tool_exe("lessmsi", "lessmsi.exe", "x", downloaded_file)

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-tool-7zip", "24.09"))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-tool-7zip", "24.09")
        __mp__.add_wheel_build_tool(w, "7zip", os.path.join(temp_dir, "7z2409", "SourceDir", "Files", "7-Zip", "*"))

    return result_wheel
