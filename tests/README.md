# tests/

Checks and measurement tools for Almond Linux images.

| File | What it does | Status |
|---|---|---|
| `measure-memory.sh` | Prints a timestamped memory report of a running system: `/proc/meminfo`, used/available, zram, the top processes by PSS, PSS per AALDM component and the PSS total of the desktop session | Implemented (source exists, untested on Linux) |

## measure-memory.sh

POSIX `sh`, no extra packages: it only needs `awk`, `sort`, `head`, `date`, `uname` and `id`, which every Debian system has. `scripts/build.sh` also copies it into the image as `/usr/share/almond/tests/measure-memory.sh`.

```sh
sudo sh measure-memory.sh -w 120 > memory-boot1.txt
```

- `-w SECONDS` waits before measuring (the method waits 120 s after login).
- `-u USER` names the desktop session user. Default: the user who ran `sudo` (`SUDO_USER`), otherwise the owner of `lxqt-session`.
- `-n COUNT` sets the number of rows in the process table (default 25).

Run it as **root**. `/proc/<pid>/smaps_rollup` of other users' processes can only be read by root; without root the report says its process totals are incomplete. Processes that cannot be read, or that exit during the scan, are counted and reported instead of stopping the script. Kernel threads have no user memory and are only counted.

How to measure and how to read the numbers (why PSS and not RSS, why "used" is bigger than the PSS total): [docs/PERFORMANCE.md](../docs/PERFORMANCE.md).

### What has been checked

On 2026-10-14, on macOS (no Linux available): `sh -n` and `dash -n` pass, and the script was run with `dash` and the macOS `awk` against a synthetic `/proc` tree (meminfo, uptime, zram `mm_stat`, 13 fake processes, one kernel thread, one unreadable `smaps_rollup`). The report's arithmetic and labels were checked by hand against that input. Debian uses `mawk`, which was not available for this check. **It has never run on a real Linux system.**

To repeat that check, point the script at a fake tree with these variables (for testing only):

```sh
ALMOND_PROC=/path/to/fake/proc ALMOND_SYS=/path/to/fake/sys \
ALMOND_PASSWD=/path/to/fake/passwd ALMOND_OS_RELEASE=/path/to/os-release \
  sh tests/measure-memory.sh -n 10
```

A fake process is a directory `proc/<pid>/` with `comm`, `status` (`PPid:` and `Uid:` lines) and `smaps_rollup` (`Rss:`, `Pss:`, `Shared_*:`, `Private_*:`, `SwapPss:` lines in kB).

## Planned

- An automated acceptance check that runs inside a booted image (identity, network, APT sources, listening services, firewall state), following the manual steps in [docs/BUILD.md](../docs/BUILD.md).
- A boot-time and idle-CPU recorder (`systemd-analyze`, `vmstat`) that writes the same report format.
