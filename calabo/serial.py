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

import io
import time
import serial
import logging



DEFAULT_READ_LINE_TIMEOUT = 1.0
DEFAULT_READ_LINE_INTERVAL = 0.1
DEFAULT_BAUD_RATE = 115200
DEFAULT_EOL = "\n"



LOG = logging.getLogger("calabo.serial")



class Serial():
    def __init__(self, device, name=None, write_eol=None):
        self._device = device
        self._name = name or device
        self._conn = None
        self._write_eol = write_eol or DEFAULT_EOL


    def __enter__(self):
        baud = DEFAULT_BAUD_RATE
        if hasattr(self._device, "__call__"):
            self._device = self._device()

        self._ser = serial.Serial(self._device, baud)
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        self._ser.close()


    def write_line(self, line):
        LOG.debug("Serial write %s %s", self._name, repr(line))
        self._ser.write((line + self._write_eol).encode("utf-8"))


    def read_line(self, timeout=None, interval=None):
        if timeout is None:
            timeout = DEFAULT_READ_LINE_TIMEOUT
        if interval is None:
            interval = DEFAULT_READ_LINE_INTERVAL

        elapsed = 0
        LOG.debug("Serial wait %s", self._name)
        while True:
            if self._ser.in_waiting:
                line = self._ser.readline().decode("utf-8").strip()
                LOG.debug("Serial read %s %s", self._name, repr(line))
                return line

            time.sleep(interval)
            elapsed += interval

            if timeout is not False and elapsed >= timeout:
                break

        LOG.debug("Serial timeout %s %s", self._name, timeout)
        return None


    def __repr__(self):  # pragma: no cover
        return "<Calabo Serial. Device: %s>" % repr(self._device)
