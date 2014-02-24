# coreos-init

CoreOS allows a user to customize EC2 instances by providing either an executable script or a cloud-config document as instance user-data. See below to learn how to use these features.

## cloud-config

Only a subset of [cloud-config functionality][cloud-config] is implemented. A set of custom parameters were added to the cloud-config format that are specific to CoreOS.

[cloud-config]: http://cloudinit.readthedocs.org/en/latest/topics/format.html#cloud-config-data

### Supported cloud-config Parameters

#### users

The only supported user that may be modified is `core`. No new users may be added. Modification of the `core` user is limited to the addition of authorized public SSH keys.

### Custom cloud-config Parameters

#### coreos.etcd.discovery-url

The value of `coreos.etcd.discovery-url` will be used to discover the instance's etcd peers using the [etcd discovery protocol][disco-proto]. Usage of the [public discovery service][disco-service] is encouraged.

[disco-proto]: https://github.com/coreos/etcd/blob/master/Documentation/discovery-protocol.md
[disco-service]: http://discovery.etcd.io


## user-data Script

Simply set your user-data to a script where the first line is a shebang:

```
#!/bin/bash

echo 'Hello, world!'
```

## Examples

### Inject an SSH key bootstrap etcd using cloud-config

```
#cloud-config

coreos:
	etcd:
		discovery_url: https://discovery.etcd.io/827c73219eeb2fa5530027c37bf18877

ssh_authorized_keys:
  - ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC0g+ZTxC7weoIJLUafOgrm+h...
```

