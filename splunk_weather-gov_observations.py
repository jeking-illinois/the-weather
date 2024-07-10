''' SPLUNK_WEATHER-GOV_OBSERVATIONS '''

import boto3
import datetime
import json
import os
import re
import requests
import time

def lambda_handler(event, context):
    start = time.perf_counter()

  # UNWRAP EVENT BODY FROM SQS
    for record in event['Records']:
        body = json.loads(record['body'])

    # INITIALIZE PARAMETERS
    source_endpoint = "/observations/latest"
    sqs_client = boto3.client("sqs",
                              region_name = os.environ['SQS_REGION'])
    body['forwarders'].append(context.invoked_function_arn)
    
    # GETS LATEST OBSERVATIONS FOR STATION 
    try:
        response = requests.get(body['station'] + source_endpoint,
                                timeout = 60)
    except requests.exceptions.RequestException as e:
        raise(e)

    # PRINTS STATUS 
    log = {
        'time': datetime.datetime.now().isoformat(),
        'description': 'api.weather.gov get latest observations',
        'station': body['station'],
        'status': response.status_code,
        'status_detail': response.reason,
        'duration': round(time.perf_counter() - start, 3)
    }
    print(json.dumps(log))

    # ENDS IF STATUS IS NOT 200
    if response.status_code != 200:
        return {
            'statusCode': response.status_code
        }

    start = time.perf_counter()
    
    # CONSTRUCT PAYLOAD WITH REQUIRED ELEMENTS FOR HTTP EVENT COLLECTOR
    payload = {
        'index': os.environ['SPLUNK_INDEX'],
        'host': (re.search("(?<=//)[^/]*", body['station'])).group(0),
        'source': source_endpoint,
        'sourcetype': os.environ['SPLUNK_SOURCETYPE'],
        'forwarders': body['forwarders'],
        'endpoint': os.environ['SPLUNK_ENDPOINT'],
        'event': response.json()
    }
    
    # SEND PAYLOAD TO SQS TO BE PROCESSED VIA splunk_http-inputs-illinois
    sqs = sqs_client.send_message(QueueUrl = os.environ['SQS_URL'],
                                  MessageBody = json.dumps(payload))

    # PRINT STATUS
    log = {
        'time': datetime.datetime.now().isoformat(),
        'description': 'sqs conditions to HEC',
        'status': sqs['ResponseMetadata']['HTTPStatusCode'],
        'retry_attempts': sqs['ResponseMetadata']['RetryAttempts'],
        'duration': round(time.perf_counter() - start, 3)
    }
    print(json.dumps(log))

    # END
    return {
        'statusCode': 200
    }
