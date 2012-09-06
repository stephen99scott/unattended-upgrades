#!/usr/bin/python3
"""Test unattended_upgrades against the real archive in a chroot.

Note that this test is not run by the makefile in this folder, as it requires
network access, and it fails in some situations (unclear which).
"""

import apt
import apt_pkg
import glob
import logging
import os
import re
import unittest

import unattended_upgrade


apt_pkg.config.set("APT::Architecture", "amd64")


class MockOptions():
    def __init__(self, debug=True, dry_run=True):
        self.debug = debug
        self.dry_run = dry_run
        self.minimal_upgrade_steps = False


class TestAgainstRealArchive(unittest.TestCase):

    def setUp(self):
        for f in glob.glob("./aptroot/var/log/*"):
            if os.path.isfile(f):
                os.remove(f)

    def test_against_real_archive(self):
        # get a lucid based cache (test good for 5y)
        cache = apt.Cache(rootdir="./aptroot")
        cache.update()
        del cache
        # create mock options
        options = MockOptions(debug=True)
        # ensure apt does not do any post-invoke stuff that fails
        # (because we are not root)
        apt_pkg.config.clear("DPkg::Post-Invoke")
        # run unattended-upgrades against fake system
        logdir = os.path.abspath("./aptroot/var/log/")
        logfile = os.path.join(logdir, "unattended-upgrades.log")
        apt_pkg.config.set("APT::UnattendedUpgrades::LogDir", logdir)
        unattended_upgrade.DISTRO_CODENAME = "lucid"
        res = unattended_upgrade.main(options, os.path.abspath("./aptroot"))
        logging.debug(res)
        # check if the log file exists
        self.assertTrue(os.path.exists(logfile))
        with open(logfile) as fp:
            log = fp.read()
        # check that stuff worked
        self.assertFalse(" ERROR " in log, log)
        # check if we actually have the expected ugprade in it
        self.assertTrue(
            re.search("INFO Packages that are upgraded:.*awstats", log))
        # apt-doc has a higher version in -updates than in -security
        # and no other dependencies so its a perfect test
        self.assertTrue(
            re.search("INFO Packages that are upgraded:.*apt-doc", log))
        self.assertFalse(
            re.search("INFO Packages that are upgraded:.*ant-doc", log))
        self.assertTrue(
            re.search("DEBUG skipping blacklisted package 'ant-doc'", log))

if __name__ == "__main__":
    unittest.main()

