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

import logging



LOG = logging.getLogger("calabo.grbl_settings")



DEFAULT_INT = 255
DEFAULT_FLOAT = 2147483.648

SETTINGS = {
    0: {
        "name": "step-pulse-time",
        "type": "integer",
        "unit": "milliseconds",
        "default": DEFAULT_INT,
    },
    1: {
        "name": "step-idle-delay",
        "type": "integer",
        "unit": "milliseconds",
        "default": DEFAULT_INT,
    },
    2: {
        "name": "step-pulse-invert",
        "type": "integer",
        "unit": "mask",
        "default": DEFAULT_INT,
    },
    3: {
        "name": "step-direction-invert",
        "type": "integer",
        "unit": "mask",
        "default": DEFAULT_INT,
    },
    4: {
        "name": "step-invert",
        "type": "boolean",
        "default": 1
    },
    5: {
        "name": "invert-step-enable-pin",
        "type": "boolean",
        "default": 1
    },
    6: {
        "name": "invert-limit-pins",
        "type": "boolean",
        "default": 1
    },

    10: {
        "name": "status-report-options",
        "type": "integer",
        "unit": "mask",
        "default": DEFAULT_INT,
    },
    11: {
        "name": "junction-deviation",
        "type": "float",
        "unit": "millimeters",
        "default": DEFAULT_FLOAT,
    },
    12: {
        "name": "arc-tolerance",
        "type": "float",
        "unit": "millimeters",
        "default": DEFAULT_FLOAT,
    },
    13: {
        "name": "report-in-inches",
        "type": "boolean",
        "default": 1
    },

    20: {
        "name": "soft-limits-enable",
        "type": "boolean",
        "default": 0
    },
    21: {
        "name": "hard-limits-enable",
        "type": "boolean",
        "default": 0
    },
    22: {
        "name": "homing-cycle-enable",
        "type": "boolean",
        "default": 0
    },
    23: {
        "name": "homing-direction-invert",
        "type": "integer",
        "unit": "mask",
        "default": DEFAULT_INT,
    },
    24: {
        "name": "homing-locate-feed-rate",
        "type": "float",
        "unit": "millimeters-per-minute",
        "default": DEFAULT_FLOAT,
    },
    25: {
        "name": "homing-search-seek-rate",
        "type": "float",
        "unit": "millimeters-per-minute",
        "default": DEFAULT_FLOAT,
    },
    26: {
        "name": "homing-switch-debounce-delay",
        "type": "integer",
        "unit": "milliseconds",
        "default": DEFAULT_INT,
    },
    27: {
        "name": "homing-switch-pull-off-distance",
        "type": "float",
        "unit": "millimeters",
        "default": DEFAULT_FLOAT,
    },

    30: {
        "name": "maximum-spindle-speed",
        "type": "float",
        "unit": "revolutions-per-minute",
        "default": DEFAULT_FLOAT,
    },
    31: {
        "name": "minimum-spindle-speed",
        "type": "float",
        "unit": "revolutions-per-minute",
        "default": DEFAULT_FLOAT,
    },
    32: {
        "name": "laser-mode-enable",
        "type": "boolean",
        "default": 1
    },

    100: {
        "name": "x-axis-steps-per-millimeter",
        "type": "float",
        "unit": "steps-per-millimeter",
        "default": DEFAULT_FLOAT,
    },
    101: {
        "name": "y-axis-steps-per-millimeter",
        "type": "float",
        "unit": "steps-per-millimeter",
        "default": DEFAULT_FLOAT,
    },
    102: {
        "name": "z-axis-steps-per-millimeter",
        "type": "float",
        "unit": "steps-per-millimeter",
        "default": DEFAULT_FLOAT,
    },

    110: {
        "name": "x-axis-maximum-rate",
        "type": "float",
        "unit": "millimeters-per-minute",
        "default": DEFAULT_FLOAT,
    },
    111: {
        "name": "y-axis-maximum-rate",
        "type": "float",
        "unit": "millimeters-per-minute",
        "default": DEFAULT_FLOAT,
    },
    112: {
        "name": "z-axis-maximum-rate",
        "type": "float",
        "unit": "millimeters-per-minute",
        "default": DEFAULT_FLOAT,
    },

    120: {
        "name": "x-axis-maximum-acceleration",
        "type": "float",
        "unit": "millimeters-per-second-per-second",
        "default": DEFAULT_FLOAT,
    },
    121: {
        "name": "y-axis-maximum-acceleration",
        "type": "float",
        "unit": "millimeters-per-second-per-second",
        "default": DEFAULT_FLOAT,
    },
    122: {
        "name": "z-axis-maximum-acceleration",
        "type": "float",
        "unit": "millimeters-per-second-per-second",
        "default": DEFAULT_FLOAT,
    },

    130: {
        "name": "x-axis-maximum-travel",
        "type": "float",
        "unit": "millimeters",
        "default": DEFAULT_FLOAT,
    },
    131: {
        "name": "y-axis-maximum-travel",
        "type": "float",
        "unit": "millimeters",
        "default": DEFAULT_FLOAT,
    },
    132: {
        "name": "z-axis-maximum-travel",
        "type": "float",
        "unit": "millimeters",
        "default": DEFAULT_FLOAT,
    },
}



SETTINGS_KEYS = {v["name"]: k for k, v in SETTINGS.items()}



def setting_index(name):
    return SETTINGS_KEYS[name]



def setting_from_string(key, value):
    template = SETTINGS[key]

    if template["type"] == "boolean":
        value = bool(int(value))
    elif template["type"] == "integer":
        value = int(value)
    elif template["type"] == "float":
        value = float(value)

    return value



def setting_to_string(key, value):
    template = SETTINGS[key]

    if template["type"] == "boolean":
        value = int(value)

    value = str(value)

    return value
