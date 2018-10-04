#!/bin/bash
rm webexdoor.zip
rm -rf build
mkdir build
cp lambda/*.py build
pip3 install -r lambda/requirements.txt -t build
cd build
zip -r ../webexdoor.zip .
cd ..
#aws lambda update-function-code --function-name WebexIncomingWebhook --zip-file fileb://webexdoor.zip
# Change this to your deploy bucket.
aws s3 cp webexdoor.zip s3://webex-door-code/webexdoor.zip
aws lambda update-function-code --function-name WebexIncomingWebhook --s3-bucket webex-door-code --s3-key webexdoor.zip
aws lambda update-function-code --function-name SlackVoiceWatercooler --s3-bucket webex-door-code --s3-key webexdoor.zip
aws lambda update-function-code --function-name WebexVoiceDisemVoices --s3-bucket webex-door-code --s3-key webexdoor.zip
