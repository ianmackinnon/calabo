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

import io
import re
import sys
import time
import errno
import logging
import traceback
from subprocess import Popen, PIPE

# Calabo imports
sys.path.append("../")
from calabo.serial import Serial, ConnectionClosedException
from calabo.grbl_settings import MM_TO_INCHES, SETTINGS, setting_index, \
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
        self._wco = None

        self._read_inches = None

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
        self._wco = None

        if self._settings[setting_index("homing-cycle-enable")]:
            self._state = "Alarm"
            self._locked = True

        self.salutation()


    def write_calibration(self):
        for key, value in self._settings.items():
            value_str = setting_to_string(key, value)
            self._serial.write_line("$%d=%s" % (key, value_str))
        self._serial.write_line("ok")


    def report_distance(self, value):
        """
        Return `value` as a string, in the units specified by setting 13.
        """
        if self._settings[setting_index("report-in-inches")]:
            value /= MM_TO_INCHES
        return "%.4f" % value


    def read_distance(self, text):
        """
        Read `text` as a float, in the units specified by G20/G21.
        """

        value = float(text)
        if self._read_inches:
            value *= MM_TO_INCHES
        return value


    def write_state(self):
        parts = [self._state]

        if self._wco:
            (x, y, z) = (-self._wco["x"], -self._wco["y"], -self._wco["z"])
        else:
            (x, y, z) = (0, 0, 0)

        parts.append("WCO:%s" % ",".join([self.report_distance(v) for v in (x, y, z)]))

        self._serial.write_line("<%s>" % "|".join(parts))


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


    def unlock(self):
        self._locked = False
        self._state = "Idle"

        self.write_message("Caution: Unlocked")
        self._serial.write_line("ok")


    def probe(self, z_to):
        if self._feed_rate is None:
            self._serial.write_line("error:22")
            return

        raise NotImplementedError()
        # time.sleep(10)
        # self._serial.write_line("ALARM:5")
        # self._serial.write_line("[PRB:0.0000,0.0000,0.0000:0]")
        # self._serial.write_line("ok")


    def set_wco(self, x, y, z):
        """
        Set WCO in millimeters.
        """

        if self._locked:
            self._serial.write_line("error:9")
            return

        self._wco = {
            "x": x,
            "y": y,
            "z": z,
        }
        self._serial.write_line("ok")


    def clear_wco(self):
        if self._locked:
            self._serial.write_line("error:9")
            return

        self._wco = False
        self._serial.write_line("ok")


    def read_inches(self, value):
        self._read_inches = value
        self._serial.write_line("ok")


    def clear_wco(self):
        if self._locked:
            self._serial.write_line("error:9")
            return

        self._wco = False
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

        match = re.compile(r"^\$X$").match(line)
        if match:
            self.unlock()
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

        match = re.compile(r"^G92 X(-?[\d.]+) Y(-?[\d.]+) Z(-?[\d.]+)$").match(line)
        if match:
            (x, y, z) = (self.read_distance(v) for v in match.groups())
            self.set_wco(x, y, z)
            return

        match = re.compile(r"^G92.1$").match(line)
        if match:
            self.clear_wco()
            return

        match = re.compile(r"^G20$").match(line)
        if match:
            self.read_inches(True)
            return

        match = re.compile(r"^G21$").match(line)
        if match:
            self.read_inches(False)
            return

        self._serial.write_line(
            "{MockGrbl unexpected request:%s}" % repr(line))


    def write_message(self, message):
        self._serial.write_line("[MSG:%s]" % message)


    def salutation(self):
        self._serial.write_line("")
        self._serial.write_line("Grbl 1.1f ['$' for help]")
        if self._settings[setting_index("homing-cycle-enable")]:
            self.write_message("'$H'|'$X' to unlock")
        else:
            self._locked = False


    def run(self):
        try:
            while True:
                try:
                    line = self._serial.read_line(timeout=False)
                except ConnectionClosedException:  # pragma: no cover
                    break
                self.process_line(line)
        except Exception as e:  # pragma: no cover
            LOG.error("Unhandled exception in `MockGrbl.run`. Exiting.")
            stream = io.StringIO()
            traceback.print_exc(file=stream)
            LOG.error("\n" + stream.getvalue())
            LOG.error(e)
            raise
