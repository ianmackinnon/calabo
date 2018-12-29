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

"""
Calabó

Command-line CNC router control software.
"""

import io
import sys
import time
import json
import logging
import threading
import traceback

from flask import Flask, abort, request

from .grbl import Grbl
from .grbl_settings import SETTINGS



LOG = logging.getLogger("calabo")



app = Flask("calabo-flask")



def app_calabo():  # pragma: no cover
    if not getattr(app, "calabo", None):
        abort(500)
    return app.calabo



@app.route("/settings", methods=["GET"])
def settings_get():
    calabo = app_calabo()
    by_name = (request.args.get("by-name") == "true")
    from_device = (request.args.get("from-device") == "true")
    data = calabo.settings(by_name=by_name, from_device=from_device)
    return json.dumps(data)



@app.route('/settings', methods=["POST"])
def settings_post():
    calabo = app_calabo()
    calabo.settings(request.json)
    return ""



@app.route('/quit', methods=["POST"])
def quit():
    calabo = app_calabo()
    calabo._quit_requested = True
    shutdown = request.environ.get('werkzeug.server.shutdown')
    shutdown()
    return ""



class CalaboServer():
    def __init__(self, device):
        self._grbl = Grbl(device)
        self._thread_flask = None
        self._quit_requested = None

        app.config.update({
            "ENV": "development",
            "DEBUG": False,
        })

        app.calabo = self


    def __enter__(self):
        self._grbl.__enter__()
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        self._grbl.__exit__(exception_type, exception_value, traceback)


    def settings(self, key=None, value=None, by_name=None, from_device=None):
        if key is None:
            if from_device:
                self._grbl._read_settings()
            settings = self._grbl._settings
            if by_name:
                settings = {SETTINGS[k]["name"]: v for k, v in settings.items()}

            return settings

        if isinstance(key, dict):
            for key, value in key.items():
                self._grbl.setting(key, value)
            return None

        if value is None:
            return self._grbl._settings[key]

        self._grbl.setting(key, value)
        return None


    def run(self):
        try:
            logging.getLogger("werkzeug").setLevel(logging.WARNING)
            self._thread_flask = threading.Thread(target=app.run)
            self._thread_flask.start()

            while True:
                if self._quit_requested:
                    break
                time.sleep(0.5)
        except Exception as e:  # pragma: no cover
            LOG.error("Unhandled exception in `CalaboServer.run`. Exiting.")
            stream = io.StringIO()
            traceback.print_exc(file=stream)
            LOG.error("\n" + stream.getvalue())
            LOG.error(e)
            raise
