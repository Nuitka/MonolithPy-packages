import __mp__
import glob
import shutil
import sys
import os
import platform
import setuptools.build_meta


def run(wheel_directory):
    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"

    shutil.copyfile(os.path.join(os.path.dirname(__file__), "core.py"), "certifi/core.py")
    os.remove("certifi/cacert.pem")

    __mp__.run_with_output(sys.executable, "-m", "pip", "wheel", ".", "-v")

    wheel_location = glob.glob("certifi-*.whl")[0]
    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
