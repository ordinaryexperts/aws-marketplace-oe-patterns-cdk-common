from aws_cdk import (
        core,
        assertions
    )

from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.asg import Asg

def test_asg():
  stack = core.Stack()
  vpc = Vpc(stack, "TestVpc")
  asg = Asg(stack, "TestAsg", vpc=vpc)
  template = assertions.Template.from_stack(stack)

  template.resource_count_is("AWS::AutoScaling::AutoScalingGroup", 1)
