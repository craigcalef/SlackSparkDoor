#!/bin/bash
source config.sh
curl $webExDoorUrl -X POST --data "test=foo" -H 'content-type: application/json'
