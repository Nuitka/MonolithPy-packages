#!/bin/sh
# verify-min-macos.sh MAX_MAJOR DIR...
#
# Assert that every Mach-O slice under the given paths -- objects (.o), static
# archive members (.a), shared objects (.so/.dylib/.bundle) and executables --
# declares a macOS minimum version whose MAJOR is strictly LESS than MAX_MAJOR.
#
# MonolithPy packages are compiled to relocatable .o / .a and linked into the
# monolithic interpreter at install time, so a package object that inherited the
# (high) build runner's OS as its deployment target would silently raise the
# minimum macOS of everything it is linked into. This gate catches that at the
# per-object level, where the leak actually is, before it is baked into a binary
# whose own LC_BUILD_VERSION the linker rewrites to the interpreter's target.
#
# The min version is read from LC_BUILD_VERSION (minos) and, for very old
# targets, the legacy LC_VERSION_MIN_MACOSX (version). All arches of a universal
# file are inspected in a single `otool -arch all -l` pass; non-macOS platform
# load commands (iOS, catalyst, simulators) are ignored.
set -eu

if [ "$#" -lt 2 ]; then
  echo "usage: verify-min-macos.sh MAX_MAJOR DIR..." >&2
  exit 2
fi
max_major="$1"; shift

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
scanned=0

for root in "$@"; do
  [ -e "$root" ] || continue
  while IFS= read -r f; do
    case "$(file -b "$f" 2>/dev/null)" in
      *Mach-O*|*"current ar archive"*|*"ar archive"*) ;;
      *) continue ;;
    esac
    scanned=$((scanned + 1))
    # Emit every minos / legacy version_min this file declares (one line per
    # LC_BUILD_VERSION / LC_VERSION_MIN_MACOSX, across all arches and, for an
    # archive, all members). MonolithPy macOS artifacts are macOS-platform only,
    # so no platform filter is applied (matching the proven texKit check).
    otool -arch all -l "$f" 2>/dev/null | awk '
      /^ *cmd LC_BUILD_VERSION/      {bv=1; next}
      bv && /^ *minos/               {print $2; bv=0; next}
      /^ *cmd LC_VERSION_MIN_MACOSX/ {vm=1; next}
      vm && /^ *version/             {print $2; vm=0; next}
    ' | while IFS= read -r v; do
      [ -n "$v" ] || continue
      maj="${v%%.*}"
      case "$maj" in ''|*[!0-9]*) continue ;; esac
      if [ "$maj" -ge "$max_major" ]; then
        printf '%s min-macos=%s\n' "$f" "$v" >> "$tmp"
      fi
    done
  done <<EOF
$(find "$root" -type f \( -perm -u+x -o -name '*.dylib' -o -name '*.a' -o -name '*.so' -o -name '*.bundle' -o -name '*.o' \) 2>/dev/null)
EOF
done

if [ -s "$tmp" ]; then
  echo "verify-min-macos: FAIL -- Mach-O with min macOS >= $max_major (must be lower):" >&2
  sort -u "$tmp" | sed 's/^/    /' >&2
  exit 1
fi

echo "verify-min-macos: OK -- all Mach-O under [$*] target macOS < $max_major ($scanned files scanned)"
