import json
from aws_cdk import (
  assertions,
  aws_iam,
  Stack
)

from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.asg import Asg

def print_resource(template, type):
  resource = template.find_resources(type)
  print('******')
  print(json.dumps(resource, indent=4, sort_keys=True))
  print('******')

def test_asg():
  stack = Stack()
  vpc = Vpc(stack, 'TestVpc')
  Asg(
    stack,
    'TestAsg',
    user_data_contents='#!/bin/bash\necho ${MYVAR}\n',
    user_data_variables={ 'MYVAR': 'Ref: MyParam' },
    vpc=vpc
  )
  template = assertions.Template.from_stack(stack)
  # print_resource(template, 'AWS::AutoScaling::AutoScalingGroup')
  template.has_resource('AWS::AutoScaling::AutoScalingGroup', {
    'UpdatePolicy': {'AutoScalingReplacingUpdate': assertions.Match.any_value()}
  })

def test_singleton_asg():
  stack = Stack()
  vpc = Vpc(stack, 'TestVpc')
  Asg(
    stack,
    'TestAsg',
    singleton=True,
    user_data_contents='#!/bin/bash\necho ${MYVAR}\n',
    user_data_variables={ 'MYVAR': 'Ref: MyParam' },
    vpc=vpc
  )
  template = assertions.Template.from_stack(stack)
  # print_resource(template, 'AWS::AutoScaling::AutoScalingGroup')
  template.has_resource('AWS::AutoScaling::AutoScalingGroup', {
    'UpdatePolicy': {'AutoScalingRollingUpdate': assertions.Match.any_value()}
  })

def test_data_asg():
  stack = Stack()
  vpc = Vpc(stack, 'TestVpc')
  Asg(
    stack,
    'TestAsg',
    data_volume_size=10,
    user_data_contents='#!/bin/bash\necho ${MYVAR}\n',
    user_data_variables={ 'MYVAR': 'Ref: MyParam' },
    vpc=vpc
  )
  template = assertions.Template.from_stack(stack)
  # print(json.dumps(template.to_json(), indent=4, sort_keys=True))
  template.resource_count_is("AWS::EC2::Volume", 1)

def test_rolling_deploy_asg():
  stack = Stack()
  vpc = Vpc(stack, 'TestVpc')
  Asg(
    stack,
    'TestAsg',
    deployment_rolling_update=True,
    user_data_contents='#!/bin/bash\necho ${MYVAR}\n',
    user_data_variables={ 'MYVAR': 'Ref: MyParam' },
    vpc=vpc
  )
  template = assertions.Template.from_stack(stack)
  # print(json.dumps(template.to_json(), indent=4, sort_keys=True))
  template.has_resource('AWS::AutoScaling::AutoScalingGroup', {
    'UpdatePolicy': {'AutoScalingRollingUpdate': assertions.Match.any_value()}
  })

def test_additional_iam_role_policies_asg():
  stack = Stack()
  vpc = Vpc(stack, 'TestVpc')
  asg_update_secret_policy = aws_iam.CfnRole.PolicyProperty(
    policy_document=aws_iam.PolicyDocument(
      statements=[
        aws_iam.PolicyStatement(
          effect=aws_iam.Effect.ALLOW,
          actions=["secretsmanager:UpdateSecret"],
          resources=["*"]
        )
      ]
    ),
    policy_name="AllowUpdateAllSecrets"
  )

  Asg(
    stack,
    'TestAsg',
    additional_iam_role_policies=[asg_update_secret_policy],
    vpc=vpc
  )
  template = assertions.Template.from_stack(stack)
  # print(json.dumps(template.to_json(), indent=4, sort_keys=True))
  role = template.find_resources('AWS::IAM::Role')

  assert role['TestAsgInstanceRole']['Properties']['Policies'][-1]['PolicyName'] == 'AllowUpdateAllSecrets'

def test_root_instance_size():
  stack = Stack()
  vpc = Vpc(stack, 'TestVpc')
  Asg(
    stack,
    'TestAsg',
    root_volume_size=100,
    vpc=vpc
  )
  template = assertions.Template.from_stack(stack)
  # print(json.dumps(template.to_json(), indent=4, sort_keys=True))
  launch_template = template.find_resources('AWS::EC2::LaunchTemplate')

  assert launch_template['TestAsgLaunchTemplate']['Properties']['LaunchTemplateData']['BlockDeviceMappings'][0]['Ebs']['VolumeSize'] == 100

def test_graviton_default():
  stack = Stack()
  vpc = Vpc(stack, 'TestVpc')
  Asg(
    stack,
    'TestAsg',
    use_graviton=True, # default
    vpc=vpc
  )
  template = assertions.Template.from_stack(stack)
  instance_type_param = template.find_parameters('TestAsgInstanceType')['TestAsgInstanceType']

  assert instance_type_param['Default'] == 't4g.small'

def test_no_graviton_default():
  stack = Stack()
  vpc = Vpc(stack, 'TestVpc')
  Asg(
    stack,
    'TestAsg',
    use_graviton=False,
    vpc=vpc
  )
  template = assertions.Template.from_stack(stack)
  instance_type_param = template.find_parameters('TestAsgInstanceType')['TestAsgInstanceType']

  assert instance_type_param['Default'] == 't2.micro'
