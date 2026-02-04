import __mp__
import glob
import shutil
import sys
import os
import setuptools.build_meta


def run(wheel_directory):
    __mp__.setup_compiler_env()

    os.environ["LXML_STATIC_INCLUDE_DIRS"] = os.pathsep.join([
        __mp__.find_dep_include("iconv"),
        __mp__.find_dep_include("libxml2"),
        __mp__.find_dep_include("libxslt")
    ])

    os.environ["LXML_STATIC_LIBRARY_DIRS"] = os.pathsep.join([
        __mp__.find_dep_libs("iconv"),
        __mp__.find_dep_libs("libxml2"),
        __mp__.find_dep_libs("libxslt"),
        __mp__.find_dep_libs("zlib")
    ])

    __mp__.run_with_output(sys.executable, "setup.py", "bdist_wheel", "--static")

    wheel_location = glob.glob(os.path.join("dist", "lxml-*.whl"))[0]
    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
