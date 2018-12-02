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
import threading

import pytest

# Calabo imports
sys.path.append("../")
from calabo.serial import Serial

# Test imports
from mock_grbl import MockGrbl



@pytest.fixture
def mock_grbl_fixture():
    with MockGrbl() as grbl:
        thread = threading.Thread(target=grbl.run)
        thread.daemon = True
        thread.start()
        yield grbl



@pytest.fixture
def mock_grbl_connection(mock_grbl_fixture):
    with Serial(mock_grbl_fixture._socat_dev_remote) as conn:
        yield conn




def test_serial(mock_grbl_connection):
    conn = mock_grbl_connection

    conn.write_line("hello")
    response = conn.read_line()

    assert response == "hello"
