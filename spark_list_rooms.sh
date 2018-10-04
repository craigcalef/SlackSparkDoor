#!/bin/bash
source config.sh
curl -H "Authorization:Bearer $webex_token" https://api.ciscospark.com/v1/rooms
