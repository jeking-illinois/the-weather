''' SPLUNK_HTTP-INPUTS-ILLINOIS '''

import boto3
import datetime
import json
import os
import requests
import time

def lambda_handler(event, context):
    start = time.perf_counter()

    # UNWRAP EVENT BODY FROM SQS
    for record in event['Records']:
        body = json.loads(record['body'])

    # INITIALIZE PARAMETERS
    payload = {}
    skipped = []
    try:
        url = os.environ['SPLUNK_URL'] + body['endpoint']
    except:
        raise("KeyError: metadata 'endpoint' is required")
    headers =  {
        'Authorization': 'Splunk ' + os.environ['SPLUNK_TOKEN']
    }
    body['forwarders'].append(context.invoked_function_arn)

    # CREATES FORMATTED HEC PAYLOAD
    #   ADDS EACH METADATA K/V ONE AT A TIME
    #   IF NOT PRESENT, EITHER RAISE OR SKIP
    try:
        payload['index'] = body['index']
    except KeyError:
        raise("KeyError: metadata 'index' is required")
    try:
        payload['time'] = body['time']
    except:
        skipped.append('time')
    try:
        payload['host'] = body['host']
    except:
        skipped.append('host')
    try:
        payload['source'] = body['source']
    except:
        skipped.append('source')
    try:
        payload['sourcetype'] = body['sourcetype']
    except:
        skipped.append("sourcetype")
    try:
        payload['fields'] = {
            'forwarder': body['forwarders']
        }
    except:
        skipped.append("fields")

    # ADDS EVENT TO PAYLOAD 
    #   ACCOMODATES BOTH BATCH & SINGLE EVENTS
    try:
        if isinstance(body['event'], list):
            temp = payload
            payload['event'] = body['event'][0]
            payload = json.dumps(payload)
            for event in body['event'][1:]:
                temp['event'] = event
                payload = payload + json.dumps(temp)
        else:
            payload['event'] = body['event']
            payload = json.dumps(payload)
    except KeyError:
        skipped.append("event")
    except IndexError:
        skipped.append("event_list")

    # SENDS PAYLOAD TO HEC
    try:
        response = requests.post(url,
                                 headers = headers,
                                 data = payload,
                                 timeout = 60)
    except requests.exceptions.RequestException as e:
        raise(e)

    # PRINT STATUS
    log = {
        'time': datetime.datetime.now().isoformat(),
        'status': response.status_code,
        'status_detail': response.reason,
        'text': response.text,
        'skipped_metadata': skipped,
        'duration': round(time.perf_counter() - start, 3)
    }
    print(log)

    # RETURN
    return {
        'statusCode': 200
    }
