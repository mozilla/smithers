#!/usr/bin/env python

"""
Generate random IP addresses and insert them into redis.
"""

import argparse
import random
import socket
import struct
import sys
from datetime import datetime

import redis

from smithers import conf


parser = argparse.ArgumentParser(description='Bart throws random IPs at Lisa.')
parser.add_argument('--count', default=250000, type=int,
                    help='number of IPs')

args = parser.parse_args()

r = redis.StrictRedis()


def get_random_ip():
    # shamelessly stolen from the maxminddb benchmark script
    # https://github.com/maxmind/MaxMind-DB-Reader-python/blob/master/examples/benchmark.py
    return socket.inet_ntoa(struct.pack('!L', random.getrandbits(32)))


for i in xrange(args.count):
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    r.lpush(conf.REDIS_BUCKETS['IPLOGS'], 'd,%s,%s' % (timestamp, get_random_ip()))
    sys.stdout.write('.')
    sys.stdout.flush()
