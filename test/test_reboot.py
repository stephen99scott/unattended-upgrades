#!/usr/bin/python3

import datetime
import logging
import os
import unittest
import subprocess

import apt_pkg
apt_pkg.config.set("Dir", os.path.join(os.path.dirname(__file__), "aptroot"))

from mock import (
    patch,
)

import unattended_upgrade
from test.test_base import TestBase


class RebootTestCase(TestBase):

    def setUp(self):
        TestBase.setUp(self)
        # create reboot required file
        REBOOT_REQUIRED_FILE = os.path.join(self.tempdir, "reboot-required")
        with open(REBOOT_REQUIRED_FILE, "w"):
            pass
        self.reboot_required_file = unattended_upgrade.REBOOT_REQUIRED_FILE
        unattended_upgrade.REBOOT_REQUIRED_FILE = REBOOT_REQUIRED_FILE
        # enable automatic-reboot
        apt_pkg.config.set("Unattended-Upgrade::Automatic-Reboot", "1")
        apt_pkg.config.set(
            "Unattended-Upgrade::Automatic-Reboot-WithUsers", "1")

    def tearDown(self):
        unattended_upgrade.REBOOT_REQUIRED_FILE = self.reboot_required_file

    @patch("subprocess.check_output")
    def test_no_reboot_done_because_no_stamp(self, mock_call):
        unattended_upgrade.REBOOT_REQUIRED_FILE = "/no/such/file/or/directory"
        unattended_upgrade.reboot_if_requested_and_needed()
        self.assertEqual(mock_call.called, False)

    @patch("subprocess.check_output")
    def test_no_reboot_done_because_no_option(self, mock_call):
        apt_pkg.config.set("Unattended-Upgrade::Automatic-Reboot", "0")
        unattended_upgrade.reboot_if_requested_and_needed()
        self.assertEqual(mock_call.called, False)

    @patch("subprocess.check_output", return_value="some shutdown msg")
    @patch("unattended_upgrade.logged_in_users", return_value={})
    def test_reboot_now(self, mock_user, mock_call):
        unattended_upgrade.reboot_if_requested_and_needed()
        mock_call.assert_called_with(["/sbin/shutdown", "-r", "now"],
                                     stderr=subprocess.STDOUT)

    @patch("subprocess.check_output", return_value="some shutdown msg")
    @patch("unattended_upgrade.logged_in_users", return_value={})
    def test_reboot_time(self, mock_users, mock_call):
        apt_pkg.config.set(
            "Unattended-Upgrade::Automatic-Reboot-Time", "03:00")
        unattended_upgrade.reboot_if_requested_and_needed()
        mock_call.assert_called_with(["/sbin/shutdown", "-r", "03:00"],
                                     stderr=subprocess.STDOUT)

    @patch("subprocess.check_output", return_value="some shutdown msg")
    @patch("unattended_upgrade.logged_in_users", return_value={})
    def test_reboot_withoutusers(self, mock_users, mock_call):
        """Ensure that a reboot happens when no users are logged in"""
        apt_pkg.config.set(
            "Unattended-Upgrade::Automatic-Reboot-WithUsers", "0")
        apt_pkg.config.set(
            "Unattended-Upgrade::Automatic-Reboot-Time", "04:00")
        # some pgm that allways output nothing
        unattended_upgrade.reboot_if_requested_and_needed()
        mock_call.assert_called_with(["/sbin/shutdown", "-r", "04:00"],
                                     stderr=subprocess.STDOUT)

    @patch("subprocess.check_output")
    @patch("unattended_upgrade.logged_in_users", return_value={'user'})
    def test_reboot_withusers(self, mock_users, mock_call):
        """Ensure that a reboot does not happen if a user is logged in"""
        apt_pkg.config.set(
            "Unattended-Upgrade::Automatic-Reboot-WithUsers", "0")
        # some pgm that allways output a word
        unattended_upgrade.reboot_if_requested_and_needed()
        self.assertEqual(
            mock_call.called, False,
            "Called '%s' when nothing should have "
            "happen" % mock_call.call_args_list)

    @patch("subprocess.call")
    def test_logged_in_users(self, mock_call):
        # some pgm that allways output a word
        unattended_upgrade.USERS = ["/bin/date", "+%Y %Y %Y"]
        users = unattended_upgrade.logged_in_users()
        today = datetime.date.today()
        self.assertEqual(users, set([today.strftime("%Y")]))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
