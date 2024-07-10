''' SPLUNK_WEATHER-GOV_STATIONS '''

import boto3
import datetime
import json
import os
import requests
import time

def lambda_handler(event, context):
  # INITIALIZE PARAMETERS
    all_stations = []
    sqs_client = boto3.client("sqs", 
                              region_name = os.environ['SQS_REGION'])
    forwarders = [context.invoked_function_arn]

    # GETS PAGE 1 OF STATIONS FOR A STATE
    try:
        response = requests.get(os.environ['WEATHER_URL'] + event['state'],
                                timeout = 60)
    except requests.exceptions.RequestException as e:
        raise(e)

    stations = json.loads(response.text)['observationStations']
    next_page = json.loads(response.text)['pagination']['next']
    count = 0

    # GETS REMAINING PAGES OF STATIONS FOR A STATE
    while len(stations) > 0:
        count += 1
        # REMOVES "Cooperative Observer Program" STATIONS
        stations = [ s for s in stations if "COOP" not in s ]
        # REMOVES "National Training Center" STATIONS
        stations = [ s for s in stations if "NTC" not in s ]
        all_stations += stations

        try:
            response = requests.get(next_page,
                                    timeout = 60)
        except requests.exceptions.RequestException as e:
            raise(e)

        stations = json.loads(response.text)['observationStations']
        next_page = json.loads(response.text)['pagination']['next']

    # PRINTS STATUS 
    log = {
        'time': datetime.datetime.now().isoformat(),
        'description': 'api.weather.gov get stations',
        'state': event['state'],
        'last_status': response.status_code,
        'status_detail': response.reason,
        'page_count': count,
        'station_count': len(all_stations),
        'duration': round(time.perf_counter() - start, 3)
    }
    print(json.dumps(log))

    start = time.perf_counter()

    # SEND ALL STATIONS TO SQS
    for station in all_stations:
        message_body = {
            'station': station,
            'forwarders': forwarders
        }

        sqs = sqs_client.send_message(QueueUrl = os.environ['SQS_URL'],
                                      MessageBody = json.dumps(message_body))

        log = {
            'time': datetime.datetime.now().isoformat(),
            'description': 'send station url to sqs to get observations',
            'sqs': os.environ['SQS_URL'],
            'station': station
        }
        print(json.dumps(log))
    
    # PRINT STATUS
    log = {
        'time': datetime.datetime.now().isoformat(),
        'description': 'sqs stations to conditions',
        'status': sqs['ResponseMetadata']['HTTPStatusCode'],
        'retry_attempts': sqs['ResponseMetadata']['RetryAttempts'],
        'duration': round(time.perf_counter() - start, 3)
    }
    print(json.dumps(log))

    # END
    return {
        'statusCode': 200
    }
