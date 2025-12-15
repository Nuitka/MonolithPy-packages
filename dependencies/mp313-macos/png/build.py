import __mp__
from typing import *

import os
import shutil
import glob
import sysconfig


def run(temp_dir: str):
    __mp__.download_extract("http://prdownloads.sourceforge.net/libpng/libpng-1.6.37.tar.xz?download", temp_dir)

    src_dir = glob.glob(os.path.join(temp_dir, "libpng*"))[0]

    prefix_dir = os.path.join(temp_dir, "prefix")
    os.mkdir(prefix_dir)
    os.chdir(src_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    os.environ["CFLAGS"] = sysconfig.get_config_var("CFLAGS")
    print("bash", os.path.join(src_dir, "configure"), "--disable-shared", "--with-zlib-prefix=" + __mp__.find_dep_root("zlib"))
    __mp__.run_with_output("bash", os.path.join(src_dir, "configure"), "--disable-shared", "--with-zlib-prefix=" + __mp__.find_dep_root("zlib"), "--prefix=" + prefix_dir)
    __mp__.run_with_output("sed", "-i", '', 's/#if PNG_ZLIB_VERNUM != 0 && PNG_ZLIB_VERNUM != ZLIB_VERNUM/#if 0/g', os.path.join(src_dir, "pngpriv.h"))
    __mp__.run_with_output("make")
    __mp__.run_with_output("make", "install")

    __mp__.install_dep_libs("png", os.path.join(prefix_dir, "lib", "*"))
    __mp__.install_dep_include("png", os.path.join(prefix_dir, "include", "*.h"), base_dir=os.path.join(prefix_dir, "include"))
