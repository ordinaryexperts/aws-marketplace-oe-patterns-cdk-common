import json
from aws_cdk import (
  assertions,
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
  asg = Asg(
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
  asg = Asg(
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
  asg = Asg(
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
