#!/bin/bash
# Copyright (c) 2026 mumuxiao722
# SPDX-License-Identifier: GPL-2.0-only
#
# Build the .deb package and place the artifact at the repo top level
# (sheng-gnome-fix_1.0.0_all.deb). Uses dpkg-deb (--root-owner-group).
#
# The source tree follows the Linux sysroot layout. Each daemon lives in its
# own directory with a /usr/ subtree; shared configs live in common/usr/.
# They are merged into one package root and packaged together.
set -e
umask 022

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$HERE"
STAGE="$REPO_ROOT/deb/root"

rm -rf "$STAGE"
mkdir -p "$STAGE/usr"

cp -a "$REPO_ROOT/sheng-fake-tablet-mode/usr/." "$STAGE/usr/"
cp -a "$REPO_ROOT/sheng-power-key-toggle/usr/." "$STAGE/usr/"
cp -a "$REPO_ROOT/common/usr/." "$STAGE/usr/"

find "$STAGE/usr" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$STAGE/usr" -type f -exec chmod 644 {} +
find "$STAGE/usr" -type d -exec chmod 755 {} +
chmod 755 "$STAGE/usr/libexec/sheng-fake-tablet-mode" "$STAGE/usr/libexec/sheng-power-key-toggle"

mkdir -p "$STAGE/DEBIAN"
cp "$REPO_ROOT/DEBIAN/control" "$REPO_ROOT/DEBIAN/postinst" \
   "$REPO_ROOT/DEBIAN/prerm" "$REPO_ROOT/DEBIAN/postrm" \
   "$STAGE/DEBIAN/"
chmod 755 "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/prerm" "$STAGE/DEBIAN/postrm"

dpkg-deb --build --root-owner-group "$STAGE" "$REPO_ROOT/sheng-gnome-fix_1.0.0_all.deb"

rm -rf "$STAGE"

echo "=== sheng-gnome-fix DEB build complete ==="
ls -la "$REPO_ROOT"/sheng-gnome-fix_1.0.0_all.deb