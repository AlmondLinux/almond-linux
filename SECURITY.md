# Security policy

## Status

Almond Linux has **no released versions**. Nothing from this project is meant to be installed or used on a real computer yet, so there are no supported versions and no security updates.

Security reports are still welcome, especially about the build configuration and the defaults it would ship.

## Reporting a vulnerability

Please report security problems **privately**, not in a public issue:

1. Go to the repository's **Security** tab: <https://github.com/AlmondLinux/almond-linux/security>
2. Choose **Report a vulnerability**.
3. Describe the problem, how to reproduce it, and what an attacker could do with it.

This uses GitHub's private vulnerability reporting, so only the maintainers can see your report.

## What to expect

Almond is a small, volunteer project. A maintainer will try to acknowledge reports within 14 days. Details will be published once the problem is understood and, where needed, only after a fix is available.

## Scope

- **In scope:** files in this repository (build configuration, scripts, image customisation hooks) and the defaults they would produce.
- **Upstream software:** problems in Debian packages themselves should go to Debian: <https://www.debian.org/security/>. Almond does not patch upstream packages.
