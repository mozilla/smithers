#!/usr/bin/env python

"""
Grab IP addresses from Redis and lookup Geo info.
"""

import argparse
import sys

import maxminddb
from redis import StrictRedis
from statsd import StatsClient

from smithers import conf


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


counter = 0

while True:
    ip_info = redis.brpop(conf.REDIS_BUCKETS['IPLOGS'])
    rtype, rtime, ip = ip_info[1].split(',')
    record = geo.get(ip)
    if record:
        redis.incr(conf.REDIS_BUCKETS['DOWNLOAD_TOTAL'])
        country = record.get('country', record.get('registered_country'))
        if country:
            redis.hincrby(conf.REDIS_BUCKETS['DOWNLOAD_TOTAL_COUNTRY'],
                      country['iso_code'], 1)

    if args.verbose:
        sys.stdout.write('.')
        sys.stdout.flush()

    counter += 1
    if counter >= 100:
        counter = 0
        statsd.gauge('queue.geoip', redis.llen(conf.REDIS_BUCKETS['IPLOGS']))
