from aws_cdk import (
        core,
        assertions
    )

from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.asg import Asg

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
  # import json
  # launch_config = template.find_resources('AWS::AutoScaling::LaunchConfiguration')
  # parsed = json.loads(str(launch_config).replace("\'", "\""))
  # print('******')
  # print(json.dumps(parsed, indent=4, sort_keys=True))
  # print('******')

  template.resource_count_is("AWS::AutoScaling::AutoScalingGroup", 1)
