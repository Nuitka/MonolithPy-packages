import __mp__
import os
import sysconfig


def run(temp_dir: str):
    __mp__.download_extract("https://download.gnome.org/sources/libxml2/2.9/libxml2-2.9.13.tar.xz", temp_dir)

    os.chdir(os.path.join(temp_dir, "libxml2-2.9.13"))

    __mp__.run_with_output("/bin/bash",
                           "configure",
                           f"CC={sysconfig.get_config_var('CC')}",
                           f"CXX={sysconfig.get_config_var('CXX')}",
                           "--prefix=" + __mp__.find_dep_root("libxml2"),
                           "--with-libiconv-prefix=" + __mp__.find_dep_root("iconv"),
                           "--disable-shared")

    __mp__.run_with_output("make", f"-j{__mp__.get_num_jobs()}")
    __mp__.run_with_output("make", "install")
