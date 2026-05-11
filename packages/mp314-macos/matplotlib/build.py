import __mp__
import glob
import re
import shutil
import sys
import os
import sysconfig
import setuptools.build_meta
from tempfile import TemporaryDirectory

from wheel.wheelfile import WheelFile


def run(wheel_directory):
    __mp__.run_with_output("patch", "-t", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "matplotlib-static-patch.patch"))

    __mp__.patch_all_source(os.getcwd())

    # Relax meson-python upper bound so builds work with newer installed versions
    pyproject_path = os.path.join(os.getcwd(), "pyproject.toml")
    with open(pyproject_path, "r") as f:
        content = f.read()
    content = re.sub(r'"meson-python[^"]*"', '"meson-python>=0.13.1"', content)
    with open(pyproject_path, "w") as f:
        f.write(content)

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    os.environ["CMAKE_PREFIX_PATH"] = __mp__.find_dep_root("freetype")
    os.environ["INCLUDE"] = sysconfig.get_config_var("INCLUDEPY")
    os.environ["CFLAGS"] = "-I" + sysconfig.get_config_var("INCLUDEPY")
    os.environ["CXXFLAGS"] = "-I" + sysconfig.get_config_var("INCLUDEPY")
    os.environ["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("cmake", "cmake")) + os.pathsep +
                   os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"])

    job_args = []
    if "MP_JOBS" in os.environ:
        job_args += ["-Ccompile-args=-j" + os.environ["MP_JOBS"]]
    __mp__.run_with_output(sys.executable, "-m", "build", "-w", "--no-isolation", "-o", ".",
                           "-Csetup-args=-Dsystem-freetype=True", *job_args)

    wheel_location = glob.glob("matplotlib-*.whl")[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        __mp__.analyze_and_rename_library_symbols(tmpdir,
                                                  "matplotlib")
        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
