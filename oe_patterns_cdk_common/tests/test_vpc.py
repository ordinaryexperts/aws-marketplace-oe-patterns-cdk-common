from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.vpc import Vpc

def test_vpc():
  stack = Stack()
  vpc = Vpc(stack, "test")
  template = assertions.Template.from_stack(stack)

  template.resource_count_is("AWS::EC2::VPC", 1)
