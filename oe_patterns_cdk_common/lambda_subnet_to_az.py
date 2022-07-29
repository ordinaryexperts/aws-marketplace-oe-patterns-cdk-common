import boto3
import json
import cfnresponse
def handler(event, context):
    try:
        print(event)
        subnet_id = event['ResourceProperties']['subnet_id']
        client = boto3.client('ec2')
        response = client.describe_subnets(SubnetIds=[subnet_id])
        responseData = {'az': response['Subnets'][0]['AvailabilityZone']}
        print(responseData)
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
    except Exception:
        cfnresponse.send(event, context, cfnresponse.FAILED)
