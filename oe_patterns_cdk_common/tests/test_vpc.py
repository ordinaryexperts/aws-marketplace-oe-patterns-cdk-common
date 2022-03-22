from aws_cdk import (
        core,
        assertions
    )

from oe_patterns_cdk_common import Vpc

def test_vpc():
  stack = core.Stack()
  vpc = Vpc(stack, "test")
  template = assertions.Template.from_stack(stack)

  template.resource_count_is("AWS::EC2::VPC", 1)
