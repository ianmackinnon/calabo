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



class GrblError(Exception):
    def __repr__(self):
        return "Grbl Error %d: %s" % (self.code, self.text)



class GrblAlarmError(GrblError):
    pass



exc = {
    9: {
        "name": "AlarmJogLock",
        "text": "G-code locked out during alarm or jog state",
    },
    10: {
        "name": "SoftLimits",
        "text": "Soft limits cannot be enabled without homing also enabled.",
    },
    22: {
        "name": "FeedRate",
        "text": "Feed rate has not yet been set or is undefined.",
    },
}



for k, v in exc.items():
    name = "Grbl%sError" % v["name"]
    v["code"] = k
    attr = v
    v["class"] = type(name, (GrblError, ), attr)
    globals()[name] = v["class"]
