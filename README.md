# sheng-gnome-fix

[中文](README_CN.md)

GNOME fixes for the Xiaomi Pad 6S Pro (`sheng`): deterministic **auto-rotation**,
a **power key** that blanks/restores the display instead of suspending, and
system-wide removal of suspend/hibernate (deep sleep cannot be woken on this
device - the kernel aborts it and leaves a black screen).

Everything is packaged as one distro-agnostic package (noarch RPM and `all`
DEB). The source tree follows the Linux sysroot layout: each daemon lives in
its own `/<daemon>/usr/` subtree, shared configuration lives in
`common/usr/`, and the build scripts merge them into a single package.

## What it does

Two small systemd services run at boot:

1. **`sheng-fake-tablet-mode`** - GNOME auto-rotation
   The physical `gpio-keys` hall sensor reports `SW_TABLET_MODE=0` in the
   shipped DTB, which makes mutter lock into "laptop" posture and permanently
   disable auto-rotation. A udev rule hides that switch from libinput, and a
   virtual `uinput` device reports `SW_TABLET_MODE` instead. The device starts
   in laptop mode (OFF); every 200 ms the daemon scans `/proc` for the
   *user's* `gnome-shell` (the GDM greeter's shell is excluded via uid range
   and `--mode=gdm`) and, after 25 consecutive ticks (~5 s), flips the switch
   0->1 to unlock mutter panel-orientation management. When the shell exits
   the switch drops back to OFF, so any session restore produces a fresh 0->1
   edge. Cover close/open blanks via `org.gnome.Mutter.DisplayConfig`
   `PowerSaveMode`. The core service has been replaced by a new implementation;
   lid open/close still uses the old one.

2. **`sheng-power-key-toggle`** - power key = display toggle, never sleep
   A wakeup pending during the suspend CPU-freeze aborts deep sleep and leaves
   a black, unresponsive screen (`Wakeup pending. Abort CPU freeze`). This
   service exclusively grabs the physical power key so GNOME never sees it as
   a suspend/wake request, and turns each press into a
`PowerSaveMode` 3<->0 toggle (3 = display off, 0 = on), injecting a
  `KEY_WAKEUP` event on wake to force a screen repaint. Blanking also locks
  every session via `loginctl lock-sessions`, so the next wake lands on the
  GNOME screen lock.

So "sleep" on sheng only ever means "display off, session locked". Suspend/hibernate is disabled
entirely:

- `/usr/lib/systemd/sleep.conf.d/10-sheng-no-suspend.conf` - `AllowSuspend=no`,
  `AllowHibernation=no`, `AllowHybridSleep=no`, `AllowSuspendThenHibernate=no`
  (no GNOME "Suspend" button, no auto-sleep).
- `/usr/lib/systemd/logind.conf.d/10-sheng-gnome-fix.conf` - ignores the power
  key and all lid-switch events at the logind level.
- GSettings override (`zz-sheng-gnome-fix.gschema.override`) - sets
  `power-button-action=nothing`, `sleep-inactive-*=nothing`, `idle-dim=false`,
  `ambient-enabled=false` system-wide.

Auto screen **locking still works**: it is driven by idle blanking, independent
of suspend. After the idle delay the screen blanks and locks; the power key
wakes it back to the lock screen.

## Files

| Source (sysroot)                       | Installed to                                  |
| -------------------------------------- | --------------------------------------------- |
| `sheng-fake-tablet-mode/usr/libexec/`  | `/usr/libexec/sheng-fake-tablet-mode`         |
| `sheng-power-key-toggle/usr/libexec/`  | `/usr/libexec/sheng-power-key-toggle`         |
| `sheng-*/usr/lib/systemd/system/`      | `/usr/lib/systemd/system/*.service`           |
| `common/usr/lib/systemd/system-preset/`| `/usr/lib/systemd/system-preset/50-sheng-gnome-fix.preset` |
| `common/usr/lib/udev/rules.d/`         | `/usr/lib/udev/rules.d/80-sheng-gnome-fix.rules` |
| `common/usr/lib/systemd/logind.conf.d/`| `/usr/lib/systemd/logind.conf.d/10-sheng-gnome-fix.conf` |
| `common/usr/lib/systemd/sleep.conf.d/` | `/usr/lib/systemd/sleep.conf.d/10-sheng-no-suspend.conf` |
| `common/usr/lib/modules-load.d/`       | `/usr/lib/modules-load.d/sheng-gnome-fix.conf` |
| `common/usr/share/glib-2.0/schemas/`   | `/usr/share/glib-2.0/schemas/zz-sheng-gnome-fix.gschema.override` |

## Prerequisites

- Python 3 with `python3-evdev`, plus systemd and udev.
- GNOME (the daemons drive mutter via its per-session D-Bus `DisplayConfig`).

## Packaging

Prebuilt packages are published as GitHub Releases; the Fedora rootfs build in
[fedora-sheng](https://github.com/mumuxiao722/fedora-sheng) fetches the
released RPM when built with **desktop=GNOME**:

- `sheng-gnome-fix-1.0.0-1.noarch.rpm` – version-independent noarch RPM (no
  `%{dist}`), installs on any Fedora release.
- `sheng-gnome-fix_1.0.0_all.deb` – Debian/Ubuntu package
  (`Depends: python3, python3-evdev, glib2.0-bin, systemd`).

Install:

- Fedora: `sudo dnf install --nogpgcheck ./sheng-gnome-fix-1.0.0-1.noarch.rpm`
- Debian/Ubuntu: `sudo dpkg -i sheng-gnome-fix_1.0.0_all.deb`, then
  `sudo apt-get install -f` to fill in dependencies.

A reboot is required after installing for the udev rule, the systemd
drop-ins/preset and the two units to take effect. If you previously installed
`sheng-tablet-mode`, remove it first (`dnf remove sheng-tablet-mode` /
`dpkg -r sheng-tablet-mode`).

## Building

- `./build-deb.sh` – runs anywhere `dpkg-deb` is available (e.g. Termux);
  outputs the `.deb` in the current directory.
- `./build-rpm.sh` – run inside a Fedora container/chroot (needs
  `rpm-build`), e.g. the DroidSpaces Fedora-44 container on the device or a
  `podman run` against a Fedora image; outputs the RPM in the current
  directory.

## Related Projects

- [DotRedstone/nixos-sheng](https://github.com/DotRedstone/nixos-sheng) – NixOS implementation this package's cover-blanking and power-key handling are adapted from
- [fedora-sheng](https://github.com/mumuxiao722/fedora-sheng) – Fedora tablet-mode rootfs that consumes the released RPM
- [CFM880/nabu-accelerometer](https://github.com/CFM880/nabu-accelerometer) – source of the tablet-mode core ported into `sheng-fake-tablet-mode`

## Credits

- **DotRedstone** – the original `fake-tablet-mode` and
  `sheng-power-key-display-toggle` services in
  [nixos-sheng](https://github.com/DotRedstone/nixos-sheng) form the basis of
  this package. The new `sheng-fake-tablet-mode` daemon replaces the original
  `fake-tablet-mode`; its cover open/close blanking is still adapted from that
  project.
- **CFM880** – the desktop-reporting core of `sheng-fake-tablet-mode` is a
  faithful port of
  [nabu-accelerometer](https://github.com/CFM880/nabu-accelerometer)`s
  `userspace/nabu-tablet-mode.c`.

Licensed under GPL-2.0-only. See `LICENSE`.