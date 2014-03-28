#!/usr/bin/env python

"""
Grab IP addresses from Redis and lookup Geo info.
"""

import argparse
import signal
import sys

import maxminddb
from redis import StrictRedis

from smithers import conf


parser = argparse.ArgumentParser(description='Lisa does smart things with IPs.')
parser.add_argument('--file', default='/usr/local/share/GeoIP/GeoIP2-City.mmdb',
                    help='path to mmdb file')
parser.add_argument('-v', '--verbose', action='store_true')


args = parser.parse_args()
redis = StrictRedis()

try:
    geo = maxminddb.Reader(args.file)
except IOError:
    print ('ERROR: Can\'t find MaxMind Database file (%s). '
           'Try setting the --file flag.' % args.file)
    sys.exit(1)


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
