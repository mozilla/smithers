# Common store for redis keys
from os import getenv


IPLOGS = getenv('REDIS_KEY_IPLOGS', 'geoip')

# integer to increment
MAP_TOTAL = 'download:total'

# hash with keys == 'lat:lon', values == count, per minute
MAP_GEO = 'download:geo:{timestamp}'

# sorted set of timestamps ready for processing
MAP_TIMESTAMPS = 'download:timestamps'
SHARE_TIMESTAMPS = 'share:timestamps'
