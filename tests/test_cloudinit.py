import time
import argparse
import os.path
import shutil
import subprocess
import tempfile
import sys
import unittest

def fail(msg):
	print >> sys.stderr, msg
	sys.exit(1)

def copy_fs(source):
	tmpdir = tempfile.mkdtemp(prefix="cloudinit-")
	cmd = subprocess.Popen(["rsync", "-L", "-r", source+"/", tmpdir])
	cmd.wait()
	return tmpdir

def insert_binary(root, binary_path):
	shutil.copy2(binary_path, os.path.join(root, "bin", "coreos-cloudinit"))

def destroy_fs(root):
	shutil.rmtree(root, ignore_errors=True)

def nspawn(root):
	return subprocess.Popen(["systemd-nspawn", "--directory=%s" % root, "-b"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def find_child_pid(ppid):
	sp = subprocess.Popen(["ps", "-o", "pid", "--ppid", "%d" % ppid, "--noheaders"], stdout=subprocess.PIPE)
	sp.wait()
	(stdout, _) = sp.communicate()
	return int(stdout)

class SmokeTestCase(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		copy = copy_fs(ARGS.coreos_fs)
		insert_binary(copy, ARGS.binary)
		cls.root = copy

	def setUp(self):
		self.nspawn = nspawn(self.root)
		self.child_systemd_pid = find_child_pid(self.nspawn.pid)
		self.wait_for_active_unit('home.mount')
		self.prep_fs()
		self.wait_for_active_dbus_service('org.freedesktop.systemd1')

	@classmethod
	def tearDownClass(cls):
		if ARGS.cleanup:
			destroy_fs(cls.root)

	def tearDown(self):
		self.nspawn.terminate()
		self.nspawn.wait()

	def nspawn_cmd(self, cmd):
		p = subprocess.Popen(["nsenter", "-t", "%d" % self.child_systemd_pid, "-m", "-u", "-i", "-n", "-p", "--"] + cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		retcode = p.wait()
		stdout, stderr = p.communicate()
		return retcode, stdout, stderr

	def prep_fs(self):
		cmds = [
			"mkdir -m 0700 /home/core/.ssh",
			"mkdir -m 0700 /home/core/.ssh/authorized_keys.d",
			"chown -R core:core /home/core",
		]

		for cmd in cmds:
			self.nspawn_cmd(cmd)

	def wait_for_active_unit(self, unit):
		for i in xrange(10):
			retcode, stdout, _ = self.nspawn_cmd("systemctl status %s" % unit)
			if retcode == 0 and "Active: active" in stdout:
				return
			else:
				time.sleep(1)

		self.fail("Took too long for unit %s to become active" % unit)

	def wait_for_file_exist(self, filename):
		for i in xrange(10):
			retcode, _, _ = self.nspawn_cmd("ls %s" % filename)
			if retcode == 0:
				return
			else:
				time.sleep(1)

		self.fail("Took too long for file %s to appear" % filename)

	def wait_for_active_dbus_service(self, service):
		for i in xrange(10):
			retcode, stdout, stderr = self.nspawn_cmd("dbus-send --system --dest=org.freedesktop.DBus --type=method_call --print-reply /org/freedesktop/DBus org.freedesktop.DBus.ListNames")
			if retcode == 0 and service in stdout:
				return
			else:
				time.sleep(1)

		self.fail("Took too long for dbus service %s to become active" % service)

	def testEtcdURL(self):
		config = """#cloud-config
coreos:
    etcd:
        discovery_url: https://discovery.etcd.io/827c73219eeb2fa5530027c37bf18877
"""
		with open(os.path.join(self.root, "cloud-config"), "w") as fap:
			fap.write(config)

		self.nspawn_cmd("/bin/coreos-cloudinit --from-file /cloud-config")

		retcode, stdout, _ = self.nspawn_cmd("cat /var/run/etcd/bootstrap.disco")
		self.assertEqual(retcode, 0)
		self.assertEqual(stdout, "https://discovery.etcd.io/827c73219eeb2fa5530027c37bf18877")

	def testSSHAuthorizedKeys(self):
		config = """#cloud-config
ssh_authorized_keys:
    - ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC5LaGMGRqZEEvOhHlIEiQgdMJIQ9Qe8L/XSz06GqzcESbEnYLIXar2nou4eW4AGMVC1V0BrcWWnSTxM1/dWeCLOUt5NulKAjtdBUZGhCT83nbimSzbmx3/q2y5bCiS4Zr8ZjYFbi1eLvye2jKPE4xo7cvIfDKc0ztQ9kU7JknUdKNZo3RKXr5EPhJ5UZ8Ff15CI9+hDSvdPwer+HNnEt/psRVC+s29EwNGwUXD4IYqrk3X4ew0YAl/oULHM4cctoBW9GM+kAl40rOuIARlKfe4UdCgDMHYA/whi7Us+cPNgPit9IVJVBU4eo/cF5molD2l+PMSntypuv79obu8sA1H cloudinit test key
"""
		with open(os.path.join(self.root, "cloud-config"), "w") as fap:
			fap.write(config)

		retcode, stdout, _ = self.nspawn_cmd("/bin/coreos-cloudinit --from-file /cloud-config")
		self.assertEqual(retcode, 0)

		retcode, stdout, _ = self.nspawn_cmd("update-ssh-keys -l")
		self.assertEqual(retcode, 0)
		expect = "All keys for core:\ncoreos-init:\n2048 fb:24:4b:5e:dd:23:02:62:67:ab:40:f7:02:51:d9:31  cloudinit test key (RSA)\nUpdated /home/core/.ssh/authorized_keys\n"
		self.assertEqual(stdout, expect)

	def testScriptExecution(self):
		config = """#!/bin/bash
touch /tmp/smoketesting
"""
		retcode, _, _ = self.nspawn_cmd("ls /tmp/smoketesting")
		self.assertEqual(retcode, 2)

		with open(os.path.join(self.root, "cloud-config"), "w") as fap:
			fap.write(config)

		retcode, _, stderr = self.nspawn_cmd("/bin/coreos-cloudinit --from-file /cloud-config")
		self.assertEqual(retcode, 0, stderr)

		self.wait_for_file_exist("/tmp/smoketesting")

def suite():
    suite = unittest.TestSuite()
    for test_class in (SmokeTestCase, ):
        tests = unittest.defaultTestLoader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="coreos-cloudinit smoketests")
	parser.add_argument("--coreos-fs", default="/mnt/coreos",
						help="Directory containing coreos filesystem")
	parser.add_argument("--binary", default="bin/coreos-cloudinit",
						help="Location of coreos-cloudinit binary to use in smoke-testing")
	parser.add_argument("--no-cleanup", default=True, action="store_false", dest="cleanup",
						help="Prevent cleanup of local artifacts after tests complete")

	global ARGS
	ARGS = parser.parse_args()

	unittest.TextTestRunner(verbosity=2).run(suite())
