### Smoke-testing coreos-cloudinit

The `test_cloudinit.py` script provides a suite of functional tests for the `coreos-cloudinit` tool.
The script is intended to be given a clean coreos filesystem, which it will copy as-needed to ensure clean runs of its tests.

The easiest way to make a coreos filesystem available to `test_cloudinit.py` is to download the latest pxe image from our archive.

```
$ wget http://storage.core-os.net/coreos/amd64-generic/dev-channel/coreos_production_pxe_image.cpio.gz
```

Once downloaded, unpack it with a command like this:

```
$ cat coreos_production_pxe_image.cpio.gz | gzip -d - | cpio -idv
```

And mount it somewhere:

```
$ sudo mount -t squashfs newroot.squashfs /mnt/coreos
```

Assuming you've already built coreos-cloudinit, you're ready to run the tests:

```
$ sudo python tests/test_cloudinit.py --coreos-fs /mnt/coreos/ --binary bin/coreos-cloudinit
```