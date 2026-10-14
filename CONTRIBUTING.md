# Contributing to Almond Linux

Thank you for your interest. Almond is at the very beginning: no ISO has been built yet. That shapes what help is useful right now.

## Most useful right now

1. **Test the build.** Follow [docs/BUILD.md](docs/BUILD.md): build and test inside a **Debian 13 amd64 virtual machine** (step by step for a Windows PC: [docs/PC-SETUP.md](docs/PC-SETUP.md)), and report exactly what happened, including the failures. A clear failure report is as valuable as a success. An arm64 VM (for example on an Apple Silicon Mac) can only build the arm64 development variant; it tests the build and the desktop, not the AALDM target hardware.
2. **Review.** Read the build configuration and docs, and point out mistakes, unsafe defaults or unclear wording.
3. **Ask questions.** If something in the docs confused you, it will confuse the next person too.

## Reporting a problem

Open an issue at <https://github.com/AlmondLinux/almond-linux/issues> and include:

- what you did, step by step;
- what you expected, and what actually happened;
- your virtual machine software and version, the host architecture, and whether you built amd64 or the arm64 development variant;
- the relevant part of `configure.log` or `build.log` (attach long logs as files).

**Security problems are different:** do not open a public issue. Follow [SECURITY.md](SECURITY.md).

## Proposing a change

1. Open an issue first for anything bigger than a typo, so the idea can be discussed before you spend time on it.
2. Keep each pull request to one change, and explain *why* in its description.
3. Say how you tested it. "Not tested" is an acceptable answer; pretending is not.
4. Package policy: packages come from Debian's `main` archive area only, plus `non-free-firmware` for firmware packages only (CPU microcode counts as firmware); these are the areas `auto/config` enables. No other areas (`contrib`, `non-free`), no third-party repositories, and never disable package signature checks.
5. Shell scripts must stay POSIX `sh` and pass `sh -n`.

## Honesty rule

Almond never claims something works until it has been shown to work. Docs, commit messages and pull requests must describe what was actually built and tested, not what is expected.

## Licensing of contributions

Almond's own files are under the [MIT License](LICENSE). By submitting a contribution you confirm that you wrote it (or have the right to submit it) and agree that it is released under the MIT License. Do not submit code copied from projects whose license is incompatible with MIT.

## Conduct

Everyone taking part is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
