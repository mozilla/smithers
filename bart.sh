#!/bin/sh

# This needs to be cleaned up:
# 1) if redis is down, it should queue up the commands rather than throw them away
# 2) run from supervisord instead of cron
# 3) proper temp file names (could conflict with #1)
# 4) use proper logrotate system rather than this hack

# Replace with proper logrotate config and process the rotated file
cp /var/log/glow.log /tmp/glow.log
cat < /dev/null > /var/log/glow.log

cat /tmp/glow.log | grep -iE 'firefox-(28|latest)' | awk '{print "lpush geoip d," $2 "," $3}' > /tmp/redis-commands.txt

cat /tmp/redis-commands.txt | redis-cli

rm /tmp/glow.log /tmp/redis-commands.txt
