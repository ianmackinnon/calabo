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

import os
import json
from subprocess import Popen, PIPE

import pytest



TEST_PATH = os.path.abspath(os.path.dirname(__file__))



@pytest.fixture
def settings_1():
    path = os.path.join(TEST_PATH, "settings/settings.test1.json")
    with open(path) as fp:
        yield json.load(fp)



@pytest.fixture
def settings_2():
    path = os.path.join(TEST_PATH, "settings/settings.test2.json")
    with open(path) as fp:
        yield json.load(fp)



def test_settings(calabo_server, settings_1, settings_2):

    settings_out = calabo_server.settings()
    assert len(settings_out) == len(settings_1)

    calabo_server.settings(settings_1)
    settings_out = calabo_server.settings(by_name=True, from_device=True)
    assert settings_out == settings_1

    calabo_server.settings(settings_2)
    settings_out = calabo_server.settings(from_device=True)
    # JSON keys are necessarily strings but Calabó returns integer keys.
    settings_2_int = {int(k): v for k, v in settings_2.items()}
    assert settings_out == settings_2_int
