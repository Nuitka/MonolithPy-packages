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

    __mp__.run_with_output(sys.executable, "-m", "build", "-w", "--no-isolation", "-o", ".",
                           "-Csetup-args=-Db_lto=false")

    wheel_location = glob.glob("kiwisolver-*.whl")[0]

    # Isolate kiwisolver's symbols (it is a pybind11 extension) so its C++ /
    # pybind11 definitions don't collide with other extensions' under the
    # monolithic interpreter's relink. Matches contourpy/scipy/sklearn;
    # kiwisolver previously shipped its symbols un-renamed.
    #
    # Repack skips two things: (1) `*.orig` -- setuptools packages the build's
    # PyInit-rename backup (<lib>.orig) into the wheel; it is pure bloat, and
    # analyze_and_rename's own <lib>.orig backup is created+removed on top of it,
    # so replaying the original namelist for it would FileNotFound; and (2) the
    # stale RECORD -- WheelFile.close() regenerates an authoritative RECORD from
    # exactly what we write, so dropping the .orig stays consistent.
    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        __mp__.analyze_and_rename_library_symbols(tmpdir, "kiwisolver")
        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                src = os.path.join(tmpdir, filename)
                if filename.endswith(".orig") or os.path.basename(filename) == "RECORD" or not os.path.exists(src):
                    continue
                wf.write(src, filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
