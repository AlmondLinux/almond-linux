# AALDM — light edition
Official expansion: **A All Little Distribution Model**, recorded in D-0002. Intended for older and low-power 64-bit PCs. The first prototype is **0.1 Marcona**, based on Debian 13, LXQt, Openbox, X11 and LightDM; amd64 hybrid BIOS/UEFI image. arm64 is a development variant, not an established tested release.

## Approved direction and implementation boundary
**Almond Pure**: flat, warm, restrained desktop. Design rules record four owner-approved mockups on 2026-10-14, with image 1 the priority and image 2 the Super-key launcher. Images are missing. The built desktop has not been demonstrated to match them.

No compositor, transparency, blur, gradients or animation. Square corners; integrated application headers cannot generally be provided by Openbox. Occasional tools should have no resident cost when closed; the desktop PCManFM-Qt process is separately budgeted. Every added resident process needs a budget entry.

Existing [desktop source](../../desktop/) includes rofi Launcher, configured PCManFM-Qt Files, Openbox/Qt/LXQt Frame, icon themes and wallpapers. Build configuration and desktop boot have recorded VM tests; individual functions remain partly or wholly untested. No real-hardware, installed-system, or release approval follows from those boots.

## Identity and customization
Light, Dark and Ocean palettes; Blue, Gray, Green, Orange, Plum and Red folder accents. Atkinson Hyperlegible UI font, DejaVu fallback/monospace. Preserve the supplied official logo. Full-color logo belongs on light backgrounds; use supplied mono-light on dark backgrounds.

Current settings route through LXQt Appearance, Openbox settings, panel/desktop preferences and Session Settings. Almond Personalize is future work. Keyboard-only usability, contrast and scaling need acceptance testing. Do not import AALLDM transparency into AALDM.

## Targets and feedback
Under 300 MiB used, measured as MemTotal minus MemAvailable, and usability on 1 GiB where feasible are targets. Recorded runs: **393.2 MiB at 1024 MB**, **413.2 MiB at 2048 MB**, one boot each. Target unmet. See [test limits](TESTS.md).

Owner feedback recorded after the first boot: dislikes desktop icons and wants a start menu with settings. T-0005 requires decisions on icons and whether a classic menu supplements or replaces the launcher. These requests do not mean the approved design was already changed.

Sources: [AALDM plan](../AALDM-PLAN.md), [design rules](../DESIGN_RULES.md), [performance method](../PERFORMANCE.md), [D-0002](../../ai-bridge/decisions/D-0002-edition-names.md), [test report](../../tests/results/2026-10-17-vm/RESULTS.md).
