#!/bin/bash
token=`cat token.txt`
curl -H "Authorization:Bearer $token" -X POST https://api.ciscospark.com/v1/messages -d "markdown=woot&roomId=Y2lzY29zcGFyazovL3VzL1JPT00vYWJhMTA0OTAtMzg0Ny0xMWU4LWJhZWItYjUzM2JjNDg3ZTU1"
