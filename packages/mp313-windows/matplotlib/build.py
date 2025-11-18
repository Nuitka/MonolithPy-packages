import __np__
import glob
import shutil
import sys
import os
import sysconfig
import setuptools.build_meta
from tempfile import TemporaryDirectory

from wheel.wheelfile import WheelFile


def run(wheel_directory):
    __np__.setup_compiler_env()

    __np__.run_build_tool_exe("patch", "patch.exe", "-t", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "matplotlib-static-patch.patch"))

    __np__.patch_all_source(os.getcwd())

    os.environ["CMAKE_PREFIX_PATH"] = __np__.find_dep_root("freetype")
    os.environ["INCLUDE"] = os.environ["INCLUDE"] + os.pathsep + sysconfig.get_config_var("INCLUDEPY")

    job_args = []
    if "NP_JOBS" in os.environ:
        job_args += ["-Ccompile-args=-j" + os.environ["NP_JOBS"]]
    __np__.run_with_output(sys.executable, "-m", "build", "-w", "--no-isolation",
                           "-Csetup-args=-Dsystem-freetype=True", *job_args)

    wheel_location = glob.glob(os.path.join("dist", "matplotlib-*.whl"))[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        __np__.rename_symbols_in_file(os.path.join(tmpdir, "matplotlib\\_c_internal_utils.mp313-win_amd64.lib"), "matplotlib__c_internal_utils_", [".*fflush.*"])
        __np__.rename_symbols_in_file(os.path.join(tmpdir, "matplotlib\\_image.mp313-win_amd64.lib"), "matplotlib__image_", [".*fflush.*"])
        __np__.rename_symbols_in_file(os.path.join(tmpdir, "matplotlib\\_path.mp313-win_amd64.lib"), "matplotlib__path_", [".*fflush.*"])
        __np__.rename_symbols_in_file(os.path.join(tmpdir, "matplotlib\\_qhull.mp313-win_amd64.lib"), "matplotlib__qhull_", [".*fflush.*"])
        __np__.rename_symbols_in_file(os.path.join(tmpdir, "matplotlib\\_tri.mp313-win_amd64.lib"), "matplotlib__tri_", [".*fflush.*"])
        __np__.rename_symbols_in_file(os.path.join(tmpdir, "matplotlib\\ft2font.mp313-win_amd64.lib"), "matplotlib_ft2font_", [".*fflush.*"])
        __np__.rename_symbols_in_file(os.path.join(tmpdir, "matplotlib\\backends\\_backend_agg.mp313-win_amd64.lib"), "matplotlib__backend_agg_", [".*fflush.*"])
        __np__.rename_symbols_in_file(os.path.join(tmpdir, "matplotlib\\backends\\_tkagg.mp313-win_amd64.lib"), "matplotlib__tkagg_", [".*fflush.*"])
        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
