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

import sys
import time
import logging
import threading

import pytest

# Calabo imports
sys.path.append("../")

from mock_grbl import MockGrbl
from calabo.calabo import CalaboServer
from calabo.grbl import Grbl
from calabo.grbl_settings import setting_index



LOG = logging.getLogger("conftest")



def pytest_addoption(parser):
    parser.addoption("--device", action="store", default="/dev/ttyACM0")
    parser.addoption("--profile", action="store_true")



def _device_mock():
    with MockGrbl({
            setting_index("homing-cycle-enable"): 1
    }) as mock_grbl:
        thread = threading.Thread(target=mock_grbl.run)
        thread.daemon = True
        thread.start()
        yield {
            "address": mock_grbl._socat_stream._dev_remote,
            "reset": mock_grbl.reset,
        }



@pytest.fixture
def device_mock():
    yield from _device_mock()



@pytest.fixture
def device(request):
    """\
A Grbl device address.

If `request.param` is not `hardware` then a mock Grbl device will be
instantiated and run in a background thread before yielding the address.
"""

    if request.param == "hardware":
        device = pytest.config.option.device
        yield device
    else:
        yield from _device_mock()



@pytest.fixture
def grbl_mock(device_mock):
    with Grbl(device_mock) as grbl:
        yield grbl



@pytest.fixture
def grbl(device):
    with Grbl(device) as grbl:
        yield grbl



@pytest.fixture
def calabo_server(device):
    with CalaboServer(device) as calabo_server:
        thread = threading.Thread(target=calabo_server.run)
        thread.daemon = True
        thread.start()

        # Allow HTTP server to start
        time.sleep(0.1)

        yield calabo_server



def pytest_generate_tests(metafunc):
    if "device" in metafunc.fixturenames:
        metafunc.parametrize("device", ["hardware", "mock"], indirect=True)



def pytest_runtest_logreport(report):
    if report.when == "call" and pytest.config.option.profile:
        LOG.info("%0.3f", report.duration)
