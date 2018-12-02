#!/usr/bin/env python3

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Mock Grbl

Mock Grbl implementation for testing Calabó.
"""

import re
import sys
import time
import serial
import argparse
import tempfile
from subprocess import Popen, PIPE, CalledProcessError



MAX_SOCAT_PARSE_LINES = 10
DEFAULT_READ_LINE_TIMEOUT = 1000
DEFAULT_READ_LINE_INTERVAL = 0.1



class MockGrblSocketError(Exception):
    pass



class MockGrbl():
    def _open_serial_device(self):
        cmd = ["socat", "-t", "0", "-d", "-d", "pty,raw,echo=1", "pty,raw,echo=1"]

        process = Popen(cmd, stderr=PIPE, universal_newlines=True)
        re_dev = re.compile(r"(/dev/pts/\d+)")
        dev_list = []
        i = 0
        while True:
            i += 1
            if i > MAX_SOCAT_PARSE_LINES:
                raise MockGrblSocketError(
                    "Could not find device names in `socat` output (max lines)")

            line = process.stderr.readline()
            match = re_dev.search(line)
            if not match:
                continue

            dev_list.append(match.group(1))
            if len(dev_list) == 2:
                break

        self._socat_process = process
        (self._socat_dev_local, self._socat_dev_remote) = dev_list

        self._conn = serial.Serial(self._socat_dev_local)


    def _close_serial_device(self):
        self._socat_process.terminate()
        self._socat_process.wait()


    def __init__(self, serial_timeout=2):
        self._socat_process = None
        self._socat_dev_local = None
        self._socat_dev_remote = None
        self._conn = None
        self._serial_timeout = serial_timeout


    def __enter__(self):
        self._open_serial_device()
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        self._conn.close()
        self._close_serial_device()


    def write_line(self, line):
        line = "%s\n" % line
        self._conn.write(line.encode("utf-8"))


    def read_line(self, timeout=None, interval=None):
        if timeout is None:
            timeout = DEFAULT_READ_LINE_TIMEOUT
        if interval is None:
            interval = DEFAULT_READ_LINE_INTERVAL

        elapsed = 0
        while True:
            while self._conn.inWaiting():
                return self._conn.readline().decode("utf-8").strip()
            time.sleep(0.1)
            elapsed += interval
            if elapsed >= timeout:
                break


    def echo_line(self, line):
        self.write_line(line)


    def process_line(self, line):
        self.echo_line(line)


    def run(self, max_time=100):
        while True:
            line = self.read_line()
            self.process_line(line)
