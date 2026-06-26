import __mp__
import glob
import os
import platform
import shutil
import subprocess
import sysconfig
import tempfile

from wheel.wheelfile import WheelFile


SHEENBIDI_VERSION = "3.0.0"
SHEENBIDI_URL = (
    "https://github.com/Tehreer/SheenBidi/archive/refs/tags/"
    "v{0}/sheenbidi-{0}.tar.gz".format(SHEENBIDI_VERSION)
)

LIBRAQM_VERSION = "0.10.5"


def _platform_args():
    if platform.machine() == "arm64":
        return ["-arch", "arm64", "-mmacosx-version-min=11.0"]
    return ["-arch", "x86_64", "-mmacosx-version-min=10.13"]


def _build_sheenbidi(work_dir, env):
    """Build SheenBidi as a static library; return its install prefix."""
    src_root = os.path.join(work_dir, "sheenbidi-src")
    os.makedirs(src_root, exist_ok=True)
    __mp__.download_extract(SHEENBIDI_URL, src_root)
    entries = [e for e in os.listdir(src_root) if not e.startswith(".")]
    src_dir = os.path.join(src_root, entries[0])

    build_dir = os.path.join(work_dir, "sheenbidi-build")
    os.makedirs(build_dir)
    install_dir = os.path.join(work_dir, "sheenbidi-install")
    os.makedirs(install_dir)

    if platform.machine() == "arm64":
        cmake_arch_args = ["-DCMAKE_OSX_ARCHITECTURES=arm64",
                           "-DCMAKE_OSX_DEPLOYMENT_TARGET=11.0"]
    else:
        cmake_arch_args = ["-DCMAKE_OSX_ARCHITECTURES=x86_64",
                           "-DCMAKE_OSX_DEPLOYMENT_TARGET=10.13"]

    __mp__.run_build_tool_exe(
        "cmake", "cmake",
        "-G", "Ninja",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_INSTALL_PREFIX=" + install_dir,
        "-DBUILD_SHARED_LIBS=OFF",
        "-DSB_CONFIG_UNITY=ON",
        "-DBUILD_TESTING=OFF",
        "-DBUILD_GENERATOR=OFF",
        *cmake_arch_args,
        src_dir,
        cwd=build_dir, env=env,
    )
    __mp__.run_build_tool_exe("ninja", "ninja", cwd=build_dir, env=env)
    __mp__.run_build_tool_exe("ninja", "ninja", "install", cwd=build_dir, env=env)
    return install_dir


def _build_libraqm(work_dir, src_dir, sheenbidi_prefix, env):
    """Compile libraqm directly with clang into libraqm.a. Returns its install prefix."""
    install_dir = os.path.join(work_dir, "libraqm-install")
    include_dir = os.path.join(install_dir, "include")
    lib_dir = os.path.join(install_dir, "lib")
    os.makedirs(include_dir)
    os.makedirs(lib_dir)

    major, minor, micro = LIBRAQM_VERSION.split(".")

    raqm_version_h = os.path.join(src_dir, "src", "raqm-version.h.in")
    with open(raqm_version_h) as f:
        version_h_content = f.read()
    version_h_content = (
        version_h_content
        .replace("@RAQM_VERSION_MAJOR@", major)
        .replace("@RAQM_VERSION_MINOR@", minor)
        .replace("@RAQM_VERSION_MICRO@", micro)
        .replace("@RAQM_VERSION@", LIBRAQM_VERSION)
    )
    with open(os.path.join(include_dir, "raqm-version.h"), "w") as f:
        f.write(version_h_content)

    config_h = os.path.join(src_dir, "src", "config.h")
    with open(config_h, "w") as f:
        f.write("#ifndef RAQM_CONFIG_H\n#define RAQM_CONFIG_H\n#define RAQM_SHEENBIDI 1\n#endif\n")

    base_root = __mp__.find_dep_root("base")
    raqm_c = os.path.join(src_dir, "src", "raqm.c")
    raqm_o = os.path.join(work_dir, "raqm.o")

    cc = (sysconfig.get_config_var("CC") or "clang").split()[0]
    sdk_path = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    subprocess.check_call([
        cc,
        "-c",
        "-O2",
        "-fPIC",
        "-std=gnu99",
        "-DHAVE_CONFIG_H",
        "-DRAQM_SHEENBIDI_GT_2_9",
        "-isysroot", sdk_path,
        "-I" + os.path.join(src_dir, "src"),
        "-I" + include_dir,
        "-I" + os.path.join(base_root, "include"),
        "-I" + os.path.join(base_root, "include", "freetype2"),
        "-I" + os.path.join(base_root, "include", "harfbuzz"),
        "-I" + os.path.join(sheenbidi_prefix, "include"),
        *_platform_args(),
        raqm_c,
        "-o", raqm_o,
    ], env=env)

    libraqm_a = os.path.join(lib_dir, "libraqm.a")
    subprocess.check_call(["ar", "rcs", libraqm_a, raqm_o], env=env)
    subprocess.check_call(["ranlib", libraqm_a], env=env)

    shutil.copy(os.path.join(src_dir, "src", "raqm.h"), include_dir)

    sb_lib_candidates = glob.glob(os.path.join(sheenbidi_prefix, "lib", "lib[Ss]heen[Bb]idi*.a"))
    if not sb_lib_candidates:
        raise RuntimeError("Could not locate built SheenBidi static library")
    shutil.copy(sb_lib_candidates[0], os.path.join(lib_dir, "libsheenbidi.a"))

    sb_include_src = os.path.join(sheenbidi_prefix, "include")
    for root, dirs, files in os.walk(sb_include_src):
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), sb_include_src)
            dst = os.path.join(include_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(os.path.join(root, name), dst)

    return install_dir


def run(wheel_directory):
    src_dir = os.getcwd()

    env = os.environ.copy()
    env["MACOSX_DEPLOYMENT_TARGET"] = "10.13" if platform.machine() != "arm64" else "11.0"
    env["PATH"] = (
        os.path.dirname(__mp__.find_build_tool_exe("cmake", "cmake")) + os.pathsep +
        os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep +
        os.path.dirname(__mp__.find_build_tool_exe("clang", "clang")) + os.pathsep +
        env.get("PATH", "")
    )
    env["PKG_CONFIG"] = "/disabled"

    work_dir = tempfile.mkdtemp(prefix="mpy-libraqm-")

    sheenbidi_prefix = _build_sheenbidi(work_dir, env)
    install_dir = _build_libraqm(work_dir, src_dir, sheenbidi_prefix, env)

    result_wheel = os.path.join(
        wheel_directory,
        __mp__.get_wheel_name("mpy_dep_libraqm", LIBRAQM_VERSION),
    )
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-libraqm", LIBRAQM_VERSION)
        __mp__.add_wheel_dep_libs(
            w, "libraqm",
            os.path.join(install_dir, "lib", "*"),
            base_dir=os.path.join(install_dir, "lib"),
        )
        __mp__.add_wheel_dep_include(
            w, "libraqm",
            os.path.join(install_dir, "include", "*"),
            base_dir=os.path.join(install_dir, "include"),
        )

    return result_wheel
