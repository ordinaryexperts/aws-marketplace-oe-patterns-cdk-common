import boto3
import json
import cfnresponse
def handler(event, context):
    print(event)
    responseData = {}
    responseData['az'] = 'us-east-1a'
    cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
