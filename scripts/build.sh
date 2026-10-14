#!/bin/sh
# Almond Linux guarded build wrapper.
# Status: Implemented (source exists, untested). It has never produced an ISO.
#
# Run it inside a dedicated Debian 13 build machine (a VM is fine) whose own
# architecture matches ALMOND_ARCH. Usage, from the repository:
#   sudo ./scripts/build.sh                      # AALDM, amd64 (default)
#   sudo ALMOND_ARCH=arm64 ./scripts/build.sh    # arm64 dev variant
# Settings are explained in auto/config and docs/BUILD.md.
set -eu

# --- Host guard: refuse before creating anything. -------------------------
if [ "$(uname -s)" != Linux ]; then
  echo 'Refusing to build: run this inside a dedicated Debian 13 build machine, not on macOS or another OS.' >&2
  exit 1
fi

edition=${ALMOND_EDITION:-aaldm}
arch=${ALMOND_ARCH:-amd64}
firmware=${ALMOND_FIRMWARE:-listed}
case "$edition" in
  aaldm) ;;
  *) echo "Refusing to build: ALMOND_EDITION must be aaldm (AALLDM is not defined yet), not '$edition'." >&2; exit 1 ;;
esac
case "$arch" in
  amd64|arm64) ;;
  *) echo "Refusing to build: ALMOND_ARCH must be amd64 or arm64, not '$arch'." >&2; exit 1 ;;
esac
case "$firmware" in
  listed|all) ;;
  *) echo "Refusing to build: ALMOND_FIRMWARE must be listed or all, not '$firmware'." >&2; exit 1 ;;
esac

if [ ! -r /etc/os-release ]; then
  echo 'Refusing to build: /etc/os-release is missing; expected Debian 13.' >&2
  exit 1
fi
. /etc/os-release
if [ "${ID:-}" != debian ] || [ "${VERSION_ID:-}" != 13 ]; then
  echo "Refusing to build: expected Debian 13 (trixie), found ${PRETTY_NAME:-unknown}." >&2
  exit 1
fi
host_arch=$(dpkg --print-architecture)
if [ "$host_arch" != "$arch" ]; then
  echo "Refusing to build: this host is $host_arch but ALMOND_ARCH is $arch." >&2
  echo 'Only native builds are supported for now (cross-building is future work; see docs/BUILD.md).' >&2
  exit 1
fi
if [ "$(id -u)" -ne 0 ]; then
  echo 'Refusing to build: run with sudo inside the dedicated build machine (live-build needs root for mounts and chroots).' >&2
  exit 1
fi
command -v lb >/dev/null || { echo 'Refusing to build: install live-build first; see docs/BUILD.md.' >&2; exit 1; }

export ALMOND_EDITION="$edition" ALMOND_ARCH="$arch" ALMOND_FIRMWARE="$firmware"

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"

# --- Fresh attempt directory: failed builds and logs are kept. -------------
mkdir -p build
build_dir=$(mktemp -d "$project_dir/build/attempt.XXXXXX")
cp -R auto config "$build_dir/"
echo "Build directory: $build_dir"

