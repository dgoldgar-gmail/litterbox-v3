#!/bin/bash

domain=${1}
token=$(cat /opt/LITTERBOX/apps/homeassistant/config/secrets.yaml |grep habitrail  |awk '{print $2}')
curl "https://www.duckdns.org/update?domains=${domain}&token=${token}&verbose=true"
