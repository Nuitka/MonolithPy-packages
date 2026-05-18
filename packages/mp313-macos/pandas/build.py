import __mp__
import glob
import shutil
import sys
import os
import sysconfig
import setuptools.build_meta
from tempfile import TemporaryDirectory
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    os.environ["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("cmake", "cmake")) + os.pathsep +
                   os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"])
    os.environ["PKG_CONFIG"] = "/disabled"

    job_args = []
    if "MP_JOBS" in os.environ:
        job_args += [f"-Ccompile-args=-j{os.environ['MP_JOBS']}"]
    __mp__.run(sys.executable, "-m", "build", "-w", "--no-isolation", *job_args)

    wheel_location = glob.glob(os.path.join("dist", "pandas-*.whl"))[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)

        __mp__.analyze_and_rename_library_symbols(tmpdir,
                                                  "pandas")

        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
