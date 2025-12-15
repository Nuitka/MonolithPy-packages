import __mp__
from typing import *

import os
import sys
import shutil
import glob
import sysconfig
import platform


def run(temp_dir: str):
    if platform.processor() == "arm":
        os.makedirs(os.path.join(__mp__.getDependencyInstallDir(), "nvidiacg"), exist_ok=True)
        with open(os.path.join(__mp__.getDependencyInstallDir(), "nvidiacg", "no-op.txt"), 'w') as f:
            f.write("Unavailable for arm.")
        return  # cg is not supported for arm64. :(

    __mp__.download_extract("https://www.panda3d.org/download/panda3d-1.10.11/panda3d-1.10.11-tools-mac.tar.gz", temp_dir)

    __mp__.install_dep_libs("nvidiacg", os.path.join(temp_dir, "panda3d-1.10.11/thirdparty/darwin-libs-a/nvidiacg", "lib", "*.dylib"))
    __mp__.install_files(os.path.dirname(os.path.realpath(sys.executable)), os.path.join(temp_dir, "panda3d-1.10.11/thirdparty/darwin-libs-a/nvidiacg", "lib", "*.dylib"))
    __mp__.install_files(os.path.join(os.path.dirname(os.path.realpath(sys.executable)), "..", "lib"),
                         os.path.join(temp_dir, "panda3d-1.10.11/thirdparty/darwin-libs-a/nvidiacg", "lib", "*.dylib"))
    # We must also install the proprietary DLLs. :(
    __mp__.install_dep_include("nvidiacg", os.path.join(temp_dir, "panda3d-1.10.11/thirdparty/darwin-libs-a/nvidiacg", "include", "*"))
