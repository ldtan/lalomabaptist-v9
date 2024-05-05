from flask import request
from pytz.exceptions import UnknownTimeZoneError

from .core.localization import set_timezone


def set_local_timezone():
    if (tz := request.args.get('tz', None)):
        try:
            set_timezone(tz)
        except UnknownTimeZoneError:
            pass
