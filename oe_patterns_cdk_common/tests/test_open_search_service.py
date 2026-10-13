from aws_cdk import (
  assertions,
  aws_ec2,
  aws_iam,
  Stack
)

from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.open_search_service import OpenSearchService
from oe_patterns_cdk_common.util import Util

def test_open_search_service():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  OpenSearchService(stack, "TestOpenSearchService", vpc=vpc)
  template = assertions.Template.from_stack(stack)
  # import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  template.resource_count_is("AWS::OpenSearchService::Domain", 1)

def test_open_search_service_ebs_volume_size():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  OpenSearchService(stack, "TestOpenSearchService", vpc=vpc)
  template = assertions.Template.from_stack(stack)
  # import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  domain = template.find_resources('AWS::OpenSearchService::Domain')

  assert domain['TestOpenSearchServiceDomain']['Properties']['EBSOptions']['VolumeSize'] == {
    'Ref': 'TestOpenSearchServiceEbsVolumeSize'
  }

def test_open_search_service_defaults_unchanged():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  oss = OpenSearchService(stack, "TestOpenSearchService", vpc=vpc)
  template = assertions.Template.from_stack(stack)
  props = template.find_resources('AWS::OpenSearchService::Domain')['TestOpenSearchServiceDomain']['Properties']

  assert oss.port == 80
  assert props['EngineVersion'] == 'Elasticsearch_7.10'
  assert 'DomainEndpointOptions' not in props
  statement = props['AccessPolicies']['Statement'][0]
  assert statement['Action'] == 'es:*'
  assert statement['Principal'] == {'AWS': '*'}

def test_open_search_service_managed_options():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  oss = OpenSearchService(
    stack,
    "TestOpenSearchService",
    access_principal_arns=["arn:aws:iam::123456789012:role/test-instance-role"],
    enforce_https=True,
    engine_version="OpenSearch_3.5",
    vpc=vpc
  )
  template = assertions.Template.from_stack(stack)
  props = template.find_resources('AWS::OpenSearchService::Domain')['TestOpenSearchServiceDomain']['Properties']

  assert oss.port == 443
  assert props['EngineVersion'] == 'OpenSearch_3.5'
  assert props['DomainEndpointOptions'] == {
    'EnforceHTTPS': True,
    'TLSSecurityPolicy': 'Policy-Min-TLS-1-2-PFS-2023-10'
  }
  statement = props['AccessPolicies']['Statement'][0]
  assert statement['Action'] == 'es:ESHttp*'
  assert statement['Principal'] == {'AWS': 'arn:aws:iam::123456789012:role/test-instance-role'}

def test_open_search_service_token_principal_and_sg_port():
  # The production path: a role ARN that is still a CloudFormation token at synth time,
  # and the SG ingress opened by Util.add_sg_ingress must follow the HTTPS port.
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  role = aws_iam.CfnRole(
    stack,
    "AppRole",
    assume_role_policy_document={
      "Version": "2012-10-17",
      "Statement": [{"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}]
    }
  )
  oss = OpenSearchService(
    stack,
    "TestOpenSearchService",
    access_principal_arns=[role.attr_arn],
    enforce_https=True,
    vpc=vpc
  )
  app_sg = aws_ec2.CfnSecurityGroup(stack, "AppSg", group_description="app", vpc_id=vpc.id())
  Util.add_sg_ingress(oss, app_sg)
  template = assertions.Template.from_stack(stack)

  props = template.find_resources('AWS::OpenSearchService::Domain')['TestOpenSearchServiceDomain']['Properties']
  assert props['AccessPolicies']['Statement'][0]['Principal'] == {'AWS': {'Fn::GetAtt': ['AppRole', 'Arn']}}
  ingress = template.find_resources('AWS::EC2::SecurityGroupIngress')['TestOpenSearchServiceSgIngress']['Properties']
  assert ingress['FromPort'] == 443
  assert ingress['ToPort'] == 443
