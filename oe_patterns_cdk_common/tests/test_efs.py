from aws_cdk import (
  assertions,
  aws_ec2,
  Stack
)

from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.efs import Efs

def test_efs():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  app_sg = aws_ec2.CfnSecurityGroup(
    stack,
    "AppSg",
    group_description="test",
    vpc_id=vpc.id()
  )
  Efs(stack, "TestEfs", app_sg=app_sg, vpc=vpc)
  template = assertions.Template.from_stack(stack)

  template.resource_count_is("AWS::EFS::FileSystem", 1)
