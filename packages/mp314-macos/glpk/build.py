import __mp__
import glob
import shutil
import sys
import os
import setuptools.build_meta


def run(wheel_directory):
    __mp__.run_with_output(sys.executable, "setup.py", "bdist_wheel", "--with-glpk=" + __mp__.find_dep_root("glpk"))

    wheel_location = glob.glob(os.path.join("dist", "glpk-*.whl"))[0]
    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
