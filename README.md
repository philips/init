System Initialization for CoreOS
================================

CoreOS uses systemd for init and process management. This repo is
divided into three collections of files:

  * configs: Customized daemon configuration files, usually installed
    into ``/etc`` but really the sky is the limit there.
  * scripts: Helper scripts for init and service startup. These are
    generally to be used as systemd oneshot services and installed
    into ``/usr/lib/coreos``.
  * systemd: Unit files for mount points, our helper scripts, or other
    services that doen't install their own unit files. There is a top
    level ``coreos-startup.target`` which depends on everything that
    should be enabled by default on CoreOS.
    See [Ordering](#ordering) for details.

The coreos-base/coreos-init ebuild handles the install process.

Important Steps
---------------

A few notes on things that must happen which are unique to Core OS.

  * resize ``state``: Support easy VM growth by checking
    if there is unused space at the end of the disk and expanding the
    filesystem to use it.
  * mount ``/``: This directory can be completely empty.
  * initialize ``/``: The ``/`` partition can be completely formatted by the
    user. Run systemd-tmpfiles to set everything up into a know state.
  * mount ``/usr``: The entire distro lives in this directory.
  * mount ``/usr/share/oem``: If an OEM is avialable on disk make sure it gets
    mounted here.
  * generate ssh keys: The stock sshd units do not handle this so
    we need to.
