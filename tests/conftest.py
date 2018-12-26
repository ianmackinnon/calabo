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
        with MockGrbl({
                setting_index("homing-cycle-enable"): 1
        }) as mock_grbl:
            thread = threading.Thread(target=mock_grbl.run)
            thread.daemon = True
            thread.start()
            device = mock_grbl.get_device()
            yield device



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
