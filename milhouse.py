#!/usr/bin/env python

import argparse
import json
import logging
import signal
import sys
import time
from os import path

from redis import RedisError, StrictRedis
from statsd import StatsClient

from smithers import conf
from smithers.conf import redis_keys as rkeys


log = logging.getLogger('milhouse')

parser = argparse.ArgumentParser(description='Milhouse makes things Lisa tells him to.')
parser.add_argument('--log', default=conf.LOG_LEVEL, metavar='LOG_LEVEL',
                    help='Log level (default: %s)' % conf.LOG_LEVEL)
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()

logging.basicConfig(level=getattr(logging, args.log.upper()),
                    format='%(asctime)s: %(message)s')

redis = StrictRedis()
statsd = StatsClient(host=conf.STATSD_HOST,
                     port=conf.STATSD_PORT,
                     prefix=conf.STATSD_PREFIX)

# has the system requested shutdown
KILLED = False


def handle_signals(signum, frame):
    # NOTE: Makes this thing non-thread-safe
    # Should not be too difficult to fix if we
    # need/want threads.
    global KILLED
    KILLED = True
    log.info('Attempting to shut down')


# register signals
signal.signal(signal.SIGHUP, handle_signals)
signal.signal(signal.SIGINT, handle_signals)
signal.signal(signal.SIGTERM, handle_signals)


def get_timestamps_to_process():
    """Return the timestamp(s) ready to output to JSON.

    Basic idea is:

    1. Get all but the most recent 2 timestamps from the
       redis sorted set. This should allow for them to be
       sure to be done filling.
    2. Do the same for the sorted set for share data.
    3. Cast these lists as sets.
    4. Get the intersection of these sets.
    5. Process all of the timestamps from the intersection.
    """
    map_set = set(int(ts) for ts in redis.zrange(rkeys.MAP_TIMESTAMPS, 0, -3))
    share_set = set(int(ts) for ts in redis.zrange(rkeys.SHARE_TIMESTAMPS, 0, -3))
    intersection = map_set & share_set
    return sorted(list(intersection))


def get_data_for_timestamp(timestamp):
    """
    Return aggregate map and share data dict for a timestamp.
    """
    data = {
        'map_total': redis.get(rkeys.MAP_TOTAL),
        'map_geo': [],
    }
    map_geo_key = rkeys.MAP_GEO.format(timestamp=timestamp)
    geo_data = redis.hgetall(map_geo_key)
    for latlon, count in geo_data.iteritems():
        lat, lon = latlon.split(':')
        data['map_geo'].append({
            'lat': float(lat),
            'lon': float(lon),
            'count': count,
        })

    return data


def write_json_for_timestamp(timestamp):
    """
    Write a json file for the given timestamp and data.
    """
    data = get_data_for_timestamp(timestamp)
    filename = path.join(conf.JSON_OUTPUT_DIR, 'stats_{}.json'.format(timestamp))
    with open(filename, 'w') as fh:
        json.dump(data, fh)

    log.debug('Wrote file for {}'.format(timestamp))
    log.debug(filename)


def main():
    counter = 0

    while True:
        if KILLED:
            log.info('Shutdown successful')
            return 0

        for timestamp in get_timestamps_to_process():
            write_json_for_timestamp(timestamp)
            redis.zrem(rkeys.MAP_TIMESTAMPS, timestamp)
            redis.zrem(rkeys.SHARE_TIMESTAMPS, timestamp)

        # don't run constantly since we'll only have something
        # to do every ~1 minute
        counter += 1
        time.sleep(10)


if __name__ == '__main__':
    sys.exit(main())
