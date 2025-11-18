import __np__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __np__.download_extract("https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip", temp_dir)

    src_dir = glob.glob(os.path.join(temp_dir, "eigen*"))[0]

    __np__.install_dep_include("eigen", os.path.join(src_dir, "Eigen", "*"), base_dir=src_dir)
