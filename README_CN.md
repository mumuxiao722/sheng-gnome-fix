# sheng-gnome-fix

[English](README.md)

小米平板 6S Pro（`sheng`）的 GNOME 修复集合：确定性的**自动旋转**、把**电源键**
变成「息屏/亮屏」开关（而不是睡眠），以及在系统层面**彻底禁用 suspend/hibernate**
（本机 deep 睡眠必然失败：内核在停 CPU 时被 pending 唤醒打断并留下黑屏，无法唤醒）。

统一打成一个与发行版无关的包（noarch RPM 与 `all` DEB）。源码树按 Linux sysroot
布局组织：每个 daemon 各自目录带一份 `/usr/` 子树，共享配置放 `common/usr/`，
构建脚本把它们合并进同一个包。

## 功能

开机启动两个小型 systemd 服务：

1. **`sheng-fake-tablet-mode`** —— GNOME 自动旋转
   出厂 DTB 中物理 `gpio-keys` 霍尔传感器上报 `SW_TABLET_MODE=0`，导致 mutter
   锁定为「笔记本」姿态并永久关闭自动旋转。udev 规则把该开关对 libinput 隐藏，
   改由虚拟 `uinput` 设备上报 `SW_TABLET_MODE`。设备启动即处于笔记本态（OFF），
   之后每 200ms 扫描 `/proc` 寻找**用户**的 `gnome-shell`（通过 uid 范围与
   `--mode=gdm` 排除 GDM 登录界面），连续 25 个 tick（约 5 秒）后才将开关 0→1，
   解锁 mutter 面板方向管理；shell 退出时开关立即回落 OFF，因此会话重启总能产生
   一次新的 0→1 边沿。合盖/开盖通过 `org.gnome.Mutter.DisplayConfig`
   `PowerSaveMode` 控制息屏/亮屏。核心服务已被新实现替代，开盖盒盖仍然沿用旧实现。

2. **`sheng-power-key-toggle`** —— 电源键只切息屏，绝不睡眠
   挂起时若有 pending 唤醒会让 deep 睡眠中途 abort（`Wakeup pending. Abort CPU
   freeze`），屏幕黑死无法唤醒。本服务独占 grab 物理电源键，让 GNOME 永远看不到
   电源事件，每次按下只切换 `PowerSaveMode` 3↔0（3=息屏，0=亮屏），唤醒时注入
   `KEY_WAKEUP` 强制屏幕重绘；息屏同时通过 `loginctl lock-sessions` 锁定所有
   会话，下次亮屏直接落在 GNOME 锁屏界面。

因此 sheng 上「睡眠」永远只是「关背光且锁定屏幕」，suspend/hibernate 被整体禁用：

- `/usr/lib/systemd/sleep.conf.d/10-sheng-no-suspend.conf`：`AllowSuspend=no`、
  `AllowHibernation=no`、`AllowHybridSleep=no`、`AllowSuspendThenHibernate=no`
  （GNOME 不再出现「挂起」按钮，也不再自动睡眠）。
- `/usr/lib/systemd/logind.conf.d/10-sheng-gnome-fix.conf`：在 logind 层忽略
  电源键与全部合盖事件。
- GSettings override（`zz-sheng-gnome-fix.gschema.override`）：系统级设置
  `power-button-action=nothing`、`sleep-inactive-*=nothing`、`idle-dim=false`、
  `ambient-enabled=false`。

**自动锁屏不受影响**：锁屏由 idle 息屏驱动，与 suspend 无关。idle 超时后屏幕
熄灭并锁屏，按电源键唤醒回到锁屏界面。

## 文件

