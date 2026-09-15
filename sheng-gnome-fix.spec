# Copyright (c) 2026 mumuxiao722 <zy349931@163.com>
# SPDX-License-Identifier: GPL-2.0-only
#
# Version-independent noarch RPM (no %%{dist}): installs on any Fedora
# release. Built from this repository by build-rpm.sh; published as a
# GitHub Release.
#
# Combined package for the Xiaomi Pad 6S Pro (sheng):
#   - fake-tablet-mode:           hides gpio-keys hall sensor and deterministically
#                                  exposes SW_TABLET_MODE to mutter for auto-rotation.
#   - sheng-power-key-display-toggle: uses the power key to blank/restore the display
#                                  instead of suspending.
#   - sleep.conf.d drop-in:       disables suspend/hibernate system-wide
#   - logind.conf.d drop-in:      ignores power key and lid events at logind level.
#   - gschema override:           disables GNOME suspend and auto-suspend.
#
# Upstream NixOS implementation: DotRedstone/nixos-sheng

%undefine __debug_package
%undefine _debugsource_packages
Name:           sheng-gnome-fix
Version:        1.0.0
Release:        1
Summary:        GNOME sleep/display/toggle fixes for the Xiaomi Pad 6S Pro (sheng)

License:        GPL-2.0-only
URL:            https://github.com/mumuxiao722/sheng-gnome-fix
Source0:        %{name}-%{version}.tar.gz

%define _debug_source_subpackages 0

BuildArch:      noarch
Requires:       python3
Requires:       python3-evdev
Requires:       glib2
Requires:       systemd

%description
Disables suspend/hibernate and replaces the power key with a display toggle
for the Xiaomi Pad 6S Pro (sheng), where deep sleep cannot be woken reliably.

Two small systemd services run at boot:
 - sheng-fake-tablet-mode: deterministically exposes SW_TABLET_MODE to mutter so
   that auto-rotation works.  A udev rule hides the real gpio-keys hall
   sensor from libinput; a virtual uinput switch reports tablet mode.
- sheng-power-key-toggle: exclusively grabs the physical power
    button and toggles org.gnome.Mutter.DisplayConfig PowerSaveMode on each
    press, injecting KEY_WAKEUP to force a screen repaint on wake and locking
    every session via loginctl so the next wake lands on the screen lock.

Systemd sleep.conf.d, logind.conf.d and gschema overrides disable suspend,
auto-suspend, and the GNOME power-button action so these functions are never
triggered at the desktop.

GNOME-only: the RPM is only installed in the Fedora rootfs when the GNOME
desktop is selected.

%prep
tar -xf %{SOURCE0}

%install
install -d %{buildroot}/usr
cp -a sheng-fake-tablet-mode/usr/. %{buildroot}/usr/
cp -a sheng-power-key-toggle/usr/. %{buildroot}/usr/
cp -a common/usr/. %{buildroot}/usr/

find %{buildroot}/usr -type f -exec chmod 644 {} +
find %{buildroot}/usr -type d -exec chmod 755 {} +
chmod 755 %{buildroot}/usr/libexec/sheng-fake-tablet-mode %{buildroot}/usr/libexec/sheng-power-key-toggle

%post
%systemd_post sheng-fake-tablet-mode.service sheng-power-key-toggle.service
glib-compile-schemas /usr/share/glib-2.0/schemas &>/dev/null || :

%preun
%systemd_preun sheng-fake-tablet-mode.service sheng-power-key-toggle.service

%postun
%systemd_postun_with_restart sheng-fake-tablet-mode.service sheng-power-key-toggle.service

%files
/usr/libexec/sheng-fake-tablet-mode
/usr/libexec/sheng-power-key-toggle
%{_unitdir}/sheng-fake-tablet-mode.service
%{_unitdir}/sheng-power-key-toggle.service
%{_presetdir}/50-sheng-gnome-fix.preset
/usr/lib/udev/rules.d/80-sheng-gnome-fix.rules
/usr/lib/systemd/logind.conf.d/10-sheng-gnome-fix.conf
/usr/lib/systemd/sleep.conf.d/10-sheng-no-suspend.conf
/usr/lib/modules-load.d/sheng-gnome-fix.conf
/usr/share/glib-2.0/schemas/zz-sheng-gnome-fix.gschema.override

%changelog
* Mon Sep 15 2026 mumuxiao722 <zy349931@163.com> - 1.0.0-1
- First release of sheng-gnome-fix.  Consolidates sheng-fake-tablet-mode and
  sheng-power-key-toggle into one package and disables system-wide
  suspend/hibernate to avoid the device hanging on wake from deep sleep.
  Adapted from DotRedstone/nixos-sheng.