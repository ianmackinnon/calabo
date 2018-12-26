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

import re
import logging
from collections import defaultdict

from calabo.serial import Serial
from calabo.grbl_settings import SETTINGS, SETTINGS_KEYS, \
    setting_from_string, setting_to_string



HANDLERS = []



LOG = logging.getLogger("calabo.grbl")



class ResponseException(Exception):
    pass

class SettingsException(Exception):
    pass



def handle(pattern):
    global HANDLERS

    regex = re.compile(pattern)

    def d(f):
        HANDLERS.append((regex, f))
        return f

    return d



class Grbl():
    """\
Grbl interface object.
"""

    def __init__(self, device):
        self._serial = Serial(device, name="ctrl", write_eol="\n")
        self._state = None
        self._homed = None
        self._unlocked = None
        self._settings = {}
        self._last_response = None


    def __enter__(self):
        self._serial.__enter__()

        result = self._step()
        if self._state != "ready":
            raise ResponseException("No salutation received")

        # Catch homing enabled message if necessary:
        self._step()

        self._read_settings()
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        self._serial.__exit__(exception_type, exception_value, traceback)


    def __repr__(self):  # pragma: no cover
        return str(self._serial)


    @handle(r"^Grbl .* for help\]$")
    def _boot(self):
        self._homed = False
        self._set_state("ready")


    @handle(r"^\[MSG:.*]$")
    def _msg(self):
        pass


    @handle(r"^ok$")
    def _ok(self):
        if self._state != "expect_ok":
            raise ResponseException(
                "Unexpected response received in state %s: 'ok'.",
                self._state)
        self._set_state("ready")


    @handle(r"^error:(\d+)$")
    def _error(self, key):
        key = int(key)

        if key == 10:
            raise ValueError("Soft limits cannot be enabled without homing also enabled.")


    @handle(r"^\$(\d+)=(.+)$")
    def _setting(self, key, value_str):
        key = int(key)
        try:
            name = SETTINGS[key]["name"]
        except IndexError:
            raise SettingsException(
                "Unknown settings key %d with value %s" % (key, value_str))

        value = setting_from_string(key, value_str)
        self.setting(key, value, from_device=True)


    def _step(self):
        while True:
            line = self._serial.read_line()
            if line is None:
                return None

            self._last_response = line

            if not line:
                continue

            for (regex, f) in HANDLERS:
                match = regex.match(line)
                if match:
                    f(self, *match.groups())
                    break
            else:
                raise ResponseException("Unexpected response: %s" % repr(line))

            if self._state in ("ready", ):
                break


    def _set_state(self, state):
        self._state = state
        LOG.debug("set state %s" % self._state)


    def setting(self, key, value=None, from_device=None):
        """
        Get or set a settings option.
        `key` may be a name or integer.
        Set `from_device` to True when reading initial values from device.
        """

        try:
            key = int(key)
        except ValueError:
            pass

        try:

            if isinstance(key, int):
                name = SETTINGS[key]["name"]
            else:
                name = key
                key = SETTINGS_KEYS[name]
        except IndexError:
            raise SettingsException(
                "Unknown settings key %d with value %s" % (key, value))

        if value is None:
            try:
                return self._settings[key]
            except IndexError:
                raise SettingsException(
                    "Requesting settings key %d before initial values have "
                    "been read from device" % (key))

        if not from_device:
            value_str = setting_to_string(key, value)
            self._serial.write_line("$%d=%s" % (key, value_str))
            self._set_state("expect_ok")
            self._step()

        self._settings[key] = value

        if from_device:
            if self._state != "read_settings":
                raise ResponseException(
                    "Unexpected setting value received. %s %s" %
                    (self._state, self._last_response))
            LOG.debug("Setting received from device %d (%d/%d) %s %s",
                      key, len(self._settings), len(SETTINGS), name, value)
            if len(self._settings) == len(SETTINGS):
                self._set_state("expect_ok")
        else:
            LOG.debug("Set setting %d %s %s", key, name, value)

        return None


    def _read_settings(self):
        self._settings = {}
        self._serial.write_line("$$")
        self._set_state("read_settings")
        return self._step()
