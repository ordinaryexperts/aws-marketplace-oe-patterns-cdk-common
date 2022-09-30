from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.asg import Asg
from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.aurora_postgresql import AuroraPostgresql

def test_aurora_postgresql():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  asg = Asg(stack, "TestAsg", vpc=vpc)
  aurora = AuroraPostgresql(stack, "TestAurora", asg=asg, vpc=vpc)
  template = assertions.Template.from_stack(stack)

  template.resource_count_is("AWS::RDS::DBCluster", 1)
