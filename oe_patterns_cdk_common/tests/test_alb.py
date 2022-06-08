from aws_cdk import (
  assertions,
  aws_ec2,
  Stack
)

from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.asg import Asg
from oe_patterns_cdk_common.alb import Alb

def test_alb():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  asg = Asg(stack, "TestAsg", vpc=vpc)
  alb = Alb(stack, "TestAlb", asg=asg, vpc=vpc)
  template = assertions.Template.from_stack(stack)

  template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 1)