# --- Stage Almond assets into the attempt's config. -----------------------
# Missing sources are warnings, not errors: the assets are developed in
# parallel and the image must still build without them.
inc=$build_dir/config/includes.chroot
boot=$build_dir/config/bootloaders
staged=0
missing=0
warn() {
  echo "warning: $*" >&2
  missing=$((missing + 1))
}
note() {
  echo "staged: $*"
  staged=$((staged + 1))
}
# Copy the directories found directly inside $1 into $2 (themes and similar).
stage_subdirs() {
  found=0
  if [ -d "$1" ]; then
    for item in "$1"/*; do
      if [ -d "$item" ]; then
        mkdir -p "$2"
        cp -RP "$item" "$2/"
        note "$item -> ${2#"$inc"}"
        found=1
      fi
    done
  fi
  [ "$found" -eq 1 ] || warn "nothing to stage from $1"
}
# Copy the files matching the shell patterns $3... found directly inside $1 into $2.
stage_files() {
  src=$1
  dest=$2
  shift 2
  found=0
  if [ -d "$src" ]; then
    for pattern in "$@"; do
      for item in "$src"/$pattern; do
        if [ -f "$item" ]; then
          mkdir -p "$dest"
          cp -P "$item" "$dest/"
          note "$item -> ${dest#"$inc"}"
          found=1
        fi
      done
    done
  fi
  [ "$found" -eq 1 ] || warn "nothing to stage from $src ($*)"
}
# Copy one file $1 to the full target path $2 with mode $3.
stage_one() {
  if [ -f "$1" ]; then
    mkdir -p "$(dirname -- "$2")"
    cp "$1" "$2"
    chmod "$3" "$2"
    note "$1 -> ${2#"$build_dir"/}"
  else
    warn "missing $1"
  fi
}

stage_subdirs desktop/icons "$inc/usr/share/icons"
stage_subdirs desktop/openbox "$inc/usr/share/themes"
stage_one desktop/launcher/almond-launch "$inc/usr/bin/almond-launch" 0755
stage_files desktop/launcher "$inc/usr/share/almond/launcher" '*.rasi' '*.example'
stage_one desktop/launcher/almond-launch.desktop "$inc/usr/share/applications/almond-launch.desktop" 0644
# Launcher helpers (almond-launch-power, almond-launch-recent, ...): almond-launch
# looks for them in /usr/libexec/almond.
for item in desktop/launcher/almond-launch-*; do
  [ -f "$item" ] || continue
  name=$(basename -- "$item")
  case "$name" in
    *.rasi|*.desktop|*.example|*.md) continue ;;
  esac
  stage_one "$item" "$inc/usr/libexec/almond/$name" 0755
done
# Super key for the launcher. Not staged to /etc/xdg/lxqt/: Debian 13's
# lxqt-globalkeys installs /etc/xdg/lxqt/globalkeyshortcuts.conf as a
# directory, so a file there would collide with the package. The 0200 hook
# merges this file with Debian's defaults into a plain file at that path.
# Staged before desktop/defaults so a copy there takes precedence (see below).
keys_src=desktop/lxqt/globalkeyshortcuts.conf
keys_dest=$inc/usr/share/almond/lxqt/globalkeyshortcuts.conf
if [ -f "$keys_src" ]; then
  stage_one "$keys_src" "$keys_dest" 0644
elif [ ! -f desktop/defaults/etc/xdg/lxqt/globalkeyshortcuts.conf ]; then
  warn 'no globalkeyshortcuts.conf: the Super key will not open the launcher'
fi
stage_files desktop/wallpapers "$inc/usr/share/backgrounds/almond" '*.png' '*.jpg' '*.jpeg' '*.svg' '*.webp'
# desktop/defaults is an overlay of the root filesystem (etc/, usr/).
for top in etc usr; do
  if [ -d "desktop/defaults/$top" ]; then
    mkdir -p "$inc/$top"
    cp -RP "desktop/defaults/$top/." "$inc/$top/"
    note "desktop/defaults/$top -> /$top"
  elif [ "$top" = etc ]; then
    warn 'missing desktop/defaults/etc'
  fi
done
# A globalkeyshortcuts.conf in desktop/defaults would land on the path that
# Debian ships as a directory; move it to where the 0200 hook reads it.
staged_keys=$inc/etc/xdg/lxqt/globalkeyshortcuts.conf
if [ -f "$staged_keys" ] && [ ! -L "$staged_keys" ]; then
  mkdir -p "$(dirname -- "$keys_dest")"
  rm -f "$keys_dest"
  mv "$staged_keys" "$keys_dest"
  note "desktop/defaults/etc/xdg/lxqt/globalkeyshortcuts.conf -> ${keys_dest#"$inc"} (wins over $keys_src)"
elif [ -e "$staged_keys" ] || [ -L "$staged_keys" ]; then
  rm -rf "$staged_keys"
  warn 'desktop/defaults/etc/xdg/lxqt/globalkeyshortcuts.conf is not a regular file; not staged'
fi
stage_subdirs desktop/lxqt/themes "$inc/usr/share/lxqt/themes"
stage_files desktop/lxqt/palettes "$inc/usr/share/lxqt/palettes" '*'
stage_one desktop/gtk/settings.ini "$inc/etc/gtk-3.0/settings.ini" 0644
# Plymouth theme files are staged for later; AALDM does not install plymouth
# (see docs/AALDM-PLAN.md), so the 0200 hook leaves them unused.
if [ -d branding/boot/plymouth/almond ]; then
  mkdir -p "$inc/usr/share/plymouth/themes"
  cp -RP branding/boot/plymouth/almond "$inc/usr/share/plymouth/themes/"
  note 'branding/boot/plymouth/almond -> /usr/share/plymouth/themes/almond'
else
  warn 'missing branding/boot/plymouth/almond'
fi
# Logo PNGs as /usr/share/pixmaps/almond-*.png.
if [ -d branding/logo/png ]; then
  for item in branding/logo/png/*.png; do
    [ -f "$item" ] || continue
    name=$(basename -- "$item")
    case "$name" in
      almond-*) ;;
      *) name="almond-$name" ;;
    esac
    stage_one "$item" "$inc/usr/share/pixmaps/$name" 0644
  done
else
  warn 'missing branding/logo/png'
fi
# The memory report script, so a booted image can measure itself.
stage_one tests/measure-memory.sh "$inc/usr/share/almond/tests/measure-memory.sh" 0755
# Boot menu backgrounds. live-build copies config/bootloaders/<name>/ over its
# own templates, and only renders its default (Debian) splash when no
# splash.png is present. isolinux/ = legacy BIOS menu (640x480),
# grub-pc/ = GRUB menu, also used for UEFI.
if [ "$arch" = amd64 ]; then
  stage_one branding/boot/isolinux-splash.png "$boot/isolinux/splash.png" 0644
fi
if [ -f branding/boot/grub-background.png ]; then
  stage_one branding/boot/grub-background.png "$boot/grub-pc/splash.png" 0644
elif [ -f branding/boot/isolinux-splash.png ]; then
  stage_one branding/boot/isolinux-splash.png "$boot/grub-pc/splash.png" 0644
else
  warn 'no GRUB background; live-build will use its default splash'
fi

# Normalise what was staged: root-owned, no macOS or documentation files,
# files 0644 unless they were executable (then 0755), directories 0755.
if [ -d "$inc" ]; then
  find "$inc" \( -name .DS_Store -o -name '*.md' \) -type f -exec rm -f {} +
  find "$inc" -type d -exec chmod 0755 {} +
  find "$inc" -type f -perm -u+x -exec chmod 0755 {} +
  find "$inc" -type f ! -perm -u+x -exec chmod 0644 {} +
  chown -R 0:0 "$inc"
fi
[ -d "$boot" ] && chown -R 0:0 "$boot"
echo "Staging: $staged item(s) staged, $missing warning(s)."

# --- Record what this attempt was built from. -----------------------------
{
  echo "date_utc=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  echo "ALMOND_EDITION=$edition"
  echo "ALMOND_ARCH=$arch"
  echo "ALMOND_FIRMWARE=$firmware"
  echo "host=$(uname -srm)"
  echo "host_debian_version=$(cat /etc/debian_version 2>/dev/null || echo unknown)"
  if command -v git >/dev/null 2>&1 && git -C "$project_dir" rev-parse HEAD >/dev/null 2>&1; then
    echo "git_commit=$(git -C "$project_dir" rev-parse HEAD)"
    if [ -n "$(git -C "$project_dir" status --porcelain 2>/dev/null)" ]; then
      echo 'git_worktree=modified (uncommitted changes were built)'
    else
      echo 'git_worktree=clean'
    fi
  else
    echo 'git_commit=unknown'
  fi
} > "$build_dir/build-settings.txt"
dpkg-query -W live-build debootstrap > "$build_dir/build-tool-versions.txt"

# --- Build. ----------------------------------------------------------------
cd "$build_dir"
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

# Package manifest: live-build writes live-image-<arch>.packages
# (dpkg-query -W of the live filesystem). Keep a copy under a fixed name.
manifest=
for item in ./*.packages; do
  if [ -f "$item" ]; then
    manifest=$item
    break
  fi
done
if [ -z "$manifest" ] && [ -f chroot.packages.live ]; then
  manifest=chroot.packages.live
fi
if [ -n "$manifest" ]; then
  cp "$manifest" package-manifest.txt
else
  echo 'warning: no package manifest found' >&2
fi
if [ -f package-manifest.txt ]; then
  sha256sum ./*.iso package-manifest.txt > SHA256SUMS
else
  sha256sum ./*.iso > SHA256SUMS
fi
printf 'ISO built, but not boot-tested. Output: %s\n' "$build_dir"
