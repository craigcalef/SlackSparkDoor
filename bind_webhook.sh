#!/bin/bash
source config.sh
roomId="Y2lzY29zcGFyazovL3VzL1JPT00vNzE1NmM1NTAtMzgxOS0xMWU4LWI2YjEtZjFkZTg2MWNkMGVl"
token=`cat token.txt`
curl -H "Authorization:Bearer $token" https://api.ciscospark.com/v1/webhooks --data "name=WebexDoor&targetUrl=${webExDoorUrl}&resource=messages&event=created&secret=foo&filter=roomId%3D$roomId"
