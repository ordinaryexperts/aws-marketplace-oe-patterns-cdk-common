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
  template.has_resource_properties(
    "AWS::ElasticLoadBalancingV2::TargetGroup",
    {
      "Port": 443,
      "Protocol": "HTTPS",
    },
  )
  template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 1)

def test_alb_http_port():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  asg = Asg(stack, "TestAsg", vpc=vpc)
  alb = Alb(stack, "TestAlb", asg=asg, vpc=vpc, target_group_https = False)
  template = assertions.Template.from_stack(stack)
  template.has_resource_properties(
    "AWS::ElasticLoadBalancingV2::TargetGroup",
    {
      "Port": 80,
      "Protocol": "HTTP",
    },
  )
  template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 1)
  
