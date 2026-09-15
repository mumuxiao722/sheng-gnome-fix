#!/bin/bash
# Copyright (c) 2026 mumuxiao722
# SPDX-License-Identifier: GPL-2.0-only
#
# Build the version-independent noarch RPM and place the artifact at the repo
# top level (sheng-gnome-fix-1.0.0-1.noarch.rpm). Run inside a Fedora
# container/chroot with rpm-build available (e.g. the DroidSpaces Fedora-44
# container, or a podman run against a Fedora image).
#
# Usage: build-rpm.sh [RPMBUILD_TOP]   # default RPMBUILD_TOP=/tmp/rpmbuild
set -e

TOP="${1:-/tmp/rpmbuild}"
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

dnf install -y rpm-build tar systemd systemd-rpm-macros

rm -rf "$TOP"
mkdir -p "$TOP"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

cp "$REPO_ROOT/sheng-gnome-fix.spec" "$TOP/SPECS/"

cd "$REPO_ROOT"
tar -czf "$TOP/SOURCES/sheng-gnome-fix-1.0.0.tar.gz" \
    --exclude=.git \
    --exclude=DEBIAN \
    --exclude=sheng-gnome-fix.spec \
    --exclude='build-*.sh' \
    --exclude='*.deb' \
    --exclude='*.rpm' \
    --exclude='__pycache__' \
    .

rpmbuild --define "_topdir $TOP" -ba "$TOP/SPECS/sheng-gnome-fix.spec"

cp "$TOP"/RPMS/noarch/sheng-gnome-fix-*.rpm "$REPO_ROOT/"

echo "=== sheng-gnome-fix RPM build complete ==="
ls -la "$REPO_ROOT"/sheng-gnome-fix-*.rpm