# Components, installer and customization
Snapshot: PR #1 at d668bc8. “Source” means files inspected, not a new runtime test. Task state is from that snapshot.

| Component | Recorded behavior / requirement | Evidence and status | Remaining limits |
|---|---|---|---|
| Almond Launcher / Almond Launch | rofi, Super-key, Apps/Windows/Recent/System; Light/Dark/Ocean | [Source](../../desktop/launcher/), partly VM-tested | Default Hibernate highlight, selection mismatch, missing icons; T-0003 backlog |
| Almond Files | Configured PCManFM-Qt, not a custom 0.1 file manager | [Plan](../AALDM-PLAN.md), desktop defaults; seen open in VM | USB/SFTP/find/hidden-file and volume-monitor checks not run; no internal-disk auto-mount |
| Almond Files Pro | AALLDM “Adaptive Minimalist” direction | PROJECT_STATUS reports owner's notes | No detailed recovered spec or software |
| Almond Frame | Openbox Light/Dark/Ocean, Qt Fusion palettes, LXQt QSS; GTK Adwaita settings | [Themes](../../desktop/openbox/), [palettes](../../desktop/lxqt/palettes/); session seen running | Contrast/theme checks missing; AALLDM Unified Frame is a design direction |
| Almond Glass | Right-side application bar; solid/translucent/frosted/clear; adjustable position, opacity, size | AALLDM visual design plus conceptual definitions | No approved implementation spec; translucent styles conflict with AALDM |
| Almond Spaces | Workspaces, saved layouts, grouping, previews, multi-monitor and restore | Visual/design direction | Restore and multi-monitor behavior unresolved |
| Almond Bridge | Compatibility manager for supported Windows apps | Planned, Wine or Proton are candidates | No selected engine/support list; never universal compatibility; distinct from AI Bridge |
| Optional Almond Shield | Antivirus/security center, scans, quarantine, warnings | Proposal | Must stay optional; base security must not depend on it; no implemented scanner claim |
| Customization | Palette, icons/folder colors, windows, fonts/size, wallpaper, session modules | Existing LXQt/Openbox tools; Personalize app planned | Persistence requires installed/persistent-system checks |
| Potato / Medium / High | User-overridable performance presets | Planned design requirement, T-0002 | No quantified budgets or implemented presets; AALDM applicability unresolved |

## Installer
[T-0007](../../ai-bridge/tasks/T-0007-install-almond-linux-option-with-calamares.md) is ready and records the owner's request for a clear **Install Almond Linux** entry on the live desktop and launcher, using Calamares. This is work toward the 0.5 milestone, not an installed feature.

Required research: Debian packages, size, configuration and Almond-specific branding. Required separation: remove live user, autologin and passwordless sudo from installed defaults. Planned validation is BIOS and UEFI installation and first boot on disposable VirtualBox disks, user/password checks and updates. No real-hardware install is authorized by this knowledge import.

## Almond Fetch
[T-0006](../../ai-bridge/tasks/T-0006-almond-a-terminal-system-information-command.md) records a ready task for command `almond`: edition, kernel, CPU model/thread count, GPU(s), RAM used/total and uptime from real system data. Unknown values must say unknown. POSIX shell, no new packages, /proc, /sys, os-release, uname and existing lspci; fake-system-tree tests planned.

Options: --no-color, --no-logo, --help; disable colors for non-terminal output. The conversation proposed an “official Almond terminal logo,” but the task explicitly treats a terminal mark as a **proposal pending owner approval**. Do not silently equate ASCII artwork with the official logo. No Fetch implementation or VM validation was established at this snapshot.

Sources: [status](../PROJECT_STATUS.md), [rules](../DESIGN_RULES.md), [T-0002](../../ai-bridge/tasks/T-0002-confirm-component-definitions.md), and source links above. Full underlying Obsidian definitions were not directly accessed.
