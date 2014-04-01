"""
Utilities common to all of Smithers' little minions.
"""

import math
import time

import pytz
from dateutil.parser import parse as parse_timestamp

from smithers import conf


# Server data currently in US/Pacific
TZ = pytz.timezone(getattr(conf, 'DATA_TIMEZONE', 'US/Pacific'))


def get_datetime_utc(timestamp):
    """Convert a timestamp string to a datetime object in UTC."""
    dt = parse_timestamp(timestamp, ignoretz=True, yearfirst=True)
    dt_local = TZ.normalize(TZ.localize(dt))
    return dt_local.astimezone(pytz.utc)


def get_epoch_minute(dt):
    """Take a datetime and return the unix time rounded down to the nearest minute."""
    unixtime = time.mktime(dt.timetuple())
    return int(math.floor(unixtime / 60) * 60)


def get_db_time_key(timestamp):
    """Convert a timestamp string to a rounded unix time."""
    return get_epoch_minute(get_datetime_utc(timestamp))


class AttrDict(dict):
    """Dict with keys accessable as attributes.

    Example:
        d = AttrDict({'dude': 'abide', 'donny': 'walrus'})
        d.dude == 'abide'  # True
        d.donny == 'walrus'  # True

    Shamelessly borrowed from http://stackoverflow.com/a/14620633
    """
    def __init__(self, iterable=None, **kwargs):
        super(AttrDict, self).__init__(iterable, **kwargs)
        self.__dict__ = self
