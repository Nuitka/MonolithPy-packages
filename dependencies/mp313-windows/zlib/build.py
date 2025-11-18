import __np__
from typing import *

import os
import shutil


def run(temp_dir: str):
    __np__.download_extract("https://github.com/madler/zlib/archive/refs/tags/v1.2.12.zip", temp_dir)

    __np__.setup_compiler_env()

    __np__.auto_patch_build(os.path.join(temp_dir, "zlib-1.2.12", "win32"))

    os.chdir(os.path.join(temp_dir, "zlib-1.2.12"))

    __np__.nmake("/f", "win32/Makefile.msc")

    __np__.install_dep_libs("zlib", os.path.join(temp_dir, "zlib-1.2.12", "zlib.lib"))
    __np__.install_dep_include("zlib", os.path.join(temp_dir, "zlib-1.2.12", "*.h"))
