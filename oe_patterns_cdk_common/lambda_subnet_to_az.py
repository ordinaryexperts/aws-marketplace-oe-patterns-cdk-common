import boto3
import cfnresponse
def handler(event, context):
    if event['RequestType'] == 'Delete':
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        return
    try:
        print(event)
        subnet_id = event['ResourceProperties']['subnet_id']
        client = boto3.client('ec2')
        response = client.describe_subnets(SubnetIds=[subnet_id])
        responseData = {'az': response['Subnets'][0]['AvailabilityZone']}
        print(responseData)
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
    except Exception as e:
        cfnresponse.send(event, context, cfnresponse.FAILED)
        raise e
