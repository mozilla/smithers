from os import getenv


DOWNLOAD = 'd'
FACEBOOK = 'f'
TWITTER = 't'

REDIS_BUCKETS = {
    'IPLOGS': getenv('REDIS_BUCKET_IPLOGS', 'geoip'),

    # integer to increment
    'DOWNLOAD_TOTAL': 'download:total',
    'SHARE_TOTAL': 'share:total',

    # sorted set of timestamps ready for processing
    'DOWNLOAD_TIMESTAMPS': 'download:timestamps',
    'SHARE_TIMESTAMPS': 'share:timestamps',

    # hash with keys == 'lat:lon', values == count, per minute
    'DOWNLOAD_GEO': 'download:geo:{timestamp}',
}
