import __mp__
from typing import *

import os
import shutil
import glob


def run(temp_dir: str):
    __mp__.download_extract("https://bitbucket.org/odedevs/ode/get/0.16.2.tar.gz", temp_dir)

    src_dir = glob.glob(os.path.join(temp_dir, "ode*"))[0]

    build_dir = os.path.join(temp_dir, "build")
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    os.environ["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"]
    
    __mp__.run_build_tool_exe("cmake", "cmake", "-G", "Ninja",
                              "-DCMAKE_BUILD_TYPE=Release",
                              "-DBUILD_SHARED_LIBS=OFF", "-DODE_WITH_DEMOS=OFF", "-DODE_WITH_TESTS=OFF",
                              "-DODE_DOUBLE_PRECISION=OFF", src_dir)
    __mp__.run_build_tool_exe("ninja", "ninja")

    __mp__.install_dep_libs("ode", os.path.join(build_dir, "*.a"))
    __mp__.install_dep_include("ode", os.path.join(src_dir, "include", "ode", "*.h"), base_dir=os.path.join(src_dir, "include"))
    __mp__.install_dep_include("ode", os.path.join(build_dir, "include", "ode"))
