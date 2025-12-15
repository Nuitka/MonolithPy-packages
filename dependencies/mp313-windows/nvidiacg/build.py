import __mp__
from typing import *

import os
import shutil
import glob
import sysconfig


def run(temp_dir: str):
    __mp__.download_extract("http://www.panda3d.org/download/noversion/nvidiacg-win64.zip", temp_dir)

    __mp__.install_dep_libs("nvidiacg", os.path.join(temp_dir, "nvidiacg", "lib", "*.lib"))
    __mp__.install_dep_include("nvidiacg", os.path.join(temp_dir, "nvidiacg", "include", "*"))
    # We must also install the proprietary DLLs. :(
    __mp__.install_files(sysconfig.get_config_var('BINDIR'), os.path.join(temp_dir, "nvidiacg", "bin", "*.dll"))
    __mp__.install_files(os.path.join(__mp__.find_dep_root("nvidiacg"), "bin"), os.path.join(temp_dir, "nvidiacg", "bin", "*.dll"))
