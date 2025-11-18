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

    build_dir = os.getcwd()

    __np__.run_build_tool_exe("patch", "patch.exe", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "numpy-static-patch.patch"))

    __np__.patch_all_source(build_dir)

    __np__.filter_paths_containing("gfortran.exe")
    env = os.environ.copy()
    job_args = []
    if "NP_JOBS" in env:
        job_args += ["-Ccompile-args=-j" + env["NP_JOBS"]]
    env["PEP517_BACKEND_PATH"] = os.pathsep.join([x for x in sys.path if not x.endswith(os.path.sep + "site")])
    env["PATH"] = os.path.dirname(__np__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + env["PATH"]
    env["LIB"] = env["LIB"] + os.pathsep + __np__.find_dep_libs("openblas")
    env["INCLUDE"] = env["INCLUDE"] + os.pathsep + __np__.find_dep_include("openblas")
    __np__.run(sys.executable, "-m", "build", "-w", "--no-isolation",
               "-Csetup-args=-Dblas=openblas", "-Csetup-args=-Dlapack=openblas", *job_args, env=env)

    wheel_location = glob.glob(os.path.join("dist", "numpy-*.whl"))[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)

        os.chdir(tmpdir)
        __np__.run_build_tool_exe("patch", "patch.exe", "-p1", "-i",
                                  os.path.join(os.path.dirname(__file__), "numpy-post.patch"))
        os.chdir(build_dir)

        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
