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
import errno
import logging
from subprocess import Popen, PIPE

# Calabo imports
sys.path.append("../")
from calabo.serial import Serial, ConnectionClosedException
from calabo.grbl_settings import SETTINGS, setting_index, \
    setting_from_string, setting_to_string



MAX_SOCAT_PARSE_LINES = 10



LOG = logging.getLogger("mock_grbl")



class MockGrblSocketError(Exception):
    pass



class SocatStream():
    def __init__(self):
        self._proc = None
        self._dev_local = None
        self._dev_remote = None


    def __enter__(self):
        self.start()
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()


    def start(self):
        cmd = ["socat", "-t", "0", "-d", "-d", "pty,raw,echo=1", "pty,raw,echo=1"]

        self._proc = Popen(cmd, stderr=PIPE, universal_newlines=True)
        re_dev = re.compile(r"(/dev/pts/\d+)")
        dev_list = []
        i = 0
        while True:  # pragma: no cover
            i += 1
            if i > MAX_SOCAT_PARSE_LINES:
                raise MockGrblSocketError(
                    "Could not find device names in `socat` output (max lines)")

            line = self._proc.stderr.readline()
            match = re_dev.search(line)
            if not match:
                continue

            dev_list.append(match.group(1))
            if len(dev_list) == 2:
                break

        (self._dev_local, self._dev_remote) = dev_list


    def stop(self):
        self._proc.terminate()
        self._proc.wait()



class MockGrbl():
    """\
Mock Grbl hardware object that provides a serial address for connection.
"""

    def __init__(self, options=None):

        self._socat_stream = None
        self._serial = None
        self._settings = {k: v["default"] for k, v in SETTINGS.items()}

        self._state = None
        self._locked = None
        self._feed_rate = None

        if options and "settings" in options:
            self._settings.update(options["settings"])

    def __enter__(self):
        self._socat_stream = SocatStream()
        self._socat_stream.__enter__()

        self._serial = Serial(
            self._socat_stream._dev_local,
            name="mock", write_eol="\r\n",
            realtime_hooks={
                "?": self.write_state,
            }
        )
        self._serial.__enter__()

        return self


    def __exit__(self, exception_type, exception_value, traceback):
        self._serial.__exit__(exception_type, exception_value, traceback)
        self._socat_stream.__exit__(exception_type, exception_value, traceback)


    def reset(self):
        self._state = "Idle"
        self._locked = False
        self._feed_rate = None

        if self._settings[setting_index("homing-cycle-enable")]:
            self._state = "Alarm"
            self._locked = True

        self.salutation()


    def write_calibration(self):
        for key, value in self._settings.items():
            value_str = setting_to_string(key, value)
            self._serial.write_line("$%d=%s" % (key, value_str))
        self._serial.write_line("ok")


    def write_state(self):
        self._serial.write_line("<%s>" % self._state)


    def set_setting(self, key, value_str):
        value = setting_from_string(key, value_str)

        # Do not allow soft limits to be enabled if homing is disabled
        if key == 20 and value and not self._settings[22]:
            self._serial.write_line("error:10")
            return

        # Disable soft-limits when homing is disabled
        if key == 22 and not value and self._settings[20]:
            self._settings[20] = False

        self._settings[key] = value
        self._serial.write_line("ok")


    def probe(self, z_to):
        if self._feed_rate is None:
            self._serial.write_line("error:22")
            return

        time.sleep(10)
        self._serial.write_line("ALARM:5")
        self._serial.write_line("[PRB:0.0000,0.0000,0.0000:0]")
        self._serial.write_line("ok")


    def move(self, x):
        if self._locked:
            self._serial.write_line("error:9")
            return

        self._serial.write_line("ok")


    def mill(self, x):
        if self._feed_rate is None:
            self._serial.write_line("error:22")
            return

        self._serial.write_line("ok")


    def process_line(self, line):

        if hasattr(line, "__call__"):
            line()
            return

        if line == "$$":
            self.write_calibration()
            return

        match = re.compile(r"^\$(\d+)=(.+)$").match(line)
        if match:
            key, value = match.groups()
            key = int(key)
            self.set_setting(key, value)
            return

        match = re.compile(r"^G0 X([\d.]+)$").match(line)
        if match:
            (x, ) = match.groups()
            self.move(x)
            return

        match = re.compile(r"^G1 X([\d.]+)$").match(line)
        if match:
            (x, ) = match.groups()
            self.mill(x)
            return

        match = re.compile(r"^G38.2 Z(-?[\d.]+)$").match(line)
        if match:
            (z_to, ) = match.groups()
            self.probe(z_to)
            return

        self._serial.write_line(
            "{MockGrbl unexpected request:%s}" % repr(line))


    def salutation(self):
        self._serial.write_line("")
        self._serial.write_line("Grbl 1.1f ['$' for help]")
        if self._settings[setting_index("homing-cycle-enable")]:
            self._serial.write_line("[MSG:'$H'|'$X' to unlock]")
        else:
            self._locked = False


    def run(self):
        while True:
            try:
                line = self._serial.read_line(timeout=False)
            except ConnectionClosedException:  # pragma: no cover
                break
            self.process_line(line)
