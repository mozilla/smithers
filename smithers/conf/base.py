from os import getenv


DOWNLOAD = 'd'
FACEBOOK = 'f'
TWITTER = 't'

REDIS_BUCKETS = {
    'IPLOGS': getenv('REDIS_BUCKET_IPLOGS', 'geoip'),

    # integer to increment
    'DOWNLOAD_TOTAL': 'total:downloads',
    'SHARE_TOTAL': 'total:shares',

    # hash with keys by type with integer to increment
    'DOWNLOAD_TOTAL_COUNTRY': 'total:downloads:country',
    'DOWNLOAD_TOTAL_REGION': 'total:downloads:region',
    'DOWNLOAD_TOTAL_CITY': 'total:downloads:city',
    'SHARE_TOTAL_COUNTRY': 'total:shares:country',
    'SHARE_TOTAL_REGION': 'total:shares:region',
    'SHARE_TOTAL_CITY': 'total:shares:city',

    # hash with keys by type for every minute with integer to increment
    'DOWNLOAD_TOTAL_TIME': 'total:downloads:time',
    'DOWNLOAD_TOTAL_TIME_COUNTRY': 'total:downloads:time:country',
    'DOWNLOAD_TOTAL_TIME_REGION': 'total:downloads:time:region',
    'DOWNLOAD_TOTAL_TIME_CITY': 'total:downloads:time:city',
    'SHARE_TOTAL_TIME': 'total:shares:time',
    'SHARE_TOTAL_TIME_COUNTRY': 'total:shares:time:country',
    'SHARE_TOTAL_TIME_REGION': 'total:shares:time:region',
    'SHARE_TOTAL_TIME_CITY': 'total:shares:time:city',
}
