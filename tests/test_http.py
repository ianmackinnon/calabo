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
import time
import json
import logging
import requests
from subprocess import Popen, PIPE

import pytest



LOG = logging.getLogger("test_http")

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
    url = "http://127.0.0.1:5000/settings"

    request = requests.get(url)
    assert request.status_code == 200
    settings = request.json()

    request = requests.post(url, data=json.dumps(settings_1), headers={
        "Content-type": "application/json",
    })
    assert request.status_code == 200

    request = requests.get(url, params={
        "by-name": "true",
        "from-device": "true",
    })
    assert request.status_code == 200
    settings = request.json()
    assert settings == settings_1

    request = requests.post(url, data=json.dumps(settings_2), headers={
        "Content-type": "application/json",
    })
    assert request.status_code == 200

    request = requests.get(url, params={
        "from-device": "true",
    })
    assert request.status_code == 200
    settings = request.json()
    assert settings == settings_2