| 源码位置（sysroot）                    | 安装位置                                    |
| -------------------------------------- | ------------------------------------------- |
| `sheng-fake-tablet-mode/usr/libexec/`  | `/usr/libexec/sheng-fake-tablet-mode`       |
| `sheng-power-key-toggle/usr/libexec/`  | `/usr/libexec/sheng-power-key-toggle`       |
| `sheng-*/usr/lib/systemd/system/`      | `/usr/lib/systemd/system/*.service`         |
| `common/usr/lib/systemd/system-preset/`| `/usr/lib/systemd/system-preset/50-sheng-gnome-fix.preset` |
| `common/usr/lib/udev/rules.d/`         | `/usr/lib/udev/rules.d/80-sheng-gnome-fix.rules` |
| `common/usr/lib/systemd/logind.conf.d/`| `/usr/lib/systemd/logind.conf.d/10-sheng-gnome-fix.conf` |
| `common/usr/lib/systemd/sleep.conf.d/` | `/usr/lib/systemd/sleep.conf.d/10-sheng-no-suspend.conf` |
| `common/usr/lib/modules-load.d/`       | `/usr/lib/modules-load.d/sheng-gnome-fix.conf` |
| `common/usr/share/glib-2.0/schemas/`   | `/usr/share/glib-2.0/schemas/zz-sheng-gnome-fix.gschema.override` |

## 前置条件

- Python 3 及 `python3-evdev`，以及 systemd 与 udev。
- GNOME（daemon 通过每会话 D-Bus `DisplayConfig` 驱动 mutter）。

## 打包

预编译包以 GitHub Releases 发布；
[fedora-sheng](https://github.com/mumuxiao722/fedora-sheng) 的 rootfs 构建在
**desktop=GNOME** 时直接拉取发布的 RPM：

- `sheng-gnome-fix-1.0-1.noarch.rpm` – 不分版本的 noarch RPM（无 `%{dist}`
  后缀），任意 Fedora 版本均可安装。
- `sheng-gnome-fix_1.0_all.deb` – Debian/Ubuntu 包
  （`Depends: python3, python3-evdev, glib2.0-bin, systemd`）。

安装：

- Fedora：`sudo dnf install --nogpgcheck ./sheng-gnome-fix-1.0-1.noarch.rpm`
- Debian/Ubuntu：`sudo dpkg -i sheng-gnome-fix_1.0_all.deb`，再用
  `sudo apt-get install -f` 补全依赖。

装完需重启，udev 规则、systemd drop-in/preset 与两个单元才会生效。若已装过旧的
`sheng-tablet-mode`，请先卸载（`dnf remove sheng-tablet-mode` /
`dpkg -r sheng-tablet-mode`）。

## 构建

- `./build-deb.sh` – 任何有 `dpkg-deb` 的环境皆可（如 Termux），产物输出到
  当前目录。
- `./build-rpm.sh` – 在 Fedora 容器/chroot 中运行（需 `rpm-build`），例如设备上
  的 DroidSpaces Fedora-44 容器或对 Fedora 镜像 `podman run`；产物输出到当前目录。

## 相关项目

- [DotRedstone/nixos-sheng](https://github.com/DotRedstone/nixos-sheng) – 本包合盖息屏与电源键切换所参照的 NixOS 实现
- [fedora-sheng](https://github.com/mumuxiao722/fedora-sheng) – 使用本仓库发布的 RPM 的 Fedora 平板 rootfs 项目
- [CFM880/nabu-accelerometer](https://github.com/CFM880/nabu-accelerometer) – `sheng-fake-tablet-mode` 的 tablet-mode 核心移植来源

## 致谢

- **DotRedstone** – 感谢其 [nixos-sheng](https://github.com/DotRedstone/nixos-sheng)
  项目：原 `fake-tablet-mode` 与 `sheng-power-key-display-toggle` 服务是本包的基础。
  新的 `sheng-fake-tablet-mode` 用于替换其原有的 `fake-tablet-mode`，合盖/开盖息屏
  仍沿用其实现。
- **CFM880** – `sheng-fake-tablet-mode` 的桌面上报核心忠实移植自
  [nabu-accelerometer](https://github.com/CFM880/nabu-accelerometer) 的
  `userspace/nabu-tablet-mode.c`。

本包按 GPL-2.0-only 发布，详见 `LICENSE`。