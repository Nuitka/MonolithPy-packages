import __mp__
import glob
import shutil
import sys
import os


def run(wheel_directory):
    __mp__.run_with_output("patch", "--binary", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "cffi-static-patch.patch"))

    __mp__.run_with_output(sys.executable, "setup.py", "bdist_wheel")

    wheel_location = glob.glob(os.path.join("dist", "cffi-*.whl"))[0]
    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
