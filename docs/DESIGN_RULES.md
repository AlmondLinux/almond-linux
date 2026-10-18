# Design rules

Rules every contributor and AI agent follows when changing how Almond Linux looks or behaves. Status of each part: [PROJECT_STATUS.md](PROJECT_STATUS.md). Detailed component plan: [AALDM-PLAN.md](AALDM-PLAN.md).

If a change would break one of these rules, stop and ask the owner first. Do not "improve" an approved design on your own.

## Identity

- Name: **Almond Linux**, short **Almond**. Tagline: **Simple. Powerful. Yours.**
- Editions: **AALDM — A All Little Distribution Model** (light) and **AALLDM — A All Large Linux Distribution Model** (large). Spell them exactly like this.
- Release codenames: Spanish almond varieties. 0.1 "Marcona", 0.2 "Largueta", 0.3 "Valencia". 0.5 and 1.0 are not named.
- Never present Almond as affiliated with Debian, AlmaLinux, Linux Mint, Canonical or anyone else. Keep the trademark footer line ("Linux® is the registered trademark of Linus Torvalds…").

## Logo

- The official logo is the owner's brown almond, adopted 2026-10-14. Files: `branding/logo/`, `branding/almond-logo*.png`. See `branding/logo/README.md`.
- **Never redraw, recolour, stretch or "modernise" the logo.** Use the provided files.
- Its outline is dark brown `#3E210F`, so place the full-colour logo **only on cream or light backgrounds**. On dark backgrounds use the provided mono-light variant.
- The name and logo are not covered by the MIT License (see `NOTICE`).

## Colour

Brand palette:

| Name | Hex |
|---|---|
| Brown | `#8B5A2B` |
| Almond beige | `#D2A679` |
| Cream | `#F5DEB3` |
| Dark brown | `#2B2118` |

Almond Pure desktop palettes (`desktop/lxqt/palettes/`): **Light** (window `#F5F2EB`, text `#2B2118`), **Dark** (window `#202125`, text `#F5DEB3`), **Ocean** (window `#E9EEF3`, text `#14212E`). Folder-colour variants: Blue, Gray, Green, Orange, Plum, Red (purple is allowed as a folder accent).

- Check contrast before adopting any new colour pair: text at least WCAG AA (4.5:1, 3:1 for large text); icons and other non-text at least 3:1.
- Do not copy another distribution's colours.

## Typography

- UI font: **Atkinson Hyperlegible** (Debian package `fonts-atkinson-hyperlegible`).
- Fallback and monospace: **DejaVu** (`fonts-dejavu-core`).
- Website: Young Serif (headings) + Atkinson Hyperlegible + DejaVu Sans Mono, all self-hosted.

## Almond Pure (AALDM look) — DESIGNED, owner-approved mockups

The four approved mockup images (2026-10-14) are not stored in this repository; image 1 has priority and image 2 is the Super-key launcher. Where code and mockups differ for technical reasons, the reason is written in AALDM-PLAN.

Hard rules for AALDM, because performance is its top priority:

- **Flat graphics only.** No compositor requirement, no blur, no transparency, no shadows that need compositing, no gradients, no animations.
- No resident daemon unless essential. Every resident process gets a line in the memory budget ([PERFORMANCE.md](PERFORMANCE.md)).
- Tools needed only sometimes (launcher, settings, file manager windows) must cost **0 MB when closed**.
- Square window corners (no compositor to round them).
- Integrated title-bar/toolbar headers from the mockups are only possible for programs that draw their own headers; Openbox cannot theme inside application windows. This is a known, accepted deviation.

## Components

| Component | Rule |
|---|---|
| Almond Launcher | rofi-based, opened by the lone Super key, keyboard-first, exits when closed. Target: opens within about half a second on the OptiPlex 390 |
| Almond Files | PCManFM-Qt, configured. No custom file manager for 0.1; missing features go upstream. Never auto-mount internal disks |
| Almond Frame | Openbox themes Almond-Pure-Light / -Dark / -Ocean, Qt Fusion + Almond palette, LXQt QSS theme. GTK apps get Adwaita / Adwaita-dark settings only |
| Almond Icons / Almond Fold | freedesktop icon theme, SVG, flat, under 8 KB per file, checked by `tools/check-icons.py`. Third-party brand icons (Firefox etc.) are not redrawn |
| Almond Glass, Spaces, Bridge, Shield, performance modes | **Concepts only** (definitions in [PROJECT_STATUS.md](PROJECT_STATUS.md#components)). Do not build them until the owner approves a spec ([T-0002](../ai-bridge/tasks/T-0002-confirm-component-definitions.md)). Glass's translucent styles and the Medium/High performance modes conflict with the AALDM rules above, so they are AALLDM-only unless the owner decides otherwise. Bridge must never promise universal Windows compatibility; Shield must stay optional |

## Customisation requirements

- Use existing tools first: LXQt Appearance, Openbox Settings, panel and desktop preferences, LXQt Session Settings.
- The user must be able to change: palette (Light / Dark / Ocean), icon theme and folder colour, window theme, fonts and size, wallpaper, which session modules run.
- "Almond Personalize" (one app for theme, accent and folder colour) is PLANNED, and only after the default look is tested.
- Changes must persist after log-out on an installed or persistent system.

## Accessibility

- Every task must be possible with the keyboard alone.
- High-contrast palette and text scaling are PLANNED; Orca is opt-in (not installed by default) until measured.
- No motion by design (see Almond Pure rules).

## Performance targets (AALDM)

Targets, never claims: idle RAM under 300 MB used 120 s after login, usable on 1 GB RAM where feasible. Measured only with `tests/measure-memory.sh` and the method in [PERFORMANCE.md](PERFORMANCE.md). Nothing comparing Almond with another distribution is published until measured, with method and raw data.

## Packages

Debian `main` only, plus `non-free-firmware` for firmware. No `contrib`, no `non-free`, no third-party repositories, never disable signature checks. Built without Recommends: every package is named on purpose and commented if it was a Recommends.

## Honesty

Never claim something works until it has been shown to work. Docs, commits, PRs and AI reports describe what was actually built and tested.
