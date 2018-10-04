#!/bin/bash
token=`cat token.txt`
curl -H "Authorization:Bearer $token" https://api.ciscospark.com/v1/$1 $2
