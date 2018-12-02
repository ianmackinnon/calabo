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

import time
import serial



DEFAULT_READ_LINE_TIMEOUT = 1000
DEFAULT_READ_LINE_INTERVAL = 0.1



class Serial():
    def __init__(self, device):
        self._device = device
        self._conn = None


    def __enter__(self):
        self._conn = serial.Serial(self._device)
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        self._conn.close()


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
