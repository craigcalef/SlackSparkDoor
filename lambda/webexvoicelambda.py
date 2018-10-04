import pprint, json, boto3, requests, os, logging
from collections import OrderedDict

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch

patch(('requests',))

# Get a token for us to use when making Webex requests.
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='WebexVoiceToken')
token = json.loads(secret['SecretString'])['WebexToken']
spark_url = 'https://api.ciscospark.com/v1'

# Webex 'room' we're sending messages to.
destroom = os.environ['OutputRoom']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

PERTINENT_FIELDS = OrderedDict([('Region', True),
                                ('AWSAccountId', True),
                                ('NewStateValue', True),
                                ('OldStateValue', True),
                                ('NewStateReason', False)])


def hson(d, bracket_dicts=True):
    """ Recursively format a data object for human readable presentation with Markdown"""
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


def webex_format(event):
    """ Build a WebEx ready representation of an object """
    smsg = {}
    fields = []
    # Format for a Cloudwatch Alarm
    if "NewStateValue" in event:
        if event['NewStateValue'] == "OK":
            color = "good"
            icon = chr(9989)
        if event['NewStateValue'] == "INSUFFICIENT_DATA":
            color = "warning"
            icon = chr(128310)
        if event['NewStateValue'] == "ALARM":
            color = "danger"
            icon = chr(128293)
        title = "{} {}".format(icon, event['AlarmName'])
        description = event['AlarmDescription']
        for pf in PERTINENT_FIELDS.items():
            fields.append("**{}**: {}".format(pf[0], event[pf[0]]))
        smsg['text'] = "{} {} {}".format(title, description, [" ".join(fields)])
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
        if event['Records'][0]['Sns']['Subject'] == 'RawMessage':
            message = {'text': event['Records'][0]['Sns']['Message']}
        else:
            payload = json.loads(event['Records'][0]['Sns']['Message'])

            # This hack is to skip Cloudwatch Alarms going between OK and INSUFFICIENT_DATA
            # Essentialy we don't want to worry about INSUFFICIENT_DATA, but you may want to.
            if payload['NewStateValue'] == 'OK' and payload['OldStateValue'] == "INSUFFICIENT_DATA":
                return
            if payload['NewStateValue'] == 'INSUFFICIENT_DATA' and payload['OldStateValue'] == "OK":
                return

            message = webex_format(payload)
    except (ValueError, KeyError) as e:
        message = webex_format(event)

    try:
        datatosend = data={'roomId': destroom, 'markdown': message}
        headers = {'Authorization': 'Bearer {}'.format(token)}
        logger.info("Sending")
        logger.info(datatosend)
        r = requests.post("{}/messages".format(spark_url), data=datatosend, headers=headers)
        logger.info("Message posted")
        logger.info(r.text)
    except requests.HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)

if __name__=='__main__':
    print("Please run this module in AWS Lambda")
