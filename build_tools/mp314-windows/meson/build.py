import __mp__
import os

from wheel.wheelfile import WheelFile


MESON_VERSION = "1.11.1"
MESON_PYZ_URL = (
    "https://github.com/mesonbuild/meson/releases/download/"
    "{0}/meson.pyz".format(MESON_VERSION)
)


def run(wheel_directory):
    # meson ships a self-contained zipapp (meson.pyz) that runs on any platform
    # via `python meson.pyz ...`. Ship it verbatim; consumers invoke it as
    #   run_with_output(sys.executable, find_build_tool_exe("meson", "meson.pyz"), ...)
    __mp__.download_file(MESON_PYZ_URL, os.getcwd())

    result_wheel = os.path.join(wheel_directory, __mp__.get_wheel_name("mpy-tool-meson", MESON_VERSION))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-tool-meson", MESON_VERSION)
        __mp__.add_wheel_build_tool(w, "meson", os.path.join(os.getcwd(), "meson.pyz"))

    return result_wheel
