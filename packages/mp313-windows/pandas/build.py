import __np__
import glob
import shutil
import sys
import os
import setuptools.build_meta
from tempfile import TemporaryDirectory

from wheel.wheelfile import WheelFile


def run(wheel_directory):
    __np__.setup_compiler_env()

    __np__.run_build_tool_exe("patch", "patch.exe", "-p1", "-ui",
                              os.path.join(os.path.dirname(__file__), "pandas-static-patch.patch"))

    env = os.environ.copy()
    job_args = []
    if "NP_JOBS" in env:
        job_args += ["-Ccompile-args=-j" + env["NP_JOBS"]]
    __np__.run(sys.executable, "-m", "build", "-w", "--no-isolation", *job_args)

    wheel_location = glob.glob(os.path.join("dist", "pandas-*.whl"))[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        __np__.analyze_and_rename_library_symbols(tmpdir,
                                                  "pandas")
        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
