import __mp__
import glob
import shutil
import sys
import os
from tempfile import TemporaryDirectory

from wheel.wheelfile import WheelFile


def run(wheel_directory):
    __mp__.setup_compiler_env()

    __mp__.run(sys.executable, "-m", "pip", "wheel", ".", "-v", "--config-settings=\"--global-option=--system-zstd\"")

    wheel_location = glob.glob("zstandard-*.whl")[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        __mp__.analyze_and_rename_library_symbols(tmpdir, "zstandard",
                                                  protected_symbol_patterns=["fflush"])
        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                if os.path.exists(os.path.join(tmpdir, filename)):
                    wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
