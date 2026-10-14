#!/bin/sh
set -eu
if [ "$(uname -s)" != Linux ]; then
  echo 'Build inside a dedicated Debian 13 ARM64 VM, not macOS.' >&2
  exit 1
fi
. /etc/os-release
if [ "${ID:-}" != debian ] || [ "${VERSION_ID:-}" != 13 ] || [ "$(dpkg --print-architecture)" != arm64 ]; then
  echo 'Expected a Debian 13 ARM64 build VM.' >&2
  exit 1
fi
if [ "$(id -u)" -ne 0 ]; then
  echo 'Run with sudo inside the dedicated build VM.' >&2
  exit 1
fi
command -v lb >/dev/null || { echo 'Install live-build first; see docs/BUILD.md.' >&2; exit 1; }
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"
# Each attempt uses its own directory, preserving failed builds and logs.
mkdir -p build
build_dir=$(mktemp -d "$project_dir/build/attempt.XXXXXX")
cp -R auto config "$build_dir/"
cd "$build_dir"
echo "Build directory: $build_dir"
if ! lb config > configure.log 2>&1; then
  cat configure.log >&2
  exit 1
fi
if ! lb build > build.log 2>&1; then
  tail -n 80 build.log >&2
  echo "Full build log: $build_dir/build.log" >&2
  exit 1
fi
set -- ./*.iso
[ -f "$1" ] || { echo 'Build returned without an ISO.' >&2; exit 1; }
sha256sum ./*.iso > SHA256SUMS
dpkg-query -W live-build debootstrap > build-tool-versions.txt
printf 'ISO built, but not boot-tested. Output: %s\n' "$build_dir"
