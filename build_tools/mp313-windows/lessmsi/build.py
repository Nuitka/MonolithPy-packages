import __np__
from typing import *

import os


def run(temp_dir: str):
    extract_dir = os.path.join(temp_dir, "lessmsi")
    os.mkdir(extract_dir)
    __np__.download_extract("https://github.com/activescott/lessmsi/releases/download/v2.2.0/lessmsi-v2.2.0.zip", extract_dir)
    __np__.install_build_tool("lessmsi", os.path.join(extract_dir, "*"))
