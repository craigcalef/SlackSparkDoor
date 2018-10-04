import pprint, json, boto3, requests, os, time

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch

patch(('requests',))

# Get a token for us to use when making Webex requests.
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='WebexDoorToken')
token = json.loads(secret['SecretString'])['WebexToken']
spark_url = 'https://api.ciscospark.com/v1'
output_topic = os.environ.get('OUTPUT_TOPIC')

def lambda_handler(event, context):
    context.log(event)
    body = json.loads(event['body'])
    context.log(body)
    # Retrieve the message, room, and person.
    messageId, roomId, personId = body['data']['id'], body['data']['roomId'], body['data']['personId']
    headers = {'Authorization': 'Bearer {}'.format(token)}
    s = time.time()
    message_r = requests.get('{}/messages/{}'.format(spark_url, messageId), headers=headers)
    if not message_r:
        raise Exception("Couldn't get message")
    message = message_r.json()
    context.log("Getting message took {}".format(time.time() - s))
    context.log(message)
    s = time.time()
    room_r = requests.get('{}/rooms/{}'.format(spark_url, roomId), headers=headers)
    if not room_r:
        raise Exception("Couldn't get room")
    room = room_r.json()
    context.log("Getting room took {}".format(time.time() - s))
    context.log(room)
    s = time.time()
    person_r = requests.get('{}/people/{}'.format(spark_url, personId), headers=headers)
    if not person_r:
        raise Exception("Couldn't get person")
    person = person_r.json()
    context.log("Getting person took {}".format(time.time() - s))
    context.log(person)
    presentation = ":spark: <"+chr(0x200B)+"*{}*".format(person['displayName'])+chr(0x200B)+"> {}".format(message['text'])
    out = json.dumps({'message': message, 'room': room, 'person': person, 'text': presentation})
    sns_client = boto3.client('sns')
    context.log(sns_client.publish(TopicArn=output_topic, Message=out, Subject="WebexMessage"))
    return {'statusCode': 200, 'headers': {'x-f': 'yes'}, 'body': 'Skookum!', "isBase64Encoded": False}
