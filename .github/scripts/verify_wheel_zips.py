"""Exit non-zero if any wheel under the given directory is not a readable zip.

Opening the archive reads its central directory, which sits at the end of the
file, so a download that stopped early fails here.
"""

import pathlib
import sys
import zipfile


def main(root):
    wheels = sorted(pathlib.Path(root).rglob("*.whl"))
    bad = []
    for wheel in wheels:
        try:
            with zipfile.ZipFile(wheel) as archive:
                archive.namelist()
        except (zipfile.BadZipFile, OSError) as error:
            bad.append(wheel)
            print(f"::warning::{wheel.name} ({wheel.stat().st_size} bytes) is not a readable zip: {error}")
    print(f"{len(wheels) - len(bad)}/{len(wheels)} wheels in {root} are readable")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
