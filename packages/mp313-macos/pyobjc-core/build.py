import __mp__
import glob
import shutil
import sys
import os
import platform
import setuptools.build_meta


def run(wheel_directory):
    if platform.machine() == "arm64":
        __mp__.run_with_output("patch", "--binary", "-p1", "-i",
                                os.path.join(os.path.dirname(__file__), "Static_arm64.patch"))
    else:
        __mp__.run_with_output("patch", "--binary", "-p1", "-i",
                                os.path.join(os.path.dirname(__file__), "Static_x86_64.patch"))

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"

    __mp__.run_with_output(sys.executable, "setup.py", "bdist_wheel")

    wheel_location = glob.glob(os.path.join("dist", "pyobjc_core-*.whl"))[0]
    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
