from flask import (
    request,
    session,
)
from pytz import timezone
from pytz.exceptions import UnknownTimeZoneError


def set_local_timezone():
    if (tz := request.args.get('tz', None)):
        try:
            timezone(tz)
            session['tz'] = tz
        except UnknownTimeZoneError:
            pass
