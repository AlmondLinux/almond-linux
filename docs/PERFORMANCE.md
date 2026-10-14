# AALDM performance budgets and measurement method

Written 2026-10-14. **Nothing has been measured yet**: no AALDM image has been built or booted. Every "Measured" cell says *not measured yet* until a report from `tests/measure-memory.sh`, taken with the method below, exists.

Performance is the top priority of AALDM (the little edition). The targets are **targets, not guarantees**:

- idle RAM under **300 MiB used** (MemTotal − MemAvailable) 120 s after login;
- usable on **1 GiB RAM** where feasible;
- minimal idle CPU and low GPU needs (no compositor, no animations, no transparency, no blur).

Component choices and the reasons for them: [AALDM-PLAN.md](AALDM-PLAN.md).

## Memory budgets

Budgets are PSS (proportional set size, see [below](#why-pss-and-not-rss)) in MiB, except the base OS line. The "Report line" column says where `measure-memory.sh` prints the number.

| Component | What runs | Target budget | Measured | Report line |
|---|---|---|---|---|
| Base OS | kernel, systemd, journald, udevd, D-Bus, logind, polkitd, timesyncd, cron; tmpfs/Shmem of the live session | 110 MiB | not measured yet | "Used" − "DESKTOP SESSION TOTAL" − "Network service" |
| Network service | NetworkManager, wpa_supplicant | 20 MiB | not measured yet | component "Network service" |
| X server | Xorg, modesetting driver, glamor | 35 MiB | not measured yet | component "X server (Xorg)" |
| Display manager | LightDM daemon and session helper (the greeter has exited) | 5 MiB | not measured yet | component "Display manager" |
| Window manager | Openbox | 8 MiB | not measured yet | component "Window manager" |
| LXQt session + panel | lxqt-session, lxqt-globalkeysd, lxqt-notificationd, lxqt-policykit-agent, lxqt-powermanagement, lxqt-panel | 55 MiB | not measured yet | component "LXQt session + panel" |
| Desktop | `pcmanfm-qt --desktop` (wallpaper and icons) | 25 MiB | not measured yet | component "Desktop + file manager", no window open |
| Network tray | nm-tray | 10 MiB | not measured yet | component "Network tray" |
| Audio | PulseAudio | 8 MiB | not measured yet | component "Audio" |
| Files and devices | gvfsd and its helpers, the remaining volume monitors `gvfs-udisks2-volume-monitor` and `gvfs-mtp-volume-monitor`, udisksd (the GOA, AFC and gphoto2 monitors are disabled by the 0200 hook; see [AALDM-PLAN.md section 7](AALDM-PLAN.md#7-file-manager-pcmanfm-qt-feature-map)) | 12 MiB | not measured yet | component "Files and devices"; no `gvfs-goa-*`, `gvfs-afc-*` or `gvfs-gphoto2-*` process may appear |
| Other session processes | systemd --user, user D-Bus, small helpers | 8 MiB | not measured yet | "Other processes of the session user" |
| Launcher | rofi (Almond Launcher) | **0 MiB when closed** (≤ 20 MiB while open) | not measured yet | component "Launcher" |
| File manager window | extra memory of the same pcmanfm-qt process while a window is open | 0 MiB when closed (≤ 20 MiB while open) | not measured yet | "Desktop + file manager", window open minus window closed |
| Customisation tools | lxqt-config, obconf-qt, pavucontrol-qt | **0 MiB resident** | not measured yet | must not appear when closed |
| **Idle total** | everything above with nothing opened | **< 300 MiB used** | not measured yet | "Used" |

The budgets add up to 296 MiB. They are deliberately tight: the planning estimates in AALDM-PLAN.md range from about 225 to 400 MiB, so some budgets will probably be missed at first. A missed budget is a finding, not a failure to hide: record it, then decide what to change.

Applications are not part of the idle budget. Record them separately, for example Firefox ESR with one simple page (no budget yet; estimate 250–450 MiB, not measured).

## Other targets (method still to be detailed)

| Target | Measurement | Measured |
|---|---|---|
| Minimal idle CPU | `vmstat 5 13` started 120 s after login; report the median `id` (idle %) and `cs` (context switches) of the last 12 lines | not measured yet |
| Boot time | `systemd-analyze` and `systemd-analyze blame`, plus a stopwatch from boot-menu selection to a usable desktop | not measured yet |
| Background services | `systemctl list-units --type=service --state=running` and `systemctl --user list-units --type=service --state=running` | not measured yet |
| Image size | ISO size; installed size = sum of the manifest (later) | not measured yet |

## Measurement method

Same procedure for every measurement, so results can be compared and repeated.

1. **Fixed machine.** Either a VM with fixed settings (record: hypervisor and version, RAM, CPU count, firmware BIOS or UEFI, graphics controller, display resolution, disk/no disk) or a named physical PC (record: model, CPU, RAM, GPU, firmware mode). Do not change settings between the boots of one series.
2. **Fixed image.** Record the ISO's SHA-256 (from `SHA256SUMS`), its `package-manifest.txt` and the kernel version (`uname -r`).
3. **Fresh boot.** Power off completely, then boot (no suspend/resume, no reboot from a used session if it can be avoided).
4. **Log in.** The live image logs in automatically; with autologin off, log in at the greeter. Note which.
5. **Wait 120 s idle.** Do not touch keyboard or mouse; open nothing. The script can wait for you: `-w 120`.
6. **Record.** As root, so every process can be read:
   ```sh
   sudo sh /usr/share/almond/tests/measure-memory.sh -w 120 > memory-boot1.txt
   ```
   (Use the repository's `tests/measure-memory.sh` if the image does not contain it.) The report includes `/proc/meminfo` (MemTotal, MemFree, MemAvailable, Buffers, Cached, Shmem, swap), **used = MemTotal − MemAvailable**, zram usage, and per-process RSS, PSS, shared and private memory from `/proc/<pid>/smaps_rollup`.
7. **Repeat 5 boots.** Report the **median** of the five for each figure (and the minimum and maximum), not the best run.
8. **Write down** the date, the Almond git commit, the kernel version, the package manifest and anything unusual (a crash dialog, an update notice, network down).

### Why PSS and not RSS

- **RSS** (resident set size) counts every page a process has in RAM, including pages *shared* with other processes. All Qt programs share the Qt libraries; with RSS each of them counts those libraries in full. Adding the RSS of ten LXQt processes therefore counts Qt ten times and gives a total far larger than the memory really used.
- **PSS** (proportional set size) divides each shared page by the number of processes that map it. A 20 MiB library shared by 10 processes adds 2 MiB to each. **PSS values add up**: the PSS sum of a group of processes is a fair estimate of the memory that group costs.
- **Shared / private**: `measure-memory.sh` also prints Shared_Clean + Shared_Dirty and Private_Clean + Private_Dirty. Private memory is what would be freed if the process exited.
- PSS needs root to read for other users' processes (`/proc/<pid>/smaps_rollup` is protected); without root the script warns that its totals are incomplete.

### Why "used" is not the PSS total

"Used" (MemTotal − MemAvailable) also contains memory that belongs to no process: the kernel itself, page tables, slab caches that cannot be reclaimed, tmpfs/Shmem, and memory used by zram. In a **live session** every file written (logs in `/run`, the home directory, caches) lives in RAM through the overlay and shows up as Shmem, so a live session reports more "used" memory than the same system installed on disk. Report live and installed results separately once an installer exists. Page cache (Cached) is mostly reclaimable and is already excluded by MemAvailable.

## Results template

Copy this table for each machine and image.

| Boot | Used (MiB) | MemAvailable (MiB) | Shmem (MiB) | Desktop session PSS (MiB) | All processes PSS (MiB) | zram RAM used (MiB) |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| **Median** | | | | | | |

Machine: … · ISO SHA-256: … · Kernel: … · Almond commit: … · Date: …

## Comparison with Linux Mint Xfce

The roadmap's goal is an AALDM that people prefer to Linux Mint's Xfce edition. Comparisons follow [ROADMAP.md](ROADMAP.md): same VM settings for both systems, same method as above (Mint measured with the same script), versions and raw reports published together. Nothing comparing Almond with Mint is published until both have been measured.
