# splunk_weather-gov_stations
Lambda function to retrieve weather stations from a specified state, which passes the results to SQS to be processed by another Lambda function to get weather conditions.

INPUT
```
EventBridge
event = { 
    "state": "IL"
}
```
OUTPUT
```
SQS
body = { 
    "station": "https://api.weather.gov/stations/FARI2", 
    "forwarders": [
        "arn:aws:lambda:us-east-2:711313490570:function:splunk_weather-gov_stations"
    ]
}
```
Environment Variables
```
AWS_LAMBDA_EXEC_WRAPPER = /opt/otel-instrument
OTEL_RESOURCE_ATTRIBUTES = deployment.environment=service-intelligence
OTEL_SERVICE_NAME = splunk_weather-gov_stations
SPLUNK_ACCESS_TOKEN = <TOKEN>
SPLUNK_REALM = us0
SQS_REGION = us-east-2
SQS_URL = https://sqs.us-east-2.amazonaws.com/711313490570/weather-gov_stations-TO-observations
WEATHER_URL = https://api.weather.gov/stations?state=
```

# splunk_weather-gov_observations
Lambda function that gets a weather station via SQS and retrieves weather conditions. Successful results get passed to SQS to be processed and sent to Splunk via HTTP Event Collector.

INPUT
```
SQS
body = { 
    "station": "https://api.weather.gov/stations/FARI2", 
    "forwarders": [
        "arn:aws:lambda:us-east-2:711313490570:function:splunk_weather-gov_stations"
    ]
}
```
OUTPUT
```
SQS
body = {
    "index": "general-weather",
    "time": 1717093391.145,
    "host": "api.weather.gov",
    "source": "/observations/latest",
    "sourcetype": "_json",
    "forwarders": [
        "arn:aws:lambda:us-east-2:711313490570:function:splunk_weather-gov_stations",
        "arn:aws:lambda:us-east-2:711313490570:function:splunk_weather-gov_observations"
    ]     
    "endpoint": "event",
    "event": {"@context": ["https://geojson.org/geojson-ld/geojson-context.jsonld", ... }
}
```
Environment Variables
```
AWS_LAMBDA_EXEC_WRAPPER = /opt/otel-instrument
OTEL_RESOURCE_ATTRIBUTES = deployment.environment=service-intelligence
OTEL_SERVICE_NAME = splunk_weather-gov_stations
SPLUNK_ACCESS_TOKEN = <TOKEN>
SPLUNK_REALM = us0
SQS_REGION = us-east-2
SQS_URL = https://sqs.us-east-2.amazonaws.com/711313490570/http-inputs-illinois
SPLUNK_ENDPOINT = event
SPLUNK_INDEX = general-weather
SPLUNK_SOURCETYPE = _json
```
# splunk_http-inputs-illinois
AWS Lambda that reads an AWS SQS to send a properly formatted payload to Splunk's HTTP Event Collector endpoint. 

INPUT
```
SQS
body = { 
    "index": "jeking-test",             # REQUIRED
    "time": 1716921324,
    "host": "authman.illinois.edu",
    "source": "\members",
    "sourcetype": "_json",
    "endpoint": "event",                # REQUIRED
    "forwarders: [
        "arn:...:lambda.A", 
        "arn:...:lambda.B"
    ],
    "event": "Hello World!"             # REQUIRED
}

body_list = [{body1}, {body2}, ... , {bodyN}]
```
OUTPUT
```
Splunk HTTP Event Collector
payload = {
    "index": "jeking-test",
    "time": 1716921324,
    "host": "authman.illinois.edu",
    "source": "\members",
    "sourcetype": "_json",
    "fields": {
        "forwarder": [
            "arn:...:lambda.A", 
            "arn:...:lambda.B",
            "arn:...:splunk_http-inputs-illinois"
        ]
    },
    "event": "Hello World!"
}

payload_list = {payload1}{payload2}...{payloadN}
```
Environment Variables
```
AWS_LAMBDA_EXEC_WRAPPER = /opt/otel-instrument
OTEL_RESOURCE_ATTRIBUTES = deployment.environment=service-intelligence
OTEL_SERVICE_NAME = splunk_weather-gov_stations
SPLUNK_ACCESS_TOKEN = <TOKEN>
SPLUNK_REALM = us0
SPLUNK_TOKEN = <HTTP EVENT COLLECTOR TOKEN>
SPLUNK_URL = https://http-inputs-illinois.splunkcloud.com/services/collector/
```
