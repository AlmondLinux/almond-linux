# ISO, test evidence and known bugs
Primary evidence: [RESULTS](../../tests/results/2026-10-17-vm/RESULTS.md), [1 GB memory](../../tests/results/2026-10-17-vm/memory-1gb.txt), [2 GB memory](../../tests/results/2026-10-17-vm/memory-2gb.txt). This import inspected reports; it did not run the ISO.

## Build and boot
Recorded test date **2026-10-17**, report written 18 October. Build commit **64014332c5ce6f22af1b43996bd2375184206fc1**.
ISO **live-image-amd64.hybrid.iso**, **845,152,256 bytes**.
Recorded SHA256: `7129bf3e3f7bededa373fe74dcc1e742891fd4d4c5dd7488581b5360d653fe9d`.
The report says checksum verification matched in the VM and Windows. The ISO is absent from this repository snapshot, so its bytes were not rehashed here.

Build host: Windows 11, i9-13900K, 63.7 GB RAM; VirtualBox 7.2.20 through the Windows hypervisor. Build VM: Debian 13.7, 8 GB, one CPU; four CPUs previously stalled. Test VM: two CPUs, no disk, VMSVGA 32 MB, NAT. These are report-attributed environment details, not newly measured hardware specifications.

| Test | Recorded result |
|---|---|
| Build | Successful, zero E: lines, 765 packages, hooks ran |
| BIOS, 2048 MB | Desktop with autologin, identity/session checks, partial launcher checks |
| UEFI, 2048 MB | Desktop and launcher open/close |
| BIOS, 1024 MB | Desktop and memory run |
| UEFI, 1024 MB | Not established by detailed report |
| Secure Boot | Not tested; build log support message is not a boot test |
| Dell OptiPlex 390 / other physical hardware | Not tested |
| Installation, stable release, public ISO download | Not established |

## Memory
| Configured VM RAM | Used | Desktop PSS | Sample count |
|---|---|---|---|
| 1024 MB (“1 GB”) | **393.2 MiB** (rounded chat: 393 MiB) | 244.5 MiB | One BIOS boot |
| 2048 MB (“2 GB”) | **413.2 MiB** (rounded chat: 413 MiB) | 243.7 MiB | One BIOS boot |

Used = MemTotal − MemAvailable, not sum of process RSS. QTerminal was open. Uptime at measurement: 335 / 329 seconds respectively; procedure waited on desktop and then script waited another 120 seconds. Four approximately 60-second VM clock stalls occurred in the 1 GB run. Both scans recorded 72 unreadable/exited processes and zero kernel threads, requiring investigation.

The **under-300 MiB goal is unmet**. The [method](../PERFORMANCE.md) calls for five fresh boots, median and range; these are not that benchmark. Do not claim a distribution comparison, installed-system memory result, or reliable speed target.

## Bugs, feedback and remaining tests
- T-0003: Hibernate highlighted on two of three openings; typing retained second match on two of two attempts. Risk of unintended action; Hibernate/Lock were not activated, so their effects are untested. Hide unsupported actions and test safe Enter behavior.
- T-0003: four iconless tiles (Session Settings, Rofi Theme Selector, Notifications, File Associations); long labels truncated.
- T-0004: two first-login power notifications; GRUB title overlaps logo; gzip fallback because zstd absent; memory scan accounting; stale docs.
- T-0005: owner dislikes desktop icons and requests a classic start menu/settings access; design decision pending.
- Environment issue: four-vCPU build VM freeze under Windows hypervisor. One CPU worked; not established as an Almond defect.
- Procedure errors: misplaced typing/focus and unconfirmed post-Esc process check are recorded in RESULTS; do not turn them into OS bugs.

Not tested: HTTPS browsing, apt update, audio, detailed Files/editor/viewer functions, keyboard-only flow, shortcut and resolution changes, listening services/firewall/AppArmor, fail-safe/Utilities entries, greeter, UEFI terminal/memory checks, five-boot series, real hardware. Internal disks of second-hand test machines must remain untouched.

The website update is a separate repository PR recorded by T-0008; its current publication state was not independently inspected during this import.
