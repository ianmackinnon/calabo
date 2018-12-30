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
import time
import logging
from collections import defaultdict

import calabo.grbl_exc
from calabo.serial import Serial
from calabo.grbl_settings import STATES, SETTINGS, SETTINGS_KEYS, \
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
        if hasattr(device, "get"):
            device_address = device["address"]
            self._reset_device = device["reset"]
        else:
            device_address = device
            self._reset_device = None

        self._serial = Serial(device_address, name="ctrl", write_eol="\n")
        self._last_response = None

        self._settings = {}
        self._state = None
        self._unlocked = None
        self._wco = None


    def __enter__(self):
        self._serial.__enter__()
        self.initialize()
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        self._serial.__exit__(exception_type, exception_value, traceback)


    def initialize(self):
        if self._reset_device:
            self._reset_device()
        else:
            self._serial._ser.dtr = False
            time.sleep(0.1)
            self._serial._ser.dtr = True

        time.sleep(0.1)
        result = self._step()
        if self._state != "ready":
            raise ResponseException("No salutation received")

        self._read_settings()
        self.read_state()  # WCO should be sent on first request
        assert self._wco is not None
        self.read_state()  # Ov should be sent on second request


    def reset(self):
        self._last_response = None

        self._settings = {}
        self._state = None
        self._unlocked = None
        self._wco = None

        self.initialize()


    def __repr__(self):  # pragma: no cover
        return str(self._serial)


    @handle(r"^Grbl .* for help\]$")
    def _boot(self):
        self._set_state("ready")


    @handle(r"^\[MSG:(.*)]$")
    def _msg(self, message):
        if message == "'$H'|'$X' to unlock":
            self._unlocked = False
        elif message == "Caution: Unlocked":
            self._unlocked = True


    @handle(r"^\[PRB:([\d.]),([\d.]),([\d.]),([01])]$")
    def _prb(self, x, y, z, status):
        x = float(x)
        y = float(y)
        z = float(z)
        status = bool(int(status))


    @handle(r"^ok$")
    def _ok(self):
        if self._state != "expect_ok":
            raise ResponseException(
                "Unexpected response received in state %s: 'ok'." %
                self._state)
        self._set_state("ready")


    @handle(r"^error:(\d+)$")
    def _error(self, key):
        key = int(key)

        for k, v in calabo.grbl_exc.exc.items():
            if k == key:
                raise v["class"](v["text"])

        raise ResponseException(
            "Unexpected error response '%s' received in state %s: 'ok'." % (
                key, self._state))


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


    def _read_settings(self):
        self._settings = {}
        self._serial.write_line("$$")
        self._set_state("read_settings")
        return self._step()


    def _parse_state(self, text):
        if not text.startswith("<"):
            raise ResponseException("State does not start with <: %s" % repr(text))
        if not text.endswith(">"):
            raise ResponseException("State does not end with >: %s" % repr(text))
        text = text[1:-1]

        parts = text.split("|")

        state = parts[0]
        _substate = None
        if ":" in state:
            (state, _substate) = state.split(":", 1)

        if state not in STATES:
            raise ResponseException("Unrecognised state %s in text %s" % (
                repr(state), repr(text)))

        re_wco = re.compile(r"^WCO:([\d.]+),([\d.]+),([\d.]+)$")

        for part in parts:
            match = re_wco.match(part)
            if match:
                (x, y, z) = (float(v) for v in match.groups())
                if x or y or z:
                    self._wco = {
                        "x": x,
                        "y": y,
                        "z": z,
                    }
                else:
                    self._wco = False
                continue

        return state


    def read_state(self):
        self._serial._ser.write(("?").encode("utf-8"))
        response = ""
        while True:
            char = self._serial._ser.read().decode("utf-8").strip()
            response += char
            if char == ">":
                break
            if len(response) > 255:
                break

        return self._parse_state(response)


    def _write_setting(self, key, value):
        """`
`key` should be an integer.
`value` should be in its native type
"""
        while True:
            state = self.read_state()
            if state in ("Alarm", ):
                if self._unlocked is False:
                    # Grbl boots in alarm state when homing is enabled.
                    # but settings can still be set.
                    break
                raise calabo.grbl_exc.GrblAlarmError()
            if state in ("Idle", "Jog"):
                break
            time.sleep(0.1)

        value_str = setting_to_string(key, value)
        self._serial.write_line("$%d=%s" % (key, value_str))
        self._set_state("expect_ok")
        self._step()


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
            self._write_setting(key, value)

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


    def unlock(self):
        self._serial.write_line("$X")
        self._set_state("expect_ok")
        self._step()


    def move(self, x):
        cmd = "G0 X%f" % x
        self._serial.write_line(cmd)
        self._set_state("expect_ok")
        self._step()


    def mill(self, x):
        cmd = "G1 X%f" % x
        self._serial.write_line(cmd)
        self._set_state("expect_ok")
        self._step()


    def probe(self, z_to):
        cmd = "G38.2 Z%f" % z_to
        self._serial.write_line(cmd)
        self._set_state("expect_probe")
        self._step()
