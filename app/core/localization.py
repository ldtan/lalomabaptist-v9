from datetime import datetime
from typing import (
    Optional,
    Union,
)

from flask import session
import pytz


def get_timezone() -> Optional[pytz.timezone]:
    """Returns the local timezone set in user session."""

    if (tz := session.get('tz', None)):
        return pytz.timezone(tz)
    
def set_timezone(tz: Union[pytz.timezone, str]):
    """Sets the local timezone by user session."""

    if isinstance(tz, str):
        tz = pytz.timezone(tz)

    session['tz'] = tz.zone

def utcnow() -> datetime:
    """Similar to datetime.utcnow only having a timezone."""

    return datetime.now(pytz.timezone('UTC'))

def now() -> datetime:
    """Similar to datetime.now only having a timezone."""

    tz = get_timezone() or pytz.timezone('UTC')
    return datetime.now(tz)

def to_user_timezone(dt: datetime) -> datetime:
    """Converts the given datetime to the local timezone set in session."""

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.timezone('UTC'))

    tz = get_timezone() or pytz.timezone('UTC')
    return tz.normalize(dt.astimezone(tz))

def to_utc(dt: datetime) -> datetime:
    """Converts the given datetime to UTC."""

    if dt.tzinfo is None:
        tz = get_timezone() or pytz.timezone('UTC')
        dt = tz.normalize(dt)

    return dt.astimezone(pytz.timezone('UTC'))

def render_datetime(
        dt: datetime,
        format: str = '%Y-%m-%d %H:%M:%S %Z%z',
    ) -> str:
    """Uses to_user_timezone to convert the given datetime and strftime to
    format it.
    """
    
    return to_user_timezone(dt).strftime(format)
