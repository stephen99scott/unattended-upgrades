#!/usr/bin/python3

import logging
import os
import os.path
import shutil
import subprocess
import tempfile
import unittest

import apt

import unattended_upgrade


class MockOptions(object):
    debug = True
    verbose = False
    download_only = False
    dry_run = False
    apt_debug = False
    minimal_upgrade_steps = True


class TestBase(unittest.TestCase):
    def setUpClass():
        # XXX: find a more elegant way
        pkgdir = os.path.join(os.path.dirname(__file__), "packages")
        subprocess.check_call(["make", "-C", pkgdir])

    def setUp(self):
        super(TestBase, self).setUp()
        self.tempdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tempdir)
        self.testdir = os.path.dirname(__file__)
        # ensure custom logging gets reset (XXX: does this work?)
        self.addCleanup(logging.shutdown)
        logging.root.handlers = []
        # XXX: workaround for most tests assuming to run inside the "test"
        # dir
        os.chdir(self.testdir)
        # fake the lock file
        unattended_upgrade.LOCK_FILE = os.path.join(self.tempdir, "u-u.lock")
        # XXX: some test monkey patch this without reset
        unattended_upgrade.init_distro_info()
        # reset apt config
        apt.apt_pkg.init_config()
