#!/bin/sh


hostname=$(hostname)
uptime=$(/usr/bin/uptime)
timestamp=$(date +"%Y/%m/%d %H:%M:%S")
ipaddress=$(ifconfig wlan0|grep "inet addr"| cut -d ':' -f 2 | cut -d ' ' -f 1)
version=$(uname -r)
token=$(cat /sbin/.ha_token)
color=$(/sbin/color status)
irled=$(/sbin/irled status)

payload="{ \"data\": { \"collection_timestamp\": \"${timestamp}\", \"hostname\": \"${hostname}\", \"timestamp\": \"${timestamp}\",\"version\": \"${version}\", \"uptime\": \"${uptime}\", \"ip\": \"${ipaddress}\",\"color\": \"${color}\", \"irled\": \"${irled}\" }}"

set -x
curl -k -X POST -H "Content-Type: application/json"  -H "Authorization: Bearer ${token}" https://192.168.50.14:8123/api/services/pyscript/thingino_info --data "${payload}"
set +x
