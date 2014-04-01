#!/usr/bin/env python

"""
Grab IP addresses from Redis and lookup Geo info.
"""

import argparse
import signal
import sys

import maxminddb
from redis import RedisError, StrictRedis
from statsd import StatsClient

from smithers import conf
from smithers.utils import AttrDict, get_db_time_key


# has the system requested shutdown
KILLED = False
RKEYS = AttrDict(conf.REDIS_BUCKETS)

parser = argparse.ArgumentParser(description='Lisa does smart things with IPs.')
parser.add_argument('--file', default=conf.GEOIP_DB_FILE,
                    help='path to mmdb file')
parser.add_argument('-v', '--verbose', action='store_true')


args = parser.parse_args()
redis = StrictRedis()

statsd = StatsClient(host=conf.STATSD_HOST,
                     port=conf.STATSD_PORT,
                     prefix=conf.STATSD_PREFIX)

try:
    geo = maxminddb.Reader(args.file)
except IOError:
    print ('ERROR: Can\'t find MaxMind Database file (%s). '
           'Try setting the --file flag.' % args.file)
    sys.exit(1)


def handle_signals(signum, frame):
    global KILLED
    KILLED = True


signal.signal(signal.SIGHUP, handle_signals)
signal.signal(signal.SIGINT, handle_signals)
signal.signal(signal.SIGTERM, handle_signals)


def process_download(timestamp, geo_data):
    """Add download aggregate data to redis."""
    redis.incr(RKEYS.DOWNLOAD_TOTAL)
    try:
        location = geo_data['location']
        lat, lon = location['latitude'], location['longitude']
    except KeyError:
        return

    geo_key = '{lat}:{lon}'.format(lat=lat, lon=lon)
    unix_min = get_db_time_key(timestamp)
    time_key = RKEYS.DOWNLOAD_GEO.format(timestamp=unix_min)
    redis.hincrby(time_key, geo_key, 1)

    # store the timestamp used in a sorted set for use in milhouse
    redis.zadd(RKEYS.DOWNLOAD_TIMESTAMPS, unix_min, unix_min)


def process_share(timestamp, geo_data, share_type):
    """Add share aggregate data to redis."""
    redis.incr(RKEYS.SHARE_TOTAL)


def main():
    counter = 0

    while True:
        if KILLED:
            return 0
        try:
            ip_info = redis.brpop(RKEYS.IPLOGS)
        except RedisError as e:
            print 'Error with Redis: {}'.format(e)
            return 1
        rtype, rtime, ip = ip_info[1].split(',')
        record = geo.get(ip)
        if record:
            is_download = rtype == conf.DOWNLOAD
            if is_download:
                process_download(rtime, record)
            else:
                process_share(rtime, record, rtype)

        if args.verbose:
            sys.stdout.write('.')
            sys.stdout.flush()

        counter += 1
        if counter >= 1000:
            counter = 0
            statsd.gauge('queue.geoip', redis.llen(RKEYS.IPLOGS))


if __name__ == '__main__':
    sys.exit(main())
