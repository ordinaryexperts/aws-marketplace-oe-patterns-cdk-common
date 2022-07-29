import boto3
import json
import cfnresponse
def handler(event, context):
    print(event)
    responseData = {}
    responseData['Data'] = 'test'
    cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
