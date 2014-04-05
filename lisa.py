#!/usr/bin/env python

"""
Grab IP addresses from Redis and lookup Geo info.
"""

import argparse
import logging
import signal
import sys

import maxminddb
from redis import RedisError, StrictRedis
from statsd import StatsClient

from smithers import conf
from smithers.conf import redis_keys as rkeys
from smithers.utils import get_db_time_key


log = logging.getLogger('lisa')

# has the system requested shutdown
KILLED = False

parser = argparse.ArgumentParser(description='Lisa does smart things with IPs.')
parser.add_argument('--file', default=conf.GEOIP_DB_FILE,
                    help='path to mmdb file (default: %s)' % conf.GEOIP_DB_FILE)
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

try:
    geo = maxminddb.Reader(args.file)
except IOError:
    log.error('ERROR: Can\'t find MaxMind Database file (%s). '
              'Try setting the --file flag.' % args.file)
    sys.exit(1)


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


def process_map(timestamp, geo_data):
    """Add download aggregate data to redis."""
    redis.incr(rkeys.MAP_TOTAL)
    try:
        location = {
            'lat': geo_data['location']['latitude'],
            'lon': geo_data['location']['longitude'],
        }
    except KeyError:
        # this appears to mostly happen with anonymous proxies
        log.info('Geo data contained no location.')
        log.debug(geo_data)
        return

    geo_key = '{lat}:{lon}'.format(**location)
    log.debug('Got location: ' + geo_key)
    unix_min = get_db_time_key(timestamp)
    time_key = rkeys.MAP_GEO.format(timestamp=unix_min)
    log.debug('Got timestamp: ' + unix_min)
    redis.hincrby(time_key, geo_key, 1)

    # store the timestamp used in a sorted set for use in milhouse
    redis.zadd(rkeys.MAP_TIMESTAMPS, unix_min, unix_min)
    # TODO: Remove this when we're producing share data
    # This makes milhouse go ahead and produce the data files.
    redis.zadd(rkeys.SHARE_TIMESTAMPS, unix_min, unix_min)


def process_share(timestamp, geo_data, share_type):
    """Add share aggregate data to redis."""
    log.debug('Processing as SHARE')


def main():
    counter = 0

    while True:
        if KILLED:
            log.info('Shutdown successful')
            return 0

        try:
            ip_info = redis.brpop(rkeys.IPLOGS)
        except RedisError as e:
            log.error('Error with Redis: {}'.format(e))
            return 1

        log.debug('Got log data: ' + ip_info[1])
        rtype, rtime, ip = ip_info[1].split(',')
        record = geo.get(ip)
        if record:
            # everything goes for total count and map
            process_map(rtime, record)
            # only shares get more processing
            if rtype != conf.DOWNLOAD:
                process_share(rtime, record, rtype)

        if args.verbose:
            sys.stdout.write('.')
            sys.stdout.flush()

        counter += 1
        if counter >= 1000:
            counter = 0
            statsd.gauge('queue.geoip', redis.llen(rkeys.IPLOGS))


if __name__ == '__main__':
    sys.exit(main())
