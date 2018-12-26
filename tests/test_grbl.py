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

import pytest



LOG = logging.getLogger("test_grbl")



def test_setting_homing(grbl):
    grbl.setting("homing-cycle-enable", True)
    grbl._read_settings()
    homing_enabled = grbl.setting("homing-cycle-enable")
    assert homing_enabled == True

    grbl.setting("homing-cycle-enable", False)
    grbl._read_settings()
    homing_enabled = grbl.setting("homing-cycle-enable")
    assert homing_enabled == False



def test_error_10(grbl):
    """\
Error 10. Soft limits cannot be enabled without homing also enabled.
"""

    grbl.setting("soft-limits-enable", False)
    grbl.setting("homing-cycle-enable", False)
    with pytest.raises(ValueError):
        grbl.setting("soft-limits-enable", True)
    grbl._read_settings()
    soft_limits_enabled = grbl.setting("soft-limits-enable")
    homing_enabled = grbl.setting("homing-cycle-enable")
    assert soft_limits_enabled == False
    assert soft_limits_enabled == False

    grbl.setting("homing-cycle-enable", True)
    grbl.setting("soft-limits-enable", True)
    grbl.setting("homing-cycle-enable", False)
    grbl._read_settings()
    soft_limits_enabled = grbl.setting("soft-limits-enable")
    homing_enabled = grbl.setting("homing-cycle-enable")
    assert soft_limits_enabled == False
    assert soft_limits_enabled == False
