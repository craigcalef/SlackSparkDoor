from __future__ import (unicode_literals, absolute_import, print_function, division)

import json
import logging
import os

from urllib2 import Request, urlopen, URLError, HTTPError
from collections import OrderedDict

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch

patch(('requests',))

HOOK_URL = os.environ['slackwebhook']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

PERTINENT_FIELDS = OrderedDict([('Region', True),
                                ('AWSAccountId', True),
                                ('NewStateValue', True),
                                ('OldStateValue', True),
                                ('NewStateReason', False)])


def hson(d, bracket_dicts=True):
    """ Recursively format a data object for human readable presentation """
    b = ""
    if isinstance(d, (str, unicode, int, float)):
        return str(d)
    if isinstance(d, list):
        return "; ".join([hson(i) for i in d])
    if isinstance(d, dict):
        for k in d.keys():
            b += " *{}*: {}".format(k, hson(d[k], bracket_dicts))
        if bracket_dicts:
            return "{ "+b+" }"
        else:
            return b
    return ''

def slack_entity_encode(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def slack_format(event):
    """ Build a Slack ready representation of an object """
    smsg = {}
    # Format for a Cloudwatch Alarm
    if "NewStateValue" in event:
        fields = []
        attachment = {'fields': fields}
        smsg['attachments'] = [attachment]
        if event['NewStateValue'] == "OK":
            attachment['color'] = "good"
            icon = ":white_check_mark:"
        if event['NewStateValue'] == "INSUFFICIENT_DATA":
            attachment['color'] = "warning"
            icon = ":interrobang:"
        if event['NewStateValue'] == "ALARM":
            attachment['color'] = "danger"
            icon = ":fire:"
        attachment['title'] = "{} {}".format(icon, event['AlarmName'])
        attachment['text'] = event['AlarmDescription']
        attachment['mrkdwn_in'] = ["pretext", "text", "fields"]
        for pf in PERTINENT_FIELDS.items():
            fields.append({'value': event[pf[0]],
                           'title': pf[0],
                           'short': pf[1]})
        #trigger_message = hson(ee['Trigger'], bracket_dicts=False)
        #fields.append({'value': trigger_message,
        #               'title': 'Trigger',
        #               'short': False})
    else:
        message = hson(event, bracket_dicts=False)
        smsg['text'] = message[:1024]
    return smsg


def lambda_handler(event, context):
    """ Handle an AWS Lambda event """
    logger.info("Event: " + str(event))
    logger.info("Context: " + str(context))

    try:
        # If the SNS object has a subject of 'RawMessage' we pass the message contents directly.
        if event['Records'][0]['Sns']['Subject'] == 'WebexMessage':
            payload = json.loads(event['Records'][0]['Sns']['Message'])
            slack_message = {'text': slack_entity_encode(payload['text'])}
        else:
            payload = json.loads(event['Records'][0]['Sns']['Message'])

            # This hack is to skip Cloudwatch Alarms going between OK and INSUFFICIENT_DATA
            # Essentialy we don't want to worry about INSUFFICIENT_DATA, but you may want to.
            if payload['NewStateValue'] == 'OK' and payload['OldStateValue'] == "INSUFFICIENT_DATA":
                return
            if payload['NewStateValue'] == 'INSUFFICIENT_DATA' and payload['OldStateValue'] == "OK":
                return

            slack_message = slack_format(payload)
    except (ValueError, KeyError) as e:
        slack_message = slack_format(event)

    rout = json.dumps(slack_message)
    logger.info("Sending to Slack: {}".format(rout))
    req = Request(HOOK_URL, rout)
    try:
        #requests.get(HOOK_URL, data=json.dumps(slack_message))
        response = urlopen(req)
        response.read()
        logger.info("Message posted")
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)
