#!/bin/sh

# This needs to be cleaned up:
# 1) if redis is down, it should queue up the commands rather than throw them away
# 2) run from supervisord instead of cron
# 3) proper temp file names (could conflict with #1)
# 4) use proper logrotate system rather than this hack

# Replace with proper logrotate config and process the rotated file
EPOCH=`date +%s`
NEW_LOG="/var/log/glowmo/syslog/glow.${EPOCH}.log"

mv -f /var/log/glow.log $NEW_LOG
kill -HUP `cat /var/run/syslogd.pid`

cat $NEW_LOG | grep -iE 'firefox-(28|latest)' | awk '{print "lpush geoip d," $2 "," $3}' > /tmp/redis-commands.txt

cat /tmp/redis-commands.txt | redis-cli

rm /tmp/redis-commands.txt

bzip2 $NEW_LOG
