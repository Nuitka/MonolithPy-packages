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
    __mp__.run_build_tool_exe("patch", "-p1", "-ui",
                              os.path.join(os.path.dirname(__file__), "scikit_learn-static-patch.patch"))

    env = os.environ.copy()
    env["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    env["PEP517_BACKEND_PATH"] = os.pathsep.join([x for x in sys.path if not x.endswith(os.path.sep + "site")])
    env["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("cmake", "cmake")) + os.pathsep +
                   os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"])
    env["PKG_CONFIG"] = "/disabled"
    __mp__.run(sys.executable, "-m", "build", "-w", "--no-isolation", env=env)

    wheel_location = glob.glob(os.path.join("dist", "scikit_learn-*.whl"))[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        __mp__.rename_symbols_in_file(os.path.join(tmpdir, "sklearn/svm/_libsvm_sparse.nuitkapython-311-darwin.a"), "sklearn_svm__libsvm_sparse")
        __mp__.rename_symbols_in_file(os.path.join(tmpdir, "sklearn/svm/_libsvm.nuitkapython-311-darwin.a"), "sklearn_svm__libsvm")
        __mp__.rename_symbols_in_file(os.path.join(tmpdir, "sklearn/svm/_newrand.nuitkapython-311-darwin.a"), "sklearn_svm__newrand")
        __mp__.rename_symbols_in_file(os.path.join(tmpdir, "sklearn/svm/_liblinear.nuitkapython-311-darwin.a"), "sklearn_svm__liblinear")
        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
