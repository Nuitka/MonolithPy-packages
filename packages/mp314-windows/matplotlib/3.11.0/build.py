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
    __mp__.setup_compiler_env()

    __mp__.run_build_tool_exe("patch", "patch.exe", "-t", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "matplotlib-static-patch.patch"))

    __mp__.patch_all_source(os.getcwd())

    # Relax meson-python upper bound so builds work with newer installed versions
    import re
    pyproject_path = os.path.join(os.getcwd(), "pyproject.toml")
    with open(pyproject_path, "r") as f:
        content = f.read()
    content = re.sub(r'"meson-python[^"]*"', '"meson-python>=0.13.1"', content)
    with open(pyproject_path, "w") as f:
        f.write(content)

    os.environ["CMAKE_PREFIX_PATH"] = __mp__.find_dep_root("freetype")
    os.environ["INCLUDE"] = os.environ["INCLUDE"] + os.pathsep + sysconfig.get_config_var("INCLUDEPY")

    raqm_root = __mp__.find_dep_root("raqm")

    os.environ["PATH"] = (
        os.path.dirname(__mp__.find_build_tool_exe("cmake", "cmake.exe")) + os.pathsep +
        os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep +
        os.path.dirname(__mp__.find_build_tool_exe("mingw", "objdump.exe")) + os.pathsep +
        os.environ["PATH"]
    )

    # Disable LTO on windows because MSVC is terrible.
    # -Db_lto=false only flips meson's own LTO knob; matplotlib's
    # meson.build still leaks /GL into the cl command line for some
    # extensions, which embeds LTCG IR tied to the building cl's
    # micro-version and trips C1047 at the final relink. Append "/GL-"
    # via CFLAGS / CXXFLAGS (meson appends both to each compile argv
    # last-wins, beating any earlier /GL) -- using the cl env var _CL_
    # instead would bypass argv and break ccache.
    os.environ["CFLAGS"]   = (os.environ.get("CFLAGS",   "") + " /GL-").strip()
    os.environ["CXXFLAGS"] = (os.environ.get("CXXFLAGS", "") + " /GL-").strip()
    job_args = ["-Csetup-args=-Db_lto=false"]
    if "MP_JOBS" in os.environ:
        job_args += ["-Ccompile-args=-j" + os.environ["MP_JOBS"]]
    __mp__.run_with_output(sys.executable, "-m", "build", "-w", "--no-isolation", "-o", ".",
                           "-Csetup-args=-Dsystem-freetype=True",
                           "-Csetup-args=-Dsystem-libraqm=True",
                           "-Csetup-args=-Draqm-root=" + raqm_root,
                           *job_args)

    wheel_location = glob.glob("matplotlib-*.whl")[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")
        __mp__.rename_symbols_in_file(os.path.join(tmpdir, f"matplotlib\\_c_internal_utils{ext_suffix}"), "_matplotlib__c_internal_utils", [".*fflush.*"])
        __mp__.rename_symbols_in_file(os.path.join(tmpdir, f"matplotlib\\_image{ext_suffix}"), "_matplotlib__image", [".*fflush.*"])
        __mp__.rename_symbols_in_file(os.path.join(tmpdir, f"matplotlib\\_path{ext_suffix}"), "_matplotlib__path", [".*fflush.*"])
        __mp__.rename_symbols_in_file(os.path.join(tmpdir, f"matplotlib\\_qhull{ext_suffix}"), "_matplotlib__qhull", [".*fflush.*"])
        __mp__.rename_symbols_in_file(os.path.join(tmpdir, f"matplotlib\\_tri{ext_suffix}"), "_matplotlib__tri", [".*fflush.*"])
        __mp__.rename_symbols_in_file(os.path.join(tmpdir, f"matplotlib\\ft2font{ext_suffix}"), "_matplotlib_ft2font", [".*fflush.*"])
        __mp__.rename_symbols_in_file(os.path.join(tmpdir, f"matplotlib\\backends\\_backend_agg{ext_suffix}"), "_matplotlib__backend_agg", [".*fflush.*"])
        __mp__.rename_symbols_in_file(os.path.join(tmpdir, f"matplotlib\\backends\\_tkagg{ext_suffix}"), "_matplotlib__tkagg", [".*fflush.*"])
        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
