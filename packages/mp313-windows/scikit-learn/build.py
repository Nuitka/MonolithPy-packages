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

    env = os.environ.copy()
    env["CFLAGS"] = "/DBYPASS_MP_EMBED"
    env["CXXFLAGS"] = "/DBYPASS_MP_EMBED"
    with TemporaryDirectory() as temp_dir:
        __mp__.run(sys.executable, "-m", "build", "-w", "--no-isolation", "-Ccompile-args=-j3", "-Cbuild-dir=" + temp_dir, env=env)

    wheel_location = glob.glob(os.path.join("dist", "scikit_learn-*.whl"))[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        __mp__.analyze_and_rename_library_symbols(tmpdir,
                                                  "scikit_learn",
                                                  symbol_mapping={
                                                      "set_seed": {"use_definition_from": "libliblinear-skl.lib"}
                                                  })
        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
