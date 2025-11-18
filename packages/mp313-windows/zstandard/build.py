import __np__
import glob
import shutil
import sys
import os


def run(wheel_directory):
    __np__.setup_compiler_env()

    # C backend conflicts with existing cpython _zstd module
    __np__.run_with_output(sys.executable, "setup.py", "bdist_wheel", "--no-c-backend")

    wheel_location = glob.glob(os.path.join("dist", "zstandard-*.whl"))[0]
    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
