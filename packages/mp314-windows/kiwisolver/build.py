import __mp__
import glob
import shutil
import sys
import os
import setuptools.build_meta
from tempfile import TemporaryDirectory
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    __mp__.setup_compiler_env()

    __mp__.run_build_tool_exe("patch", "patch.exe", "-t", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "kiwisolver-static-patch.patch"))

    __mp__.run_with_output(sys.executable, "-m", "build", "-w", "--no-isolation", "-o", ".")

    wheel_location = glob.glob("kiwisolver-*.whl")[0]

    # Isolate kiwisolver's symbols (it is a pybind11 extension) so its C++ /
    # pybind11 definitions don't collide with other extensions' under the
    # monolithic interpreter's /FORCE:MULTIPLE relink. Matches contourpy/scipy/
    # sklearn; kiwisolver previously shipped its symbols un-renamed.
    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        __mp__.analyze_and_rename_library_symbols(tmpdir, "kiwisolver")
        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
