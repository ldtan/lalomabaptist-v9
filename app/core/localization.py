from datetime import datetime
from typing import (
    Optional,
    Union,
)

from flask import session
import pytz


def get_timezone() -> Optional[pytz.timezone]:
    if (tz := session.get('tz', None)):
        return pytz.timezone(tz)
    
def set_timezone(tz: Union[pytz.timezone, str]):
    if isinstance(tz, str):
        tz = pytz.timezone(tz)

    session['tz'] = tz.zone

def utcnow() -> datetime:
    return datetime.now(pytz.timezone('UTC'))

def now() -> datetime:
    tz = get_timezone() or pytz.timezone('UTC')
    return datetime.now(tz)

def to_user_timezone(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.timezone('UTC'))

    tz = get_timezone() or pytz.timezone('UTC')
    return tz.normalize(dt.astimezone(tz))

def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        tz = get_timezone() or pytz.timezone('UTC')
        dt = tz.normalize(dt)

    return dt.astimezone(pytz.timezone('UTC'))

def render_datetime(
        dt: datetime,
        format: str = '%Y-%m-%d %H:%M:%S %Z%z',
    ) -> str:
    
    return to_user_timezone(dt).strftime(format)
