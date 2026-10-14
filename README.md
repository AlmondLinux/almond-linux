<p align="center">
  <img src="branding/almond-logo-cream.png" width="200" alt="The Almond Linux logo: a brown almond above the words Almond Linux">
</p>

<h1 align="center">Almond Linux</h1>

<p align="center"><strong>Simple. Powerful. Yours.</strong></p>

<p align="center">
  <a href="https://almondlinux.github.io">Website</a> ·
  <a href="docs/ROADMAP.md">Roadmap</a> ·
  <a href="docs/AALDM-PLAN.md">AALDM plan</a> ·
  <a href="docs/BUILD.md">Build notes</a> ·
  <a href="docs/PC-SETUP.md">PC setup</a> ·
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

---

Almond Linux is an independent Linux distribution project focused on simplicity, stability, performance, and freedom. The initial operating system will be based on Debian. The long-term goal is for Almond to become a fully independent distribution of its own.

> **Status: early development.** No ISO has been built, booted or released. Nothing in this repository is ready to install. See [Project status](#project-status).

## Names

| Name | Meaning |
|---|---|
| **Almond Linux** | The official project name. Short name: **Almond**. |
| **AALLDM** | **A All Large Linux Distribution Model** — the large edition: a bigger, more modern desktop for newer PCs. |
| **AALDM** | **A All Little Distribution Model** — the little edition: a lighter system for older and low-power 64-bit PCs. |

Release codenames are Spanish almond varieties: **0.1 "Marcona"**, **0.2 "Largueta"**, **0.3 "Valencia"**. Later releases are not named yet.

## Project status

As of 14 October 2026. Status words: **Planned** · **Implemented (source exists, untested)** · **Tested** · **Released**.

| Area | Status |
|---|---|
| AALDM build configuration (live-build, amd64 hybrid BIOS+UEFI ISO; arm64 dev variant) | Implemented (source exists, untested). Checked: shell syntax, that the build script refuses to run outside a Debian 13 build machine, and that every package name exists in Debian 13 |
| ISO image | Planned (not built yet) |
| Boot, networking, security defaults | Implemented (source exists, untested): nothing has been booted yet |
| Almond Pure desktop: Almond Frame (Openbox themes, Qt palettes, LXQt themes), icons and folder colours, Almond Launcher, desktop defaults (LXQt, Openbox, PCManFM-Qt, GTK, global shortcuts) | Implemented (source exists, untested): staged into the image by the build; none of it has run |
| Branding: logo, boot menu artwork, wallpapers, image identity | Implemented (source exists, untested) |
| Memory measurement (`tests/measure-memory.sh`, also copied into the image) | Implemented (source exists, untested on Linux) |
| AALDM phases 1–10 ([plan, section 14](docs/AALDM-PLAN.md#14-phases-mapped-to-the-roadmap)) | No phase is complete |
| Anything Tested | Nothing yet |
| Installer | Planned |
| Editions | AALDM first (provisional desktop: LXQt + Openbox on X11). AALLDM: desktop still undecided |
| Website | [almondlinux.github.io](https://almondlinux.github.io) |

## Roadmap

| Version | Goal | Status |
|---|---|---|
| 0.1 "Marcona" | First bootable AALDM ISO for 64-bit PCs (amd64) | Implemented (source exists, untested) |
| 0.2 "Largueta" | Custom Almond branding, wallpaper, themes, and system identity | Planned (its assets: Implemented (source exists, untested)) |
| 0.3 "Valencia" | Customized desktop experience | Planned |
| 0.5 | Graphical installer and testing | Planned |
| 1.0 | First stable public release | Planned |

A milestone is only marked done when its evidence exists (ISO hash, build log, boot tests and so on). After 1.0, Almond plans to become independent of Debian one layer at a time. Details: [docs/ROADMAP.md](docs/ROADMAP.md).

## Technical direction

- **Base:** Debian Stable, currently Debian 13 "trixie" (`main` and `non-free-firmware`).
- **Build tool:** [Debian live-build](https://wiki.debian.org/DebianLive).
- **First edition: AALDM on amd64.** A hybrid ISO that boots old PCs in legacy-BIOS and UEFI mode, from DVD or USB. Provisional desktop, approved by the owner for evaluation: **LXQt + Openbox on X11** with LightDM; no compositor, no animations, flat graphics. Targets (not guarantees): idle RAM under 300 MB, usable on 1 GB RAM where feasible. Plan: [docs/AALDM-PLAN.md](docs/AALDM-PLAN.md); budgets and method: [docs/PERFORMANCE.md](docs/PERFORMANCE.md).
- **First real test PC:** a Dell OptiPlex 390 (2011, 64-bit Intel, integrated graphics), a second-hand PC: booted from USB only, and its internal disk is never mounted or read.
- **ARM64** is only a development variant (VMs on Apple Silicon Macs), not a target.
- **AALLDM** (the large edition): desktop still undecided.
- **Almond Pure** (the visual design): icons, folder colours, Openbox themes, launcher and boot artwork are Implemented (source exists, untested): they exist as source files and the build stages them into the image, but none of it has run yet.
- **Testing:** virtual machines first (VirtualBox, QEMU/KVM, UTM), then the OptiPlex 390.
- **Not a goal:** native installation on Apple Silicon Macs.

Architecture notes: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Component plan and the ten AALDM phases: [docs/AALDM-PLAN.md](docs/AALDM-PLAN.md). How to try a build: [docs/BUILD.md](docs/BUILD.md) (Windows PC walk-through: [docs/PC-SETUP.md](docs/PC-SETUP.md)). Testing happens in a Debian 13 amd64 VM first.

## Repository layout

```
auto/config                     live-build configuration (ALMOND_EDITION, ALMOND_ARCH, ALMOND_FIRMWARE)
config/package-lists/           packages in the image (aaldm.list.chroot)
config/hooks/live/              image customisation (Almond identity, desktop defaults)
scripts/build.sh                guarded build wrapper: refuses to run unless on Debian 13 as root with
                                live-build and a matching architecture; stages the Almond assets;
                                meant for a dedicated build machine
desktop/                        Almond Pure desktop assets (icons, Openbox themes, launcher, defaults)
branding/                       the Almond logo and boot artwork
tests/                          measurement tools (measure-memory.sh)
tools/                          generators for some of the artwork
docs/                           plan, performance, architecture, build notes, roadmap
```

## Contributing

Almond is at the very beginning, so the most useful help right now is careful testing, review and honest feedback. Read [CONTRIBUTING.md](CONTRIBUTING.md) first. Everyone taking part is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

Security problems: please report them privately, as described in [SECURITY.md](SECURITY.md), never in a public issue.

## License

Almond's own files (build configuration, scripts and documentation) are released under the [MIT License](LICENSE). What it does not cover is listed in [NOTICE](NOTICE).

- **Upstream software keeps its own licenses.** An Almond image is assembled mainly from Debian packages; each keeps its original license and copyright. The MIT License does not relicense them.
- **The name and logo are not covered by the MIT License.** "Almond Linux" and the almond logo identify this project. Please do not use them in a way that suggests something is an official Almond release when it is not.

## Disclaimer

Almond Linux is in early development and comes with no warranty. Do not install anything from this project on a computer you care about.

Almond Linux is an independent project and is not affiliated with, endorsed by or sponsored by Debian, Canonical, Red Hat, AlmaLinux, or any other Linux organization. Linux® is the registered trademark of Linus Torvalds in the U.S. and other countries. Debian is a registered trademark owned by Software in the Public Interest, Inc.
