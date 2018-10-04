#!/bin/bash
slack_token=`cat slack_token.txt`
curl "https://slack.com/api/emoji.list?token=$slack_token&pretty=1" > emoji.json
for D in `cat emoji.json | jq -r '.emoji | to_entries| .[].value'`; do wget -x $D ; done
