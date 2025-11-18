import __np__
import shutil
import os


def run(temp_dir: str):
    __np__.download_extract("https://github.com/GNOME/libxslt/archive/refs/tags/v1.1.34.zip", temp_dir)

    os.chdir(os.path.join(temp_dir, "libxslt-1.1.34", "win32"))

    __np__.run_build_tool_exe("patch", "patch.exe", "--binary", "configure.js", os.path.join(temp_dir, "configure.js.patch"))

    __np__.run_compiler_exe(
        "cscript.exe", "configure.js",
        "compiler=msvc",
        "prefix=" + os.path.join(temp_dir, "install_tmp"),
        "cruntime=/MT",
        "include=" + __np__.find_dep_include("iconv") + ";" + __np__.find_dep_include("libxml2"),
        "lib=" + __np__.find_dep_libs("iconv") + ";" + __np__.find_dep_libs("libxml2"))

    __np__.setup_compiler_env()

    __np__.nmake("/f", "Makefile.msvc", "LIBS=iconv.lib Ws2_32.lib")
    __np__.nmake("/f", "Makefile.msvc", "install")

    shutil.copy(os.path.join(temp_dir, "install_tmp", "lib", "libxslt_a.lib"), os.path.join(temp_dir, "libxslt.lib"))
    shutil.copy(os.path.join(temp_dir, "install_tmp", "lib", "libxslt_a.lib"), os.path.join(temp_dir, "libxslt_a.lib"))
    shutil.copy(os.path.join(temp_dir, "install_tmp", "lib", "libexslt_a.lib"), os.path.join(temp_dir, "libexslt.lib"))
    shutil.copy(os.path.join(temp_dir, "install_tmp", "lib", "libexslt_a.lib"), os.path.join(temp_dir, "libexslt_a.lib"))

    __np__.prepend_to_file(os.path.join(temp_dir, "install_tmp", "include", "libxslt", "xsltexports.h"), "#define LIBXSLT_STATIC\n")
    __np__.prepend_to_file(os.path.join(temp_dir, "install_tmp", "include", "libexslt", "exsltexports.h"), "#define LIBEXSLT_STATIC\n")

    __np__.install_dep_libs("libxslt", os.path.join(temp_dir, "*.lib"))
    __np__.install_dep_include("libxslt", os.path.join(temp_dir, "install_tmp", "include", "*"))
