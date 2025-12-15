import __mp__
from typing import *

import os
import shutil


def run(temp_dir: str):
    __mp__.download_extract("https://github.com/madler/zlib/archive/refs/tags/v1.2.12.zip", temp_dir)

    __mp__.setup_compiler_env()

    __mp__.auto_patch_build(os.path.join(temp_dir, "zlib-1.2.12", "win32"))

    os.chdir(os.path.join(temp_dir, "zlib-1.2.12"))

    __mp__.nmake("/f", "win32/Makefile.msc")

    __mp__.install_dep_libs("zlib", os.path.join(temp_dir, "zlib-1.2.12", "zlib.lib"))
    __mp__.install_dep_include("zlib", os.path.join(temp_dir, "zlib-1.2.12", "*.h"))
