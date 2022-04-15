import json
from aws_cdk import (
        core,
        assertions
    )

from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.asg import Asg

def print_resource(template, type):
  resource = template.find_resources(type)
  print('******')
  print(json.dumps(resource, indent=4, sort_keys=True))
  print('******')

def test_asg():
  stack = core.Stack()
  vpc = Vpc(stack, "TestVpc")
  asg = Asg(
    stack,
    "TestAsg",
    user_data_contents="#!/bin/bash\necho ${MYVAR}\n",
    user_data_variables={ 'MYVAR': 'Ref: MyParam' },
    vpc=vpc
  )
  template = assertions.Template.from_stack(stack)
  # print_resource(template, 'AWS::AutoScaling::AutoScalingGroup')
  template.resource_count_is("AWS::AutoScaling::AutoScalingGroup", 1)
