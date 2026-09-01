import __mp__
import glob
import shutil
import sys
import os
from tempfile import TemporaryDirectory

import setuptools.build_meta
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    # statsmodels 0.15.0 switched from a setuptools build to the meson-python
    # backend, which needs ninja (and cmake for meson's dependency probes) on
    # PATH. Unlike the Windows recipe, macOS needs no /FORCE cython wrapper: the
    # linker resolves extension symbols with -undefined dynamic_lookup, so
    # meson's cython sanity-check links cleanly. statsmodels has no Fortran and
    # links no BLAS at build time (its meson.build only does a `cy.compiles`
    # probe of scipy.linalg.cython_blas), so scipy's Fortran/openblas setup is
    # intentionally omitted.
    __mp__.run_with_output("patch", "-t", "-p1", "-i",
                           os.path.join(os.path.dirname(__file__), "statsmodels-static-patch.patch"))

    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "10.13"
    os.environ["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("cmake", "cmake")) + os.pathsep +
                          os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep +
                          os.environ["PATH"])
    os.environ["PKG_CONFIG"] = "/disabled"

    job_args = []
    if "MP_JOBS" in os.environ:
        job_args += ["-Ccompile-args=-j" + os.environ["MP_JOBS"]]
    __mp__.run(sys.executable, "-m", "build", "-w", "--no-isolation",
               "-Cbuild-dir=build", *job_args)

    wheel_location = glob.glob(os.path.join("dist", "statsmodels-*.whl"))[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        __mp__.analyze_and_rename_library_symbols(tmpdir, "statsmodels")
        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
